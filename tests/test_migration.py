from unittest.mock import patch

from src.migration_decomposition import get_hop_sequence, decompose_and_retrieve

def test_multi_hop_sequence_uses_only_known_versions():
    assert get_hop_sequence("2021-08-16","2022-06-28") == [("2021-08-16","2022-02-22"),("2022-02-22","2022-06-28")]

def test_single_hop_sequence():
    assert get_hop_sequence("2022-06-28","2025-09-03") == [("2022-06-28","2025-09-03")]

def test_invalid_migration_ranges_are_rejected():
    assert get_hop_sequence("2022-06-28","2022-06-28") is None
    assert get_hop_sequence("2025-09-03","2022-06-28") is None
    assert get_hop_sequence("bad","2022-06-28") is None

def test_all_hops_are_batched_into_one_grading_pipeline():
    calls=[]
    def retrieve(q, expected_version):
        return [{"text":expected_version,"doc_type":"migration","version":expected_version}]
    def batch(groups, retrieve_fn):
        calls.append(groups)
        return {"status":"found","groups":[{**g,"chunks":retrieve_fn(g["question"],g["expected_version"])} for g in groups]}
    with patch("src.migration_decomposition.retrieve_and_grade_batch", side_effect=batch):
        r=decompose_and_retrieve("2021-08-16","2022-06-28",retrieve)
    assert r["status"] == "found"
    assert len(calls) == 1
    assert len(calls[0]) == 2

def test_each_hop_has_explicit_from_and_to_context_in_its_question():
    captured=[]
    def retrieve(q, expected_version):
        captured.append((q, expected_version))
        return [{"text":"x","doc_type":"migration","version":expected_version}]
    def batch(groups, retrieve_fn):
        for g in groups:
            retrieve_fn(g["question"], g["expected_version"])
        return {"status":"found","groups":[{**g,"chunks":[{"text":"x","doc_type":"migration","version":g["expected_version"]}]} for g in groups]}
    with patch("src.migration_decomposition.retrieve_and_grade_batch", side_effect=batch):
        decompose_and_retrieve("2021-08-16","2022-06-28",retrieve)
    assert captured == [
        ("What changed migrating from 2021-08-16 to 2022-02-22?","2022-02-22"),
        ("What changed migrating from 2022-02-22 to 2022-06-28?","2022-06-28"),
    ]

# Regression test for the user's reported context problem. The current API has
# no session/history field, so this is expected to fail until memory is added.
def test_clarification_followup_preserves_previous_question_context():
    from main import app, _pipeline
    from fastapi.testclient import TestClient
    seen=[]
    class Graph:
        def invoke(self, state):
            seen.append(state)
            return {"status":"needs_clarification"}
    _pipeline["graph"] = Graph()
    client=TestClient(app)
    client.post("/ask", json={"question":"How do I query a database?"})
    client.post("/ask", json={"question":"2022-06-28"})
    assert "previous_question" in seen[1] or "history" in seen[1]
