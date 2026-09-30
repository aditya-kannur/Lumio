

if __name__ == "__main__":
    import json

    from src.query_understanding import understand_query
    from src.router import route_query

    print("\n=== 1. LOAD REAL DATA ===")

    chunks = load_all_chunks()
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError("FAIL: No chunks loaded.")

    print("PASS: Real chunks loaded.")

    # ------------------------------------------------------------------
    # 2. CHROMA
    # ------------------------------------------------------------------

    print("\n=== 2. CHROMA ===")

    collection = build_chroma_collection(chunks)

    print(f"Chroma documents: {collection.count()}")

    if collection.count() != len(chunks):
        raise RuntimeError(
            "FAIL: Chroma count does not match chunks."
        )

    print("PASS: Chroma index correct.")

    # ------------------------------------------------------------------
    # 3. BM25
    # ------------------------------------------------------------------

    print("\n=== 3. BM25 ===")

    bm25 = build_bm25_index(chunks)

    print(f"BM25 documents: {len(bm25.doc_freqs)}")

    if len(bm25.doc_freqs) != len(chunks):
        raise RuntimeError(
            "FAIL: BM25 count does not match chunks."
        )

    print("PASS: BM25 index correct.")

    # ------------------------------------------------------------------
    # 4. REAL QUERY UNDERSTANDING → ROUTER → RETRIEVAL
    # ------------------------------------------------------------------

    test_queries = [
        {
            "name": "Reference lookup - supported version",
            "question": (
                "How do I query a database in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_intent": "reference",
            "expected_status": "ready",
            "should_retrieve": True,
        },
        {
            "name": "Reference lookup - unavailable version",
            "question": (
                "How do I query a database in "
                "Notion-Version 2022-06-28?"
            ),
            "expected_intent": "reference",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Migration path",
            "question": (
                "How do I upgrade from "
                "2021-08-16 to 2022-06-28?"
            ),
            "expected_intent": "migration",
            "expected_status": "ready",
            "should_retrieve": False,
        },
        {
            "name": "Breaking changes",
            "question": (
                "What breaks if I move from "
                "2022-06-28 to 2025-09-03?"
            ),
            "expected_intent": "migration",
            "expected_status": "ready",
            "should_retrieve": False,
        },
        {
            "name": "Diagnostic - missing version",
            "question": (
                "Why did my request start failing "
                "with a missing_version error?"
            ),
            "expected_intent": "diagnostic",
            "expected_status": "needs_clarification",
            "should_retrieve": False,
        },
        {
            "name": "Not found - unsupported version",
            "question": (
                "How do I configure webhook retry backoff "
                "in Notion-Version 2021-05-13?"
            ),
            "expected_intent": "reference",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Not found - completely unknown version",
            "question": (
                "How do I query a database in "
                "Notion-Version 2030-01-01?"
            ),
            "expected_intent": "reference",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Clarification trigger",
            "question": "How do I query a database?",
            "expected_intent": "reference",
            "expected_status": "needs_clarification",
            "should_retrieve": False,
        },
        {
            "name": "Migration - unknown source",
            "question": (
                "How do I upgrade from "
                "2030-01-01 to 2025-09-03?"
            ),
            "expected_intent": "migration",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Migration - unknown target",
            "question": (
                "How do I upgrade from "
                "2022-06-28 to 2030-01-01?"
            ),
            "expected_intent": "migration",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
    ]

    print(
        "\n=== 4. QUERY UNDERSTANDING → ROUTER → RETRIEVAL ==="
    )

    total_tests = len(test_queries)
    passed_tests = 0
    failed_tests = 0

    for test in test_queries:

        print("\n" + "=" * 80)
        print(f"TEST:     {test['name']}")
        print(f"QUESTION: {test['question']}")
        print("=" * 80)

        # --------------------------------------------------------------
        # Query Understanding
        # --------------------------------------------------------------

        print("\n[1. Query Understanding]")

        understood = understand_query(test["question"])

        print(json.dumps(understood, indent=2))

        intent = understood.get("intent")
        version = understood.get("version")

        print(f"Intent:  {intent}")
        print(f"Version: {version}")

        if intent != test["expected_intent"]:
            print(
                f"FAIL: Expected intent "
                f"'{test['expected_intent']}', got '{intent}'"
            )
            failed_tests += 1
            continue

        print("PASS: Intent correct.")

        # --------------------------------------------------------------
        # Router
        # --------------------------------------------------------------

        print("\n[2. Router]")

        routing = route_query(understood)

        print(json.dumps(routing, indent=2))

        status = routing.get("status")

        print(f"Router status: {status}")

        if status != test["expected_status"]:
            print(
                f"FAIL: Expected router status "
                f"'{test['expected_status']}', got '{status}'"
            )
            failed_tests += 1
            continue

        print("PASS: Router status correct.")

        # --------------------------------------------------------------
        # Verify early-stop behavior
        # --------------------------------------------------------------

        if not test["should_retrieve"]:

            if status in {"needs_clarification", "not_found"}:
                print(
                    "\nPASS: Retrieval correctly skipped by router."
                )
            elif intent == "migration" and status == "ready":
                print(
                    "\nPASS: Migration correctly stops before "
                    "direct retrieval and will use multi-hop flow."
                )
            else:
                print(
                    "\nFAIL: Test expected retrieval to be skipped."
                )
                failed_tests += 1
                continue

            passed_tests += 1
            continue

        # --------------------------------------------------------------
        # 3. Normal retrieval
        # --------------------------------------------------------------

        if status != "ready":
            print(
                "\nFAIL: Expected ready status before retrieval."
            )
            failed_tests += 1
            continue

        doc_types = routing.get("doc_types", [])

        if not doc_types:
            print("FAIL: Router returned no doc_types.")
            failed_tests += 1
            continue

        print("\n[3. Retrieval]")
        print(f"Doc types: {doc_types}")
        print(f"Version filter: {version}")

        all_results = []

        for doc_type in doc_types:

            results = hybrid_retrieve(
                query=test["question"],
                collection=collection,
                bm25=bm25,
                chunks=chunks,
                doc_type=doc_type,
                version=version,
                top_k=5,
            )

            all_results.extend(results)

        print(f"Results returned: {len(all_results)}")

        # --------------------------------------------------------------
        # Retrieval must actually return something for this test
        # --------------------------------------------------------------

        if not all_results:
            print(
                "FAIL: Router said ready, but retrieval returned "
                "zero results."
            )
            failed_tests += 1
            continue

        print("PASS: Retrieval returned results.")

        # --------------------------------------------------------------
        # Verify document type filter
        # --------------------------------------------------------------

        wrong_types = [
            result
            for result in all_results
            if result.get("doc_type") not in doc_types
        ]

        if wrong_types:
            print(
                "FAIL: Retrieval returned an incorrect document type."
            )
            failed_tests += 1
            continue

        print("PASS: Document type filter correct.")

        # --------------------------------------------------------------
        # Verify version filter
        # --------------------------------------------------------------

        wrong_versions = []

        for result in all_results:

            actual_version = (
                result.get("version")
                or result.get("release_date")
            )

            if actual_version != version:
                wrong_versions.append(result)

        if wrong_versions:
            print(
                "FAIL: Retrieval returned an incorrect version."
            )
            failed_tests += 1
            continue

        print("PASS: Version filter correct.")

        # --------------------------------------------------------------
        # Print actual retrieved chunks
        # --------------------------------------------------------------

        for i, result in enumerate(all_results, start=1):

            actual_version = (
                result.get("version")
                or result.get("release_date")
            )

            print(f"\n--- Result {i} ---")
            print(f"doc_type: {result.get('doc_type')}")
            print(f"version:  {actual_version}")
            print(f"endpoint: {result.get('endpoint', '')}")
            print(f"section:  {result.get('section', '')}")
            print(
                f"text:     "
                f"{result.get('text', '')[:300]}"
            )

        passed_tests += 1

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETE")
    print("=" * 80)

    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {passed_tests}")
    print(f"Failed:       {failed_tests}")

    if failed_tests:
        raise AssertionError(
            f"{failed_tests} pipeline test(s) failed."
        )

    print("\nALL REAL PIPELINE TESTS PASSED.")