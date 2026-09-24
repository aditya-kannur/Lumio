from src.router import route_query
from src.messages import CLARIFICATION_QUESTION, NOT_FOUND_MESSAGE

def test_reference_routes_to_reference_with_version():
    r = route_query({"intent":"reference","version":"2022-06-28"})
    assert r == {"status":"ready","doc_types":["reference"],"version":"2022-06-28"}

def test_diagnostic_routes_to_changelog_and_reference():
    r = route_query({"intent":"diagnostic","version":"2022-06-28"})
    assert r["status"] == "ready"
    assert r["doc_types"] == ["changelog","reference"]

def test_migration_requires_both_versions():
    r = route_query({"intent":"migration","from_version":"2021-08-16","to_version":None})
    assert r == {"status":"needs_clarification","message":CLARIFICATION_QUESTION}

def test_reference_without_version_does_not_guess_latest():
    r = route_query({"intent":"reference","version":None})
    assert r["status"] == "needs_clarification"
    assert r["message"] == CLARIFICATION_QUESTION

def test_unknown_intent_is_not_found():
    r = route_query({"intent":"other","version":"2022-06-28"})
    assert r == {"status":"not_found","message":NOT_FOUND_MESSAGE}
