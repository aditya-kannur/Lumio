# ----------------------------------------------------------------------
# Manual tests
# Run:
#     python -m src.router
# ----------------------------------------------------------------------

if __name__ == "__main__":

    test_cases = [
        (
            "Reference - supported version",
            {
                "intent": "reference",
                "version": REFERENCE_AVAILABLE_VERSIONS[0],
            },
            "ready",
        ),
        (
            "Reference - missing version",
            {
                "intent": "reference",
                "version": None,
            },
            "needs_clarification",
        ),
        (
            "Reference - unknown version",
            {
                "intent": "reference",
                "version": "2030-01-01",
            },
            "not_found",
        ),
        (
            "Reference - known version but reference unavailable",
            {
                "intent": "reference",
                "version": "2021-05-13",
            },
            "not_found",
        ),
        (
            "Diagnostic - supported version",
            {
                "intent": "diagnostic",
                "version": KNOWN_VERSIONS[0],
            },
            "ready",
        ),
        (
            "Diagnostic - missing version",
            {
                "intent": "diagnostic",
                "version": None,
            },
            "needs_clarification",
        ),
        (
            "Diagnostic - unknown version",
            {
                "intent": "diagnostic",
                "version": "2030-01-01",
            },
            "not_found",
        ),
        (
            "Migration - valid versions",
            {
                "intent": "migration",
                "from_version": "2021-08-16",
                "to_version": "2022-06-28",
            },
            "ready",
        ),
        (
            "Migration - both versions missing",
            {
                "intent": "migration",
                "from_version": None,
                "to_version": None,
            },
            "needs_clarification",
        ),
        (
            "Migration - from version missing",
            {
                "intent": "migration",
                "from_version": None,
                "to_version": "2022-06-28",
            },
            "needs_clarification",
        ),
        (
            "Migration - to version missing",
            {
                "intent": "migration",
                "from_version": "2021-08-16",
                "to_version": None,
            },
            "needs_clarification",
        ),
        (
            "Migration - unknown source version",
            {
                "intent": "migration",
                "from_version": "2030-01-01",
                "to_version": "2022-06-28",
            },
            "not_found",
        ),
        (
            "Migration - unknown target version",
            {
                "intent": "migration",
                "from_version": "2021-08-16",
                "to_version": "2030-01-01",
            },
            "not_found",
        ),
        (
            "Migration - same versions",
            {
                "intent": "migration",
                "from_version": "2022-06-28",
                "to_version": "2022-06-28",
            },
            "not_found",
        ),
        (
            "Unknown intent",
            {
                "intent": "unknown",
                "version": "2022-06-28",
            },
            "not_found",
        ),
    ]

    print("\n=== ROUTER TESTS ===\n")

    passed = 0

    for name, query, expected_status in test_cases:
        result = route_query(query)
        actual_status = result.get("status")

        if actual_status == expected_status:
            print(f"PASS: {name}")
            print(f"      status: {actual_status}")
            passed += 1
        else:
            print(f"FAIL: {name}")
            print(f"      expected: {expected_status}")
            print(f"      actual:   {actual_status}")
            print(f"      result:   {result}")

        print()

    print(f"Result: {passed}/{len(test_cases)} tests passed.")

    if passed != len(test_cases):
        raise AssertionError("One or more router tests failed.")