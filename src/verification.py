import json
import os

from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL = "gemini-3.5-flash-lite"


VERIFY_PROMPT = """
You are the final verification layer for a version-aware developer
documentation QA system.

Verify the generated answer against ONLY the supplied evidence.

Question:
{question}

Generated answer:
{answer}

Evidence used by generation:
{source_text}

Check all of the following:

1. supported
   Are all factual claims in the answer supported by the evidence?

2. version_mixed
   Does the answer mix information from different API versions?

3. irrelevant_evidence
   Does the answer rely on evidence that does not actually support
   the claims being made?

4. citation_supported
   Do the cited/used chunks actually support the answer?

5. hallucination
   Does the answer contain information that is not present in the evidence?

6. confidence
   How confident are you that the answer is fully grounded in the evidence?
   Return a number from 0.0 to 1.0.

Return ONLY valid JSON:

{{
  "verified": true,
  "supported": true,
  "version_mixed": false,
  "irrelevant_evidence": false,
  "citation_supported": true,
  "hallucination": false,
  "confidence": 0.95,
  "reason": "short explanation"
}}

Rules:
- verified is true ONLY when all checks pass.
- Do not use outside knowledge.
- Do not judge whether the answer is generally correct outside the supplied evidence.
- Check only whether the answer is supported by the supplied evidence.
"""


def _parse_verification_response(response_text):
    raw = response_text.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "", 1)
        raw = raw.replace("```", "", 1).strip()

    return json.loads(raw)


def verify_answer(
    question,
    answer_text,
    chunks,
):
    """
    Verify a generated answer against the exact evidence
    used for generation.
    """

    if not answer_text:
        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": False,
            "citation_supported": False,
            "hallucination": True,
            "confidence": 0.0,
            "reason": "Generated answer is empty.",
        }

    if not chunks:
        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": True,
            "citation_supported": False,
            "hallucination": True,
            "confidence": 0.0,
            "reason": "No evidence was supplied for verification.",
        }

    source_text = "\n\n".join(
        (
            f"Chunk ID: {chunk.get('chunk_id', '')}\n"
            f"Version: "
            f"{chunk.get('version') or chunk.get('release_date', '')}\n"
            f"Text: {chunk.get('text', '')}"
        )
        for chunk in chunks
    )

    prompt = VERIFY_PROMPT.format(
        question=question,
        answer=answer_text,
        source_text=source_text,
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )

        result = _parse_verification_response(
            response.text
        )

    except (
        json.JSONDecodeError,
        AttributeError,
        TypeError,
        ValueError,
    ) as exc:

        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": False,
            "citation_supported": False,
            "hallucination": True,
            "confidence": 0.0,
            "reason": (
                f"Verification response could not be parsed: {exc}"
            ),
        }

    confidence = result.get(
        "confidence",
        0.0,
    )

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(
        0.0,
        min(1.0, confidence),
    )

    supported = bool(
        result.get("supported", False)
    )

    version_mixed = bool(
        result.get("version_mixed", False)
    )

    irrelevant_evidence = bool(
        result.get("irrelevant_evidence", False)
    )

    citation_supported = bool(
        result.get("citation_supported", False)
    )

    hallucination = bool(
        result.get("hallucination", False)
    )

    verified = (
        supported
        and not version_mixed
        and not irrelevant_evidence
        and citation_supported
        and not hallucination
    )

    return {
        "verified": verified,
        "supported": supported,
        "version_mixed": version_mixed,
        "irrelevant_evidence": irrelevant_evidence,
        "citation_supported": citation_supported,
        "hallucination": hallucination,
        "confidence": confidence,
        "reason": str(
            result.get("reason", "")
        ).strip(),
    }


def generate_verified_answer(
    query,
    graded_result,
    generation_result,
):
    """
    Final Generation → Verification step.

    Grading provides:
        - final/re-written query
        - graded chunks

    Generation provides:
        - generated answer
        - used chunk IDs
        - citations

    Verification validates the generated answer against
    only the chunks actually used by Generation.
    """

    if graded_result.get("status") != "found":
        return {
            "status": "not_found",
            "answer": None,
            "citations": [],
            "confidence": 0.0,
        }

    if generation_result.get("status") != "found":
        return {
            "status": "not_found",
            "answer": None,
            "citations": [],
            "confidence": 0.0,
        }

    graded_chunks = graded_result.get(
        "chunks",
        [],
    )

    used_chunk_ids = set(
        generation_result.get(
            "used_chunk_ids",
            [],
        )
    )

    # Generation must identify at least one supporting chunk.
    if not used_chunk_ids:
        return {
            "status": "hallucination_flagged",
            "answer": None,
            "citations": [],
            "used_chunk_ids": [],
            "confidence": 0.0,
            "verification": {
                "verified": False,
                "reason": (
                    "Generation returned no supporting chunk IDs."
                ),
            },
        }

    # Resolve Generation's persistent IDs back to the graded chunks.
    used_chunks = [
        chunk
        for chunk in graded_chunks
        if chunk.get("chunk_id") in used_chunk_ids
    ]

    # Every used ID must exist in the graded evidence.
    if len(used_chunks) != len(used_chunk_ids):
        return {
            "status": "hallucination_flagged",
            "answer": None,
            "citations": [],
            "used_chunk_ids": list(
                used_chunk_ids
            ),
            "confidence": 0.0,
            "verification": {
                "verified": False,
                "reason": (
                    "Generation referenced a chunk ID that was "
                    "not present in graded evidence."
                ),
            },
        }

    verdict = verify_answer(
        question=query,
        answer_text=generation_result["answer"],
        chunks=used_chunks,
    )

    if not verdict["verified"]:
        return {
            "status": "hallucination_flagged",
            "answer": None,
            "citations": [],
            "used_chunk_ids": generation_result.get(
                "used_chunk_ids",
                [],
            ),
            "confidence": verdict["confidence"],
            "verification": verdict,
        }

    return {
        "status": "ok",
        "answer": generation_result["answer"],
        "citations": generation_result.get(
            "citations",
            [],
        ),
        "used_chunk_ids": generation_result.get(
            "used_chunk_ids",
            [],
        ),
        "confidence": verdict["confidence"],
        "verification": verdict,
    }


# ---------------------------------------------------------------------------
# TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("\n" + "=" * 80)
    print("GENERATION → VERIFICATION TEST")
    print("=" * 80)

    # ------------------------------------------------------------------
    # Shared dummy graded evidence.
    # ------------------------------------------------------------------

    chunks = [
        {
            "chunk_id": "abc123",
            "doc_type": "reference",
            "endpoint": "/v1/search",
            "version": "2025-09-03",
            "text": (
                "POST /v1/search is used to search Notion content. "
                "The endpoint accepts a JSON request body containing "
                "the search parameters."
            ),
        },
        {
            "chunk_id": "def456",
            "doc_type": "reference",
            "endpoint": "/v1/pages/{page_id}",
            "version": "2025-09-03",
            "text": (
                "GET /v1/pages/{page_id} retrieves a page by page ID."
            ),
        },
    ]

    graded_result = {
        "status": "found",
        "search_query": (
            "How do I search Notion content in version 2025-09-03?"
        ),
        "chunks": chunks,
    }

    # ------------------------------------------------------------------
    # Five Generation edge cases.
    # ------------------------------------------------------------------

    test_cases = [
        {
            "name": "Valid grounded answer",
            "generation": {
                "status": "found",
                "answer": (
                    "Use POST /v1/search to search Notion content."
                ),
                "used_chunk_ids": ["abc123"],
                "citations": [
                    "[Source: reference | /v1/search | version 2025-09-03]"
                ],
            },
            "expected": "ok",
        },
        {
            "name": "Hallucinated endpoint",
            "generation": {
                "status": "found",
                "answer": (
                    "Use POST /v1/query to search Notion content."
                ),
                "used_chunk_ids": ["abc123"],
                "citations": [
                    "[Source: reference | /v1/search | version 2025-09-03]"
                ],
            },
            "expected": "hallucination_flagged",
        },
        {
            "name": "Version-mixed answer",
            "generation": {
                "status": "found",
                "answer": (
                    "Use POST /v1/search, which is supported in "
                    "the 2025-09-03 API version."
                ),
                "used_chunk_ids": ["abc123", "def456"],
                "citations": [
                    "[Source: reference | /v1/search | version 2025-09-03]",
                    "[Source: reference | /v1/pages/{page_id} | version 2025-09-03]",
                ],
            },
            "expected": "ok",
        },
        {
            "name": "Unknown chunk ID",
            "generation": {
                "status": "found",
                "answer": (
                    "Use POST /v1/search to search Notion content."
                ),
                "used_chunk_ids": ["does-not-exist"],
                "citations": [],
            },
            "expected": "hallucination_flagged",
        },
        {
            "name": "Generation returned no supporting IDs",
            "generation": {
                "status": "found",
                "answer": (
                    "Use POST /v1/search to search Notion content."
                ),
                "used_chunk_ids": [],
                "citations": [],
            },
            "expected": "hallucination_flagged",
        },
    ]

    passed = 0
    failed = 0

    for index, case in enumerate(
        test_cases,
        start=1,
    ):

        print("\n" + "-" * 80)
        print(
            f"CASE {index}/{len(test_cases)}: "
            f"{case['name']}"
        )
        print("-" * 80)

        result = generate_verified_answer(
            query=graded_result["search_query"],
            graded_result=graded_result,
            generation_result=case["generation"],
        )

        print(
            f"Status:     {result['status']}"
        )

        print(
            f"Confidence: {result['confidence']}"
        )

        if result.get("verification"):
            print(
                f"Reason:     "
                f"{result['verification'].get('reason', '')}"
            )

        if result["status"] == "ok":
            print(
                f"Answer:     {result['answer']}"
            )

        if result["status"] == case["expected"]:
            print("PASS")
            passed += 1
        else:
            print(
                f"FAIL: expected {case['expected']}"
            )
            failed += 1

    # ------------------------------------------------------------------
    # Final summary.
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("VERIFICATION TEST COMPLETE")
    print("=" * 80)

    print(f"Total:  {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed:
        raise AssertionError(
            f"{failed} verification test(s) failed."
        )

    print("\nALL VERIFICATION TESTS PASSED.")