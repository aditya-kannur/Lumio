
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