import os
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL = "gemini-3.5-flash-lite"

CITATION_TEMPLATE = (
    "[Source: {doc_type} | {identifier} | version {version}]"
)

GEN_PROMPT = """Answer the developer's question using ONLY the
provided evidence.

Do not use outside knowledge.

If the evidence is insufficient, do not invent an answer.

Question:
"{question}"

Evidence:
{chunks_text}

Return JSON only:

{{
  "answer": "direct answer grounded only in the evidence",
  "used_chunk_ids": [0, 1]
}}

used_chunk_ids must contain ONLY the IDs of evidence chunks
that actually support the answer.
"""


def format_chunk_for_prompt(chunk_id, chunk):
    metadata = {
        key: value
        for key, value in chunk.items()
        if key != "text"
    }

    return (
        f"---\n"
        f"Chunk ID: {chunk_id}\n"
        f"Metadata: {metadata}\n"
        f"Text: {chunk['text']}\n"
        f"---"
    )


def build_citation(chunk):
    doc_type = chunk.get(
        "doc_type",
        "unknown",
    )

    version = (
        chunk.get("version")
        or chunk.get("release_date")
        or "unknown"
    )

    identifier = (
        chunk.get("endpoint")
        or chunk.get("section")
        or chunk.get("summary", "")[:50]
    )

    return CITATION_TEMPLATE.format(
        doc_type=doc_type,
        identifier=identifier,
        version=version,
    )


def generate_answer(question, graded_evidence):
    """
    Generate an answer only from evidence accepted by grading.
    """

    if not graded_evidence.get(
        "evidence_sufficient",
        False,
    ):
        return {
            "status": "not_found",
            "answer": (
                "The available documentation does not "
                "provide enough evidence to answer this question."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    chunks = graded_evidence.get(
        "chunks",
        [],
    )

    if not chunks:
        return {
            "status": "not_found",
            "answer": (
                "The available documentation does not "
                "provide enough evidence to answer this question."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    chunks_text = "\n".join(
        format_chunk_for_prompt(
            chunk_id=index,
            chunk=chunk,
        )
        for index, chunk in enumerate(chunks)
    )

    prompt = GEN_PROMPT.format(
        question=question,
        chunks_text=chunks_text,
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )

        result = json.loads(response.text)

    except (
        json.JSONDecodeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:
        return {
            "status": "generation_error",
            "answer": "",
            "used_chunk_ids": [],
            "citations": [],
            "error": str(exc),
        }

    answer = str(
        result.get(
            "answer",
            "",
        )
    ).strip()

    raw_ids = result.get(
        "used_chunk_ids",
        [],
    )

    if not isinstance(
        raw_ids,
        list,
    ):
        raw_ids = []

    valid_ids = []

    for chunk_id in raw_ids:
        if (
            isinstance(chunk_id, int)
            and 0 <= chunk_id < len(chunks)
            and chunk_id not in valid_ids
        ):
            valid_ids.append(chunk_id)

    citations = [
        build_citation(chunks[chunk_id])
        for chunk_id in valid_ids
    ]

    return {
        "status": "found",
        "answer": answer,
        "used_chunk_ids": valid_ids,
        "citations": citations,
    }


if __name__ == "__main__":

    from src.grading import retrieve_and_grade
    from src.retrieval_pipeline import hybrid_retrieve

    from src.chunking.migration_chunker import (
        chunk_migration_file,
    )
    from src.chunking.changelog_chunker import (
        chunk_changelog,
    )
    from src.chunking.reference_chunker import (
        chunk_reference_file,
    )
    from src.data_sources import DATA_SOURCES

    from rank_bm25 import BM25Okapi
    from tests.chroma_cache import get_chroma_collection

    print("\n" + "=" * 80)
    print("GRADING → GENERATION PIPELINE TEST")
    print("=" * 80)

    # ------------------------------------------------------------------
    # 1. LOAD + CHUNK ONCE
    # ------------------------------------------------------------------

    print("\n=== 1. LOAD + CHUNK ===")

    chunks = []

    for source in DATA_SOURCES:

        doc_type = source["doc_type"]
        path = source["path"]

        if doc_type == "migration":
            source_chunks = chunk_migration_file(path)

        elif doc_type == "changelog":
            with open(path, encoding="utf-8") as f:
                source_chunks = chunk_changelog(
                    f.read(),
                    doc_type="changelog",
                )

        elif doc_type == "reference":
            source_chunks = chunk_reference_file(path)

        else:
            continue

        chunks.extend(source_chunks)

    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "FAIL: No chunks loaded."
        )

    print("PASS: Chunks loaded.")

    # ------------------------------------------------------------------
    # 2. CHROMA
    # ------------------------------------------------------------------

    print("\n=== 2. CHROMA ===")

    collection = get_chroma_collection(chunks)

    print(
        f"Chroma documents: {collection.count()}"
    )

    if collection.count() != len(chunks):
        raise RuntimeError(
            "FAIL: Chroma count does not match chunks."
        )

    print("PASS: Chroma ready.")

    # ------------------------------------------------------------------
    # 3. BM25
    # ------------------------------------------------------------------

    print("\n=== 3. BM25 ===")

    bm25 = BM25Okapi(
        [
            chunk["text"].lower().split()
            for chunk in chunks
        ]
    )

    print(
        f"BM25 documents: {len(bm25.doc_freqs)}"
    )

    if len(bm25.doc_freqs) != len(chunks):
        raise RuntimeError(
            "FAIL: BM25 count does not match chunks."
        )

    print("PASS: BM25 ready.")

    # ------------------------------------------------------------------
    # 4. TEST CASES
    # ------------------------------------------------------------------

    test_cases = [
        {
            "name": "Direct single-chunk answer",
            "question": (
                "What endpoint is used to search in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "single_chunk",
        },
        {
            "name": "Multi-chunk answer",
            "question": (
                "What endpoint is used to search, and what endpoint "
                "is used to retrieve a page in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "multi_chunk",
        },
        {
            "name": "Mixed relevant and irrelevant evidence",
            "question": (
                "How do I query a data source in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "filtered_evidence",
        },
        {
            "name": "Insufficient evidence",
            "question": (
                "What undocumented database query behavior is "
                "guaranteed in Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "abstain",
        },
        {
            "name": "Wrong topic with rewrite",
            "question": (
                "How do I configure webhook retry backoff in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "rewrite_abstain",
        },
    ]

    # ------------------------------------------------------------------
    # 5. RUN TESTS
    # ------------------------------------------------------------------

    from src import grading

    production_max_retries = grading.MAX_RETRIES

    # Maximum two total attempts:
    # attempt 1 + one retry.
    grading.MAX_RETRIES = 1

    passed_tests = 0
    failed_tests = 0

    try:

        for case_number, case in enumerate(
            test_cases,
            start=1,
        ):

            print("\n" + "=" * 80)
            print(
                f"CASE {case_number}/{len(test_cases)}: "
                f"{case['name']}"
            )
            print("=" * 80)

            question = case["question"]
            expected_version = case["expected_version"]
            expected_doc_type = case["expected_doc_type"]

            print(
                f"Question:          {question}"
            )
            print(
                f"Expected version:  {expected_version}"
            )
            print(
                f"Expected type:     {expected_doc_type}"
            )
            print(
                f"Expected behavior: "
                f"{case['expected_behavior']}"
            )

            attempts_seen = []

            # ----------------------------------------------------------
            # Retrieval used by grading
            # ----------------------------------------------------------

            def retrieve_for_grading(
                search_query,
                expected_version,
            ):

                return hybrid_retrieve(
                    query=search_query,
                    collection=collection,
                    bm25=bm25,
                    chunks=chunks,
                    doc_type=expected_doc_type,
                    version=expected_version,
                    top_k=5,
                )

            # ----------------------------------------------------------
            # Attempt logger
            # ----------------------------------------------------------

            def on_attempt(info):

                attempts_seen.append(info)

                print("\n" + "-" * 80)
                print(
                    f"GRADING ATTEMPT {info['attempt']}"
                )

                print(
                    f"Search query: "
                    f"{info['search_query']}"
                )

                print(
                    f"Retrieved chunks: "
                    f"{len(info['retrieved_chunks'])}"
                )

                for index, chunk in enumerate(
                    info["retrieved_chunks"],
                    start=1,
                ):

                    version = (
                        chunk.get("version")
                        or chunk.get("release_date")
                    )

                    print(
                        f"\n  Chunk {index}"
                    )

                    print(
                        f"    version:  {version}"
                    )

                    print(
                        f"    endpoint: "
                        f"{chunk.get('endpoint', '')}"
                    )

                    print(
                        f"    section:  "
                        f"{chunk.get('section', '')}"
                    )

                    print(
                        f"    text:     "
                        f"{chunk.get('text', '')[:250]}"
                    )

            # ----------------------------------------------------------
            # REAL GRADING
            # ----------------------------------------------------------

            result = retrieve_and_grade(
                question=question,
                expected_version=expected_version,
                expected_doc_type=expected_doc_type,
                retrieve_fn=retrieve_for_grading,
                on_attempt=on_attempt,
            )

            print("\n" + "-" * 80)
            print("GRADING RESULT")
            print("-" * 80)

            print(
                f"Status:              "
                f"{result.get('status')}"
            )

            print(
                f"Evidence sufficient: "
                f"{result.get('evidence_sufficient')}"
            )

            print(
                f"Attempts used:       "
                f"{result.get('attempts')}"
            )

            print(
                f"Final query:         "
                f"{result.get('search_query')}"
            )

            print(
                f"Selected chunks:     "
                f"{len(result.get('chunks', []))}"
            )

            if result.get("grading_reason"):
                print(
                    f"Reason:              "
                    f"{result['grading_reason']}"
                )

            # ----------------------------------------------------------
            # VERIFY GRADING BEHAVIOR
            # ----------------------------------------------------------

            case_passed = True
            behavior = case["expected_behavior"]

            if not attempts_seen:

                print(
                    "\nFAIL: No grading attempt occurred."
                )

                case_passed = False

            if behavior == "single_chunk":

                if len(attempts_seen) == 1:

                    print(
                        "PASS: Completed in one attempt."
                    )

                else:

                    print(
                        "FAIL: Expected one attempt."
                    )

                    case_passed = False

            elif behavior == "multi_chunk":

                selected_chunks = result.get(
                    "chunks",
                    [],
                )

                if (
                    result.get("status") == "found"
                    and len(selected_chunks) >= 2
                ):

                    print(
                        "PASS: Grading selected multiple "
                        "supporting chunks."
                    )

                else:

                    print(
                        "FAIL: Expected at least two "
                        "selected evidence chunks."
                    )

                    case_passed = False

            elif behavior == "filtered_evidence":

                if result.get("status") == "found":

                    print(
                        "PASS: Grading selected evidence "
                        "from retrieved chunks."
                    )

                else:

                    print(
                        "FAIL: Expected graded evidence."
                    )

                    case_passed = False

            elif behavior == "abstain":

                if result.get("status") == "not_found":

                    print(
                        "PASS: Grading determined evidence "
                        "was insufficient."
                    )

                else:

                    print(
                        "FAIL: Expected insufficient evidence."
                    )

                    case_passed = False

            elif behavior == "rewrite_abstain":

                if len(attempts_seen) >= 2:

                    first_query = (
                        attempts_seen[0]["search_query"]
                    )

                    second_query = (
                        attempts_seen[1]["search_query"]
                    )

                    if first_query != second_query:

                        print(
                            "PASS: Grading rewrote the query."
                        )

                    else:

                        print(
                            "FAIL: Retry query was unchanged."
                        )

                        case_passed = False

                else:

                    print(
                        "FAIL: Expected a retry."
                    )

                    case_passed = False

            # ----------------------------------------------------------
            # GENERATION
            # ----------------------------------------------------------

            print("\n" + "-" * 80)
            print("GENERATION")
            print("-" * 80)

            generation_result = generate_answer(
                question=question,
                graded_evidence=result,
            )

            print("\nGenerated answer:")
            print(
                generation_result["answer"]
            )

            print("\nUsed chunk IDs:")
            print(
                generation_result["used_chunk_ids"]
            )

            print("\nCitations:")

            for citation in generation_result[
                "citations"
            ]:
                print(citation)

            # ----------------------------------------------------------
            # VERIFY GENERATION
            # ----------------------------------------------------------

            if result.get("status") == "found":

                if generation_result["status"] != "found":

                    print(
                        "\nFAIL: Expected generated answer."
                    )

                    case_passed = False

                elif not generation_result["answer"]:

                    print(
                        "\nFAIL: Generated answer is empty."
                    )

                    case_passed = False

                else:

                    print(
                        "\nPASS: Generated answer "
                        "from graded evidence."
                    )

                used_ids = generation_result[
                    "used_chunk_ids"
                ]

                if not used_ids:

                    print(
                        "FAIL: No supporting chunks identified."
                    )

                    case_passed = False

                else:

                    print(
                        "PASS: Generation identified "
                        "supporting chunks."
                    )

                if not generation_result["citations"]:

                    print(
                        "FAIL: No citations generated."
                    )

                    case_passed = False

                else:

                    print(
                        "PASS: Citations generated."
                    )

                # ------------------------------------------------------
                # Multi-chunk generation validation
                # ------------------------------------------------------

                if behavior == "multi_chunk":

                    if len(used_ids) >= 2:

                        print(
                            "PASS: Generation used multiple "
                            "evidence chunks."
                        )

                    else:

                        print(
                            "FAIL: Expected Generation to use "
                            "at least two chunks."
                        )

                        case_passed = False

                    if len(
                        generation_result["citations"]
                    ) >= 2:

                        print(
                            "PASS: Multiple citations generated."
                        )

                    else:

                        print(
                            "FAIL: Expected multiple citations."
                        )

                        case_passed = False

            else:

                if generation_result["status"] == "not_found":

                    print(
                        "\nPASS: Generation correctly "
                        "abstained."
                    )

                else:

                    print(
                        "\nFAIL: Generation should abstain "
                        "when evidence is insufficient."
                    )

                    case_passed = False

            # ----------------------------------------------------------
            # FINAL CASE RESULT
            # ----------------------------------------------------------

            if case_passed:

                print(
                    f"\nPASS: Case {case_number} completed."
                )

                passed_tests += 1

            else:

                print(
                    f"\nFAIL: Case {case_number} failed."
                )

                failed_tests += 1

    finally:

        grading.MAX_RETRIES = production_max_retries

    # ------------------------------------------------------------------
    # FINAL SUMMARY
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("GRADING → GENERATION TEST COMPLETE")
    print("=" * 80)

    print(
        f"Total cases: {len(test_cases)}"
    )

    print(
        f"Passed:      {passed_tests}"
    )

    print(
        f"Failed:      {failed_tests}"
    )

    if failed_tests:

        raise AssertionError(
            f"{failed_tests} pipeline case(s) failed."
        )

    print(
        "\nALL GRADING → GENERATION TESTS PASSED."
    )