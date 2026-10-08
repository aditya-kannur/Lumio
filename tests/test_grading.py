"""
GRADING STAGE TEST COVERAGE
===========================

This file tests the grading stage in isolation.

The grading stage being tested is:

    Retrieved RRF chunks
            |
            v
    Candidate formatting
            |
            v
       Gemini grader
            |
            v
    Response validation
            |
            +-------------------+
            |                   |
            v                   v
       sufficient          insufficient
            |                   |
            v                   v
      selected chunks      rewritten query
                                |
                                v
                         next retrieval attempt

The tests cover:

1. CANDIDATE FORMATTING
   - Every chunk becomes a candidate
   - Candidate IDs are sequential
   - Chunk metadata is preserved
   - Chunk text is separated from metadata

2. GRADER RESPONSE VALIDATION
   - Valid candidate IDs are accepted
   - Invalid candidate IDs are ignored
   - Candidate selection requires all three checks:
       relevant
       version_correct
       doc_type_correct
   - Invalid selected candidates are rejected
   - Empty selections force evidence_sufficient=False
   - Rewritten queries are normalized
   - Reasons are normalized

3. GROUP GRADING
   - Empty evidence does not call Gemini
   - One grading group produces one Gemini call
   - Selected candidate IDs map back to original chunks
   - Valid grading returns "found"
   - Insufficient evidence returns "insufficient"
   - Invalid JSON is handled
   - Gemini/service errors are handled

4. RETRIEVE -> GRADE -> RETRY
   - Retrieved chunks are capped at MAX_GRADING_CHUNKS
   - Successful grading stops immediately
   - Insufficient evidence triggers another attempt
   - Rewritten query is used on the next attempt
   - Original question remains unchanged
   - Maximum attempts are MAX_RETRIES + 1
   - Empty retrieval retries and eventually returns not_found
   - Final grading failure returns grading_error

Gemini is mocked in these tests.

These are modular CI tests, not end-to-end tests against the real
Gemini API or the complete retrieval pipeline.
"""

import json
from unittest.mock import patch

from src.grading import (
    _format_candidates,
    _parse_grade_response,
    _grade_group,
    retrieve_and_grade,
)
from src.grading_config import (
    MAX_GRADING_CHUNKS,
    MAX_RETRIES,
)


# ==============================================================
# TEST DATA
# ==============================================================


def make_chunk(
    chunk_id="chunk-1",
    text="valid evidence",
    version="2025-09-03",
    doc_type="reference",
):
    return {
        "chunk_id": chunk_id,
        "text": text,
        "version": version,
        "doc_type": doc_type,
    }


def make_group(
    chunks=None,
):
    return {
        "question": "How do I query a database?",
        "expected_version": "2025-09-03",
        "expected_doc_type": "reference",
        "chunks": chunks
        if chunks is not None
        else [make_chunk()],
    }


# ==============================================================
# CANDIDATE FORMATTING
# ==============================================================


def test_format_candidates_creates_one_candidate_per_chunk():
    chunks = [
        make_chunk("chunk-1", "first"),
        make_chunk("chunk-2", "second"),
        make_chunk("chunk-3", "third"),
    ]

    candidates = _format_candidates(
        question="How do I query a database?",
        expected_version="2025-09-03",
        expected_doc_type="reference",
        chunks=chunks,
    )

    assert len(candidates) == 3


def test_format_candidates_assigns_sequential_candidate_ids():
    chunks = [
        make_chunk("chunk-1"),
        make_chunk("chunk-2"),
        make_chunk("chunk-3"),
    ]

    candidates = _format_candidates(
        "question",
        "2025-09-03",
        "reference",
        chunks,
    )

    assert [
        candidate["candidate_id"]
        for candidate in candidates
    ] == [0, 1, 2]


def test_format_candidates_preserves_chunk_ids():
    chunks = [
        make_chunk("persistent-1"),
        make_chunk("persistent-2"),
    ]

    candidates = _format_candidates(
        "question",
        "2025-09-03",
        "reference",
        chunks,
    )

    assert [
        candidate["chunk_id"]
        for candidate in candidates
    ] == [
        "persistent-1",
        "persistent-2",
    ]


def test_format_candidates_preserves_chunk_text():
    chunks = [
        make_chunk(
            "chunk-1",
            "database query information",
        )
    ]

    candidates = _format_candidates(
        "question",
        "2025-09-03",
        "reference",
        chunks,
    )

    assert (
        candidates[0]["chunk_text"]
        == "database query information"
    )


def test_format_candidates_preserves_metadata():
    chunks = [
        {
            "chunk_id": "chunk-1",
            "text": "evidence",
            "version": "2025-09-03",
            "doc_type": "reference",
            "endpoint": "/v1/databases/query",
        }
    ]

    candidates = _format_candidates(
        "question",
        "2025-09-03",
        "reference",
        chunks,
    )

    metadata = candidates[0]["chunk_metadata"]

    assert metadata["chunk_id"] == "chunk-1"
    assert metadata["version"] == "2025-09-03"
    assert metadata["doc_type"] == "reference"
    assert metadata["endpoint"] == "/v1/databases/query"
    assert "text" not in metadata


def test_format_candidates_preserves_retrieval_order():
    chunks = [
        make_chunk("first"),
        make_chunk("second"),
        make_chunk("third"),
    ]

    candidates = _format_candidates(
        "question",
        "2025-09-03",
        "reference",
        chunks,
    )

    assert [
        candidate["chunk_id"]
        for candidate in candidates
    ] == [
        "first",
        "second",
        "third",
    ]


# ==============================================================
# GRADER RESPONSE VALIDATION
# ==============================================================


def test_parse_grade_response_accepts_valid_candidate():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [0],
            "results": [
                {
                    "candidate_id": 0,
                    "relevant": True,
                    "version_correct": True,
                    "doc_type_correct": True,
                }
            ],
            "rewritten_question": None,
            "reason": "Evidence is sufficient.",
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=1,
    )

    assert result["evidence_sufficient"] is True
    assert result["selected_candidate_ids"] == [0]
    assert result["results"][0]["relevant"] is True


def test_candidate_requires_all_three_checks_to_be_selected():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [0],
            "results": [
                {
                    "candidate_id": 0,
                    "relevant": True,
                    "version_correct": False,
                    "doc_type_correct": True,
                }
            ],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=1,
    )

    assert result["selected_candidate_ids"] == []
    assert result["evidence_sufficient"] is False


def test_candidate_fails_when_not_relevant():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [0],
            "results": [
                {
                    "candidate_id": 0,
                    "relevant": False,
                    "version_correct": True,
                    "doc_type_correct": True,
                }
            ],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=1,
    )

    assert result["selected_candidate_ids"] == []
    assert result["evidence_sufficient"] is False


def test_candidate_fails_when_doc_type_is_wrong():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [0],
            "results": [
                {
                    "candidate_id": 0,
                    "relevant": True,
                    "version_correct": True,
                    "doc_type_correct": False,
                }
            ],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=1,
    )

    assert result["selected_candidate_ids"] == []
    assert result["evidence_sufficient"] is False


def test_invalid_candidate_ids_are_ignored():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [
                -1,
                0,
                10,
            ],
            "results": [
                {
                    "candidate_id": 0,
                    "relevant": True,
                    "version_correct": True,
                    "doc_type_correct": True,
                },
                {
                    "candidate_id": 99,
                    "relevant": True,
                    "version_correct": True,
                    "doc_type_correct": True,
                },
            ],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=1,
    )

    assert result["selected_candidate_ids"] == [0]


def test_missing_results_prevent_evidence_from_being_sufficient():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [0],
            "results": [],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=1,
    )

    assert result["selected_candidate_ids"] == []
    assert result["evidence_sufficient"] is False


def test_empty_selection_forces_evidence_sufficient_false():
    response = json.dumps(
        {
            "evidence_sufficient": True,
            "selected_candidate_ids": [],
            "results": [],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=2,
    )

    assert result["evidence_sufficient"] is False
    assert result["selected_candidate_ids"] == []


def test_valid_rewritten_question_is_preserved():
    response = json.dumps(
        {
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "results": [],
            "rewritten_question": (
                "Which endpoint queries a database?"
            ),
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=2,
    )

    assert (
        result["rewritten_question"]
        == "Which endpoint queries a database?"
    )


def test_blank_rewritten_question_becomes_none():
    response = json.dumps(
        {
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "results": [],
            "rewritten_question": "   ",
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=2,
    )

    assert result["rewritten_question"] is None


def test_missing_rewritten_question_becomes_none():
    response = json.dumps(
        {
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "results": [],
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=2,
    )

    assert result["rewritten_question"] is None


def test_reason_is_normalized_to_string():
    response = json.dumps(
        {
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "results": [],
            "reason": "Missing endpoint details.",
        }
    )

    result = _parse_grade_response(
        response,
        candidate_count=2,
    )

    assert result["reason"] == (
        "Missing endpoint details."
    )


# ==============================================================
# GROUP GRADING
# ==============================================================


def test_empty_group_does_not_call_gemini():
    with patch(
        "src.grading.client.models.generate_content"
    ) as generate:

        result = _grade_group(
            question="question",
            expected_version="2025-09-03",
            expected_doc_type="reference",
            search_query="question",
            chunks=[],
        )

    assert result["status"] == "no_candidates"
    assert result["selected_chunks"] == []
    generate.assert_not_called()


def test_group_grading_makes_exactly_one_gemini_call():
    response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [0],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                }
            )
        },
    )()

    chunks = [make_chunk()]

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ) as generate:

        result = _grade_group(
            question="question",
            expected_version="2025-09-03",
            expected_doc_type="reference",
            search_query="question",
            chunks=chunks,
        )

    assert result["status"] == "found"
    assert generate.call_count == 1


def test_group_grading_selects_correct_original_chunk():
    response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [1],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": False,
                            "version_correct": True,
                            "doc_type_correct": True,
                        },
                        {
                            "candidate_id": 1,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        },
                    ],
                }
            )
        },
    )()

    chunks = [
        make_chunk("wrong", "wrong evidence"),
        make_chunk("correct", "correct evidence"),
    ]

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ):

        result = _grade_group(
            "question",
            "2025-09-03",
            "reference",
            "question",
            chunks,
        )

    assert result["selected_candidate_ids"] == [1]
    assert result["selected_chunks"] == [chunks[1]]


def test_group_grading_returns_insufficient_when_evidence_is_not_sufficient():
    response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": False,
                    "selected_candidate_ids": [],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": False,
                            "doc_type_correct": True,
                        }
                    ],
                    "rewritten_question": (
                        "Find the endpoint for database queries."
                    ),
                }
            )
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ):

        result = _grade_group(
            "question",
            "2025-09-03",
            "reference",
            "question",
            [make_chunk()],
        )

    assert result["status"] == "insufficient"
    assert result["selected_chunks"] == []
    assert (
        result["rewritten_question"]
        == "Find the endpoint for database queries."
    )


def test_group_grading_handles_invalid_json():
    response = type(
        "Response",
        (),
        {
            "text": "not valid json",
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ):

        result = _grade_group(
            "question",
            "2025-09-03",
            "reference",
            "question",
            [make_chunk()],
        )

    assert result["status"] == "grader_error"
    assert result["error_type"] == (
        "invalid_grader_response"
    )


def test_group_grading_handles_gemini_service_error():
    with patch(
        "src.grading.client.models.generate_content",
        side_effect=RuntimeError("service unavailable"),
    ):

        result = _grade_group(
            "question",
            "2025-09-03",
            "reference",
            "question",
            [make_chunk()],
        )

    assert result["status"] == "grader_error"
    assert result["error_type"] == (
        "grader_service_error"
    )


# ==============================================================
# RETRIEVE -> GRADE -> RETRY
# ==============================================================


def test_retrieve_and_grade_caps_chunks_before_grading():
    retrieved = [
        make_chunk(f"chunk-{i}")
        for i in range(MAX_GRADING_CHUNKS + 5)
    ]

    seen = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        return retrieved

    def on_attempt(info):
        seen.append(info)

    success_response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [0],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                }
            )
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        return_value=success_response,
    ):

        result = retrieve_and_grade(
            question="question",
            expected_version="2025-09-03",
            expected_doc_type="reference",
            retrieve_fn=retrieve_fn,
            on_attempt=on_attempt,
        )

    assert result["status"] == "found"
    assert len(
        seen[0]["retrieved_chunks"]
    ) == MAX_GRADING_CHUNKS


def test_success_stops_after_first_grading_attempt():
    calls = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        calls.append(query)
        return [make_chunk()]

    response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [0],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                }
            )
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ) as generate:

        result = retrieve_and_grade(
            "original question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "found"
    assert len(calls) == 1
    assert generate.call_count == 1


def test_insufficient_evidence_uses_rewritten_query():
    queries = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        queries.append(query)
        return [make_chunk()]

    insufficient = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": False,
                    "selected_candidate_ids": [],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": False,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                    "rewritten_question": "better query",
                }
            )
        },
    )()

    sufficient = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [0],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                    "rewritten_question": None,
                }
            )
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        side_effect=[
            insufficient,
            sufficient,
        ],
    ):

        result = retrieve_and_grade(
            "original question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "found"

    assert queries == [
        "original question",
        "better query",
    ]


def test_original_question_is_preserved_across_retry():
    seen_questions = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        return [make_chunk()]

    def fake_grade_group(**kwargs):
        seen_questions.append(
            kwargs["question"]
        )

        if len(seen_questions) == 1:
            return {
                "status": "insufficient",
                "evidence_sufficient": False,
                "selected_candidate_ids": [],
                "selected_chunks": [],
                "rewritten_question": "rewritten query",
                "reason": "insufficient",
            }

        return {
            "status": "found",
            "evidence_sufficient": True,
            "selected_candidate_ids": [0],
            "selected_chunks": [make_chunk()],
            "rewritten_question": None,
            "reason": "",
        }

    with patch(
        "src.grading._grade_group",
        side_effect=fake_grade_group,
    ):

        result = retrieve_and_grade(
            "original question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "found"

    assert seen_questions == [
        "original question",
        "original question",
    ]


def test_final_failure_respects_maximum_attempt_count():
    grading_calls = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        return [make_chunk()]

    insufficient = {
        "status": "insufficient",
        "evidence_sufficient": False,
        "selected_candidate_ids": [],
        "selected_chunks": [],
        "rewritten_question": None,
        "reason": "not enough evidence",
    }

    with patch(
        "src.grading._grade_group",
        side_effect=lambda **kwargs: (
            grading_calls.append(kwargs)
            or insufficient
        ),
    ):

        result = retrieve_and_grade(
            "question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "not_found"
    assert result["attempts"] == MAX_RETRIES + 1
    assert len(grading_calls) == MAX_RETRIES + 1


def test_empty_retrieval_does_not_call_grader():
    retrieve_calls = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        retrieve_calls.append(query)
        return []

    with patch(
        "src.grading._grade_group"
    ) as grade:

        result = retrieve_and_grade(
            "question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "not_found"
    assert grade.call_count == 0
    assert len(retrieve_calls) == MAX_RETRIES + 1


def test_grader_error_retries():
    retrieve_calls = []

    def retrieve_fn(
        query,
        expected_version=None,
    ):
        retrieve_calls.append(query)
        return [make_chunk()]

    grader_error = {
        "status": "grader_error",
        "error_type": "grader_service_error",
        "evidence_sufficient": False,
        "selected_candidate_ids": [],
        "selected_chunks": [],
        "rewritten_question": None,
        "reason": "",
    }

    with patch(
        "src.grading._grade_group",
        return_value=grader_error,
    ):

        result = retrieve_and_grade(
            "question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "grading_error"
    assert result["attempts"] == MAX_RETRIES + 1
    assert len(retrieve_calls) == MAX_RETRIES + 1


def test_retrieve_function_can_return_chunk_list_directly():
    def retrieve_fn(
        query,
        expected_version=None,
    ):
        return [make_chunk()]

    response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [0],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                }
            )
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ):

        result = retrieve_and_grade(
            "question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "found"


def test_retrieve_function_can_return_chunks_inside_dict():
    def retrieve_fn(
        query,
        expected_version=None,
    ):
        return {
            "chunks": [make_chunk()]
        }

    response = type(
        "Response",
        (),
        {
            "text": json.dumps(
                {
                    "evidence_sufficient": True,
                    "selected_candidate_ids": [0],
                    "results": [
                        {
                            "candidate_id": 0,
                            "relevant": True,
                            "version_correct": True,
                            "doc_type_correct": True,
                        }
                    ],
                }
            )
        },
    )()

    with patch(
        "src.grading.client.models.generate_content",
        return_value=response,
    ):

        result = retrieve_and_grade(
            "question",
            "2025-09-03",
            "reference",
            retrieve_fn,
        )

    assert result["status"] == "found"