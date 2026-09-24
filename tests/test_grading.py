from unittest.mock import patch

from src.grading import _format_candidates, _grade_batch, _retrieve_groups, retrieve_and_grade_batch, retrieve_and_grade

def group():
    return {"question":"What changed?","expected_version":"2025-09-03","expected_doc_type":"migration"}

def test_grader_formats_all_chunks_into_one_candidate_batch():
    g = {**group(), "chunks":[{"text":"a","version":"2025-09-03","doc_type":"migration"},{"text":"b","version":"2025-09-03","doc_type":"migration"}]}
    c = _format_candidates([g])
    assert [x["candidate_id"] for x in c] == [0,1]
    assert len(c) == 2

def test_grader_makes_one_model_call_for_a_batch():
    class R: text = '{"results":[{"candidate_id":0,"relevant":true,"version_correct":true,"doc_type_correct":true}],"rewritten_questions":[]}'
    with patch("src.grading.client.models.generate_content", return_value=R()) as call:
        grades, rewrites = _grade_batch([{**group(),"chunks":[{"text":"valid","version":"2025-09-03","doc_type":"migration"}]}])
    assert grades == {0: True}
    assert rewrites == {}
    assert call.call_count == 1

def test_grader_requires_all_three_dimensions():
    class R: text = '{"results":[{"candidate_id":0,"relevant":true,"version_correct":false,"doc_type_correct":true}],"rewritten_questions":[]}'
    with patch("src.grading.client.models.generate_content", return_value=R()):
        grades, _ = _grade_batch([{**group(),"chunks":[{"text":"wrong","version":"2022-06-28","doc_type":"migration"}]}])
    assert grades == {0: False}

def test_retrieve_groups_caps_each_group_at_configured_limit():
    groups = [group()]
    result = _retrieve_groups(groups, lambda q, expected_version=None: list(range(20)))
    assert len(result[0]["chunks"]) == 5

def test_success_stops_after_first_grading_attempt():
    with patch("src.grading._grade_batch", return_value=({0:True}, {})) as grade:
        r = retrieve_and_grade_batch([group()], lambda q, expected_version=None: [{"text":"ok","version":expected_version,"doc_type":"migration"}])
    assert r["status"] == "found"
    assert grade.call_count == 1

def test_failure_uses_maximum_three_grading_calls():
    with patch("src.grading._grade_batch", return_value=({}, {})) as grade:
        r = retrieve_and_grade_batch([group()], lambda q, expected_version=None: [{"text":"bad","version":expected_version,"doc_type":"migration"}])
    assert r["status"] == "not_found"
    assert grade.call_count == 3

def test_backward_compatible_single_group_wrapper_returns_chunks():
    with patch("src.grading._grade_batch", return_value=({0:True}, {})):
        r = retrieve_and_grade("q","2025-09-03","migration",lambda q, expected_version=None:[{"text":"ok","version":expected_version,"doc_type":"migration"}])
    assert r["status"] == "found"
    assert len(r["chunks"]) == 1
