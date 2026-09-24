"""
Day 7: Routing logic — maps intent -> doc_type(s) + version filter,
and handles clarification / deterministic not-found cases before retrieval.
"""

from src.constants import KNOWN_VERSIONS, REFERENCE_AVAILABLE_VERSIONS
from src.messages import CLARIFICATION_QUESTION
from dotenv import load_dotenv

load_dotenv()


# Maps each intent to which doc_type(s) it should search.
# Diagnostic searches two doc types in parallel per PRD section 4.3.
INTENT_TO_DOC_TYPES = {
    "reference": ["reference"],
    "diagnostic": ["changelog", "reference"],
    "migration": ["migration"],
}


def _not_found(message: str) -> dict:
    """Build a consistent deterministic not-found response."""
    return {
        "status": "not_found",
        "message": message,
    }


def _unknown_version_message(version: str) -> str:
    """Message for a version that does not exist in the dataset."""
    return (
        f"Notion API version '{version}' is not available in the dataset. "
        f"Known versions are: {', '.join(KNOWN_VERSIONS)}."
    )


def route_query(understood_query: dict) -> dict:
    """
    Takes the dict from query_understanding.understand_query() and turns it
    into a routing decision.

    Possible statuses:
        - ready
        - needs_clarification
        - not_found

    Deterministic validation is performed here so requests that cannot
    possibly be answered from the available dataset do not reach retrieval.
    """

    intent = understood_query.get("intent")
    doc_types = INTENT_TO_DOC_TYPES.get(intent)

    # ------------------------------------------------------------------
    # 1. Unknown intent
    # ------------------------------------------------------------------

    if doc_types is None:
        return _not_found(
            "I could not determine a supported request type from your question. "
            "Supported request types are reference, diagnostic, and migration."
        )

    # ------------------------------------------------------------------
    # 2. Migration routing
    # ------------------------------------------------------------------

    if intent == "migration":
        from_version = understood_query.get("from_version")
        to_version = understood_query.get("to_version")

        # Both versions are required to construct the migration path.
        if not from_version and not to_version:
            return {
                "status": "needs_clarification",
                "message": (
                    "Which Notion API versions are you migrating from and to? "
                    "For example: 2021-08-16 to 2022-06-28."
                ),
            }

        if not from_version:
            return {
                "status": "needs_clarification",
                "message": (
                    "What Notion API version are you migrating from?"
                ),
            }

        if not to_version:
            return {
                "status": "needs_clarification",
                "message": (
                    "What Notion API version are you migrating to?"
                ),
            }

        # Source version does not exist in our dataset.
        if from_version not in KNOWN_VERSIONS:
            return _not_found(
                f"The migration source version '{from_version}' is not "
                f"available in the dataset. Known versions are: "
                f"{', '.join(KNOWN_VERSIONS)}."
            )

        # Target version does not exist in our dataset.
        if to_version not in KNOWN_VERSIONS:
            return _not_found(
                f"The migration target version '{to_version}' is not "
                f"available in the dataset. Known versions are: "
                f"{', '.join(KNOWN_VERSIONS)}."
            )

        # Same-version migration has no migration path.
        if from_version == to_version:
            return _not_found(
                f"The source and target versions are both '{from_version}'. "
                "No migration path is required because the versions are the same."
            )

        return {
            "status": "ready",
            "doc_types": doc_types,
            "from_version": from_version,
            "to_version": to_version,
        }

    # ------------------------------------------------------------------
    # 3. Reference / diagnostic routing
    # ------------------------------------------------------------------

    version = understood_query.get("version")

    # Version is required for both reference and diagnostic requests.
    if not version:
        return {
            "status": "needs_clarification",
            "message": CLARIFICATION_QUESTION,
        }

    # Version does not exist anywhere in our dataset.
    if version not in KNOWN_VERSIONS:
        return _not_found(
            _unknown_version_message(version)
        )

    # Reference documentation is only available for specific versions.
    if intent == "reference" and version not in REFERENCE_AVAILABLE_VERSIONS:
        available = ", ".join(REFERENCE_AVAILABLE_VERSIONS)

        return _not_found(
            f"Reference documentation for Notion API version '{version}' "
            f"is not available in the dataset. Reference documentation is "
            f"available for: {available}."
        )

    return {
        "status": "ready",
        "doc_types": doc_types,
        "version": version,
    }


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