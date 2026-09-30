# ---------------------------------------------------------------------------
# LOCAL GRADING TEST
# ---------------------------------------------------------------------------
#
# This test is intentionally isolated from retrieval_pipeline.py.
#
# Test flow:
#   1. Load + chunk documents once.
#   2. Build Chroma once.
#   3. Build BM25 once.
#   4. Attempt 1: hybrid RRF retrieval -> ONE group grading call.
#   5. Expect attempt 1 to be insufficient (hardcoded test expectation).
#   6. Use Gemini's rewritten query.
#   7. Attempt 2: hybrid RRF retrieval -> ONE group grading call.
#   8. Do not rerun chunking, Chroma creation, or routing.
#
# This is a terminal test only. Production retrieval_pipeline.py is not used.
# ---------------------------------------------------------------------------



if __name__ == "__main__":

    import json

    from src.retrieval_pipeline import hybrid_retrieve

    from src.chunking.migration_chunker import chunk_migration_file
    from src.chunking.changelog_chunker import chunk_changelog
    from src.chunking.reference_chunker import chunk_reference_file

    from src.data_sources import DATA_SOURCES

    print("\n" + "=" * 80)
    print("GRADING PIPELINE TEST")
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
        raise RuntimeError("FAIL: No chunks loaded.")

    print("PASS: Chunks loaded.")

    # ------------------------------------------------------------------
    # 2. CHROMA ONCE
    # ------------------------------------------------------------------

    print("\n=== 2. CHROMA ===")

    from tests.chroma_cache import get_chroma_collection

    collection = get_chroma_collection(chunks)

    print(f"Chroma documents: {collection.count()}")

    if collection.count() != len(chunks):
        raise RuntimeError(
            "FAIL: Chroma count does not match chunks."
        )

    print("PASS: Chroma ready.")

    # ------------------------------------------------------------------
    # 3. BM25 ONCE
    # ------------------------------------------------------------------

    print("\n=== 3. BM25 ===")

    from rank_bm25 import BM25Okapi

    bm25 = BM25Okapi(
        [chunk["text"].lower().split() for chunk in chunks]
    )

    print(f"BM25 documents: {len(bm25.doc_freqs)}")

    if len(bm25.doc_freqs) != len(chunks):
        raise RuntimeError(
            "FAIL: BM25 count does not match chunks."
        )

    print("PASS: BM25 ready.")

    # ------------------------------------------------------------------
    # 4. GRADING TEST CASES
    #
    # All cases reuse the SAME:
    #   - chunks
    #   - Chroma collection
    #   - BM25 index
    #
    # No routing/chunking/index rebuilding happens during retries.
    # ------------------------------------------------------------------

    test_cases = [

        {
            "name": "Mixed relevant + irrelevant evidence",
            "question": (
                "How do I query a data source in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "grade_group",
        },

        {
            "name": "Single relevant evidence",
            "question": (
                "What endpoint is used to search in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "grade_group",
        },

        {
            "name": "Potentially insufficient evidence",
            "question": (
                "What undocumented database query behavior is "
                "guaranteed in Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "rewrite",
        },

        {
            "name": "Wrong-topic retrieval / rewrite",
            "question": (
                "How do I configure webhook retry backoff in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "rewrite",
        },

        {
            "name": "Near-match endpoint",
            "question": (
                "How do I create a database and what request body "
                "does it accept in Notion-Version 2025-09-03?"
            ),
            "expected_version": "2025-09-03",
            "expected_doc_type": "reference",
            "expected_behavior": "grade_group",
        },
    ]

    # ------------------------------------------------------------------
    # 5. RUN EACH GRADING CASE
    # ------------------------------------------------------------------

    print("\n=== 4. GRADING CASES ===")
    print(f"Total grading cases: {len(test_cases)}")

    production_max_retries = MAX_RETRIES

    # Test maximum = 2 attempts.
    MAX_RETRIES = 1

    passed_tests = 0
    failed_tests = 0

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

        print(f"Question:         {question}")
        print(f"Expected version: {expected_version}")
        print(f"Expected type:    {expected_doc_type}")
        print(
            f"Expected behavior: "
            f"{case['expected_behavior']}"
        )

        # --------------------------------------------------------------
        # Retrieval function.
        #
        # IMPORTANT:
        # This reuses the SAME Chroma + BM25 objects.
        #
        # Retry only changes search_query.
        # --------------------------------------------------------------

        def retrieve_for_grading(
            search_query,
            expected_version,
        ):

            results = hybrid_retrieve(
                query=search_query,
                collection=collection,
                bm25=bm25,
                chunks=chunks,
                doc_type=expected_doc_type,
                version=expected_version,
                top_k=5,
            )

            return results

        # --------------------------------------------------------------
        # Attempt logger.
        # --------------------------------------------------------------

        attempts_seen = []

        def on_attempt(info):

            attempts_seen.append(info)

            print("\n" + "-" * 80)
            print(
                f"ATTEMPT {info['attempt']}/2"
            )
            print(
                f"Search query: {info['search_query']}"
            )
            print(
                f"RRF chunks:   "
                f"{len(info['retrieved_chunks'])}"
            )

            for index, chunk in enumerate(
                info["retrieved_chunks"],
                start=1,
            ):

                actual_version = (
                    chunk.get("version")
                    or chunk.get("release_date")
                )

                print(f"\n  Result {index}")
                print(
                    f"    doc_type: "
                    f"{chunk.get('doc_type')}"
                )
                print(
                    f"    version:  "
                    f"{actual_version}"
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
                    f"{chunk.get('text', '')[:300]}"
                )

        # --------------------------------------------------------------
        # RUN RETRIEVE → GRADE → OPTIONAL REWRITE
        # --------------------------------------------------------------

        try:

            result = retrieve_and_grade(
                question=question,
                expected_version=expected_version,
                expected_doc_type=expected_doc_type,
                retrieve_fn=retrieve_for_grading,
                on_attempt=on_attempt,
            )

        finally:

            MAX_RETRIES = production_max_retries

        # --------------------------------------------------------------
        # REPORT
        # --------------------------------------------------------------

        print("\n" + "-" * 80)
        print("CASE RESULT")
        print("-" * 80)

        print(
            f"Attempts used: "
            f"{result.get('attempts')}"
        )

        print(
            f"Final status:  "
            f"{result.get('status')}"
        )

        print(
            f"Final query:   "
            f"{result.get('search_query')}"
        )

        if result.get("grading_reason"):
            print(
                f"Reason:        "
                f"{result['grading_reason']}"
            )

        # --------------------------------------------------------------
        # VALIDATE BASIC GRADING BEHAVIOR
        # --------------------------------------------------------------

        case_passed = True

        # We must always have at least one grading attempt.
        if not attempts_seen:

            print(
                "FAIL: No grading attempt was recorded."
            )

            case_passed = False

        # --------------------------------------------------------------
        # REWRITE CASES
        # --------------------------------------------------------------

        if case["expected_behavior"] == "rewrite":

            if len(attempts_seen) < 2:

                print(
                    "FAIL: Expected a rewritten-query "
                    "retry, but only one attempt occurred."
                )

                case_passed = False

            else:

                first_query = attempts_seen[0]["search_query"]
                second_query = attempts_seen[1]["search_query"]

                if first_query == second_query:

                    print(
                        "FAIL: Attempt 2 used the same "
                        "query. Expected a rewritten query."
                    )

                    case_passed = False

                else:

                    print(
                        "PASS: Grader produced a different "
                        "query for the retry."
                    )

                    print(
                        f"  Attempt 1: {first_query}"
                    )

                    print(
                        f"  Attempt 2: {second_query}"
                    )

        # --------------------------------------------------------------
        # NORMAL GROUP-GRADING CASES
        #
        # These cases do not require a retry because the purpose is
        # to observe whether the group grader can distinguish:
        #
        #   relevant chunks
        #   irrelevant chunks
        #   sufficient evidence
        #   insufficient evidence
        #
        # --------------------------------------------------------------

        elif case["expected_behavior"] == "grade_group":

            if len(attempts_seen) >= 1:

                print(
                    "PASS: Group grading was executed."
                )

                if result.get("status") == "found":

                    selected = result.get(
                        "chunks",
                        [],
                    )

                    print(
                        f"Selected evidence: "
                        f"{len(selected)} chunk(s)"
                    )

                else:

                    print(
                        "Result remained insufficient/not found "
                        "after grading."
                    )

        # --------------------------------------------------------------
        # FINAL CASE STATUS
        # --------------------------------------------------------------

        if case_passed:

            print(
                f"\nPASS: Case {case_number} "
                f"completed successfully."
            )

            passed_tests += 1

        else:

            print(
                f"\nFAIL: Case {case_number} "
                f"failed."
            )

            failed_tests += 1

    # ------------------------------------------------------------------
    # FINAL SUMMARY
    # ------------------------------------------------------------------

    MAX_RETRIES = production_max_retries

    print("\n" + "=" * 80)
    print("GRADING PIPELINE TEST COMPLETE")
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

    print(
        "\nAll cases reused the same:"
    )

    print("  - chunk set")
    print("  - Chroma collection")
    print("  - BM25 index")

    print(
        "\nRetries changed only the retrieval query."
    )

    if failed_tests:

        raise AssertionError(
            f"{failed_tests} grading case(s) failed."
        )

    print(
        "\nALL GRADING TESTS PASSED."
    )