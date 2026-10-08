"""Modular CI tests for the Generation stage.

These tests isolate ``src.generation`` from Gemini and from the retrieval,
grading, and verification pipeline. The broader ``verify/generation.py``
script remains the local/integration reference for real-data behavior.
"""

import json
from unittest.mock import patch

import pytest

from src.generation import (
    GEN_PROMPT,
    _parse_generation_response,
    build_citation,
    format_chunk_for_prompt,
    generate_answer,
)


@pytest.fixture
def reference_chunk():
    return {
        "chunk_id": "abc123",
        "text": "Use POST /v1/pages to create a page.",
        "doc_type": "reference",
        "version": "2025-09-03",
        "endpoint": "/v1/pages",
        "section": "Pages",
    }


@pytest.fixture
def graded_evidence(reference_chunk):
    return {
        "status": "found",
        "evidence_sufficient": True,
        "chunks": [reference_chunk],
    }


class FakeResponse:
    def __init__(self, text):
        self.text = text


# ---------------------------------------------------------------------------
# Prompt formatting
# ---------------------------------------------------------------------------


def test_format_chunk_for_prompt_contains_id_metadata_and_text(reference_chunk):
    formatted = format_chunk_for_prompt(reference_chunk)

    assert "Chunk ID: abc123" in formatted
    assert "2025-09-03" in formatted
    assert "/v1/pages" in formatted
    assert "Use POST /v1/pages to create a page." in formatted


def test_format_chunk_for_prompt_excludes_duplicate_top_level_text_and_id(
    reference_chunk,
):
    formatted = format_chunk_for_prompt(reference_chunk)

    assert "'chunk_id': 'abc123'" not in formatted
    assert "'text': 'Use POST /v1/pages to create a page.'" not in formatted


def test_generation_prompt_requires_json_and_grounded_chunk_ids():
    assert "ONLY valid JSON" in GEN_PROMPT
    assert "used_chunk_ids" in GEN_PROMPT
    assert "using ONLY the provided evidence" in GEN_PROMPT

# ---------------------------------------------------------------------------
# Citation construction
# ---------------------------------------------------------------------------


def test_build_citation_prefers_endpoint_identifier(reference_chunk):
    citation = build_citation(reference_chunk)

    assert citation == (
        "[Source: reference | /v1/pages | version 2025-09-03]"
    )


def test_build_citation_falls_back_to_section(reference_chunk):
    chunk = {
        "chunk_id": "abc123",
        "text": "Page information.",
        "doc_type": "reference",
        "version": "2025-09-03",
        "section": "Pages",
    }

    assert build_citation(chunk) == (
        "[Source: reference | Pages | version 2025-09-03]"
    )


def test_build_citation_uses_release_date_when_version_missing():
    chunk = {
        "chunk_id": "abc123",
        "text": "Release information.",
        "doc_type": "changelog",
        "release_date": "2025-09-03",
        "summary": "Page API changes",
    }

    assert build_citation(chunk) == (
        "[Source: changelog | Page API changes | version 2025-09-03]"
    )


def test_build_citation_falls_back_to_chunk_id():
    chunk = {
        "chunk_id": "abc123",
        "text": "Some evidence.",
        "doc_type": "reference",
    }

    assert build_citation(chunk) == (
        "[Source: reference | abc123 | version unknown]"
    )


# ---------------------------------------------------------------------------
# Generation response parsing
# ---------------------------------------------------------------------------


def test_parse_generation_response_accepts_valid_json():
    result = _parse_generation_response(
        '{"answer":"Use POST /v1/pages","used_chunk_ids":["abc123"]}'
    )

    assert result == {
        "answer": "Use POST /v1/pages",
        "used_chunk_ids": ["abc123"],
    }


def test_parse_generation_response_accepts_json_code_fence():
    result = _parse_generation_response(
        '```json\n{"answer":"A","used_chunk_ids":["abc123"]}\n```'
    )

    assert result["answer"] == "A"
    assert result["used_chunk_ids"] == ["abc123"]


def test_parse_generation_response_rejects_invalid_json():
    with pytest.raises(json.JSONDecodeError):
        _parse_generation_response("not valid json")


# ---------------------------------------------------------------------------
# Evidence gating
# ---------------------------------------------------------------------------


def test_generate_answer_abstains_when_evidence_is_insufficient():
    result = generate_answer(
        "How?",
        {
            "evidence_sufficient": False,
            "chunks": [],
        },
    )

    assert result["status"] == "not_found"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


def test_generate_answer_abstains_when_evidence_chunks_are_empty():
    result = generate_answer(
        "How?",
        {
            "evidence_sufficient": True,
            "chunks": [],
        },
    )

    assert result["status"] == "not_found"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


def test_generate_answer_does_not_call_llm_when_evidence_is_insufficient():
    with patch("src.generation.client.models.generate_content") as call:
        result = generate_answer(
            "How?",
            {
                "evidence_sufficient": False,
                "chunks": [],
            },
        )

    assert result["status"] == "not_found"
    call.assert_not_called()


# ---------------------------------------------------------------------------
# Successful generation
# ---------------------------------------------------------------------------


def test_generate_answer_returns_grounded_answer_and_citations(
    graded_evidence,
):
    response = FakeResponse(
        json.dumps(
            {
                "answer": "Use POST /v1/pages to create a page.",
                "used_chunk_ids": ["abc123"],
            }
        )
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ) as call:
        result = generate_answer(
            "How do I create a page?",
            graded_evidence,
        )

    assert result["status"] == "found"
    assert result["answer"] == "Use POST /v1/pages to create a page."
    assert result["used_chunk_ids"] == ["abc123"]
    assert result["citations"] == [
        "[Source: reference | /v1/pages | version 2025-09-03]"
    ]
    assert call.call_count == 1


def test_generate_answer_passes_question_and_evidence_to_llm(
    graded_evidence,
):
    response = FakeResponse(
        '{"answer":"A","used_chunk_ids":["abc123"]}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ) as call:
        generate_answer(
            "How do I create a page?",
            graded_evidence,
        )

    prompt = call.call_args.kwargs["contents"]

    assert "How do I create a page?" in prompt
    assert "abc123" in prompt
    assert "Use POST /v1/pages to create a page." in prompt


# ---------------------------------------------------------------------------
# used_chunk_ids validation
# ---------------------------------------------------------------------------


def test_generate_answer_filters_unknown_chunk_ids(reference_chunk):
    evidence = {
        "evidence_sufficient": True,
        "chunks": [reference_chunk],
    }

    response = FakeResponse(
        '{"answer":"A","used_chunk_ids":["abc123","unknown"]}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", evidence)

    assert result["status"] == "found"
    assert result["used_chunk_ids"] == ["abc123"]
    assert len(result["citations"]) == 1


def test_generate_answer_ignores_non_string_chunk_ids(reference_chunk):
    evidence = {
        "evidence_sufficient": True,
        "chunks": [reference_chunk],
    }

    response = FakeResponse(
        '{"answer":"A","used_chunk_ids":[123,"abc123",null]}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", evidence)

    assert result["status"] == "found"
    assert result["used_chunk_ids"] == ["abc123"]


def test_generate_answer_abstains_when_used_chunk_ids_is_not_a_list(
    graded_evidence,
):
    response = FakeResponse(
        '{"answer":"A","used_chunk_ids":"abc123"}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", graded_evidence)

    assert result["status"] == "not_found"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


def test_generate_answer_abstains_when_answer_is_empty(
    graded_evidence,
):
    response = FakeResponse(
        '{"answer":"","used_chunk_ids":["abc123"]}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", graded_evidence)

    assert result["status"] == "not_found"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


def test_generate_answer_abstains_when_no_valid_chunk_ids_remain(
    graded_evidence,
):
    response = FakeResponse(
        '{"answer":"A","used_chunk_ids":["unknown"]}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", graded_evidence)

    assert result["status"] == "not_found"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


# ---------------------------------------------------------------------------
# LLM failure handling
# ---------------------------------------------------------------------------


def test_generate_answer_handles_llm_service_error(graded_evidence):
    with patch(
        "src.generation.client.models.generate_content",
        side_effect=RuntimeError("service unavailable"),
    ):
        result = generate_answer("How?", graded_evidence)

    assert result["status"] == "generation_error"
    assert result["error_type"] == "llm_service_error"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


def test_generate_answer_handles_invalid_llm_json(graded_evidence):
    response = FakeResponse("not valid json")

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", graded_evidence)

    assert result["status"] == "generation_error"
    assert result["error_type"] == "invalid_llm_response"
    assert result["used_chunk_ids"] == []
    assert result["citations"] == []


def test_generate_answer_handles_missing_response_text(graded_evidence):
    class ResponseWithoutText:
        pass

    with patch(
        "src.generation.client.models.generate_content",
        return_value=ResponseWithoutText(),
    ):
        result = generate_answer("How?", graded_evidence)

    assert result["status"] == "generation_error"
    assert result["error_type"] == "invalid_llm_response"


# ---------------------------------------------------------------------------
# Multiple supporting chunks
# ---------------------------------------------------------------------------


def test_generate_answer_creates_one_citation_per_used_chunk(
    reference_chunk,
):
    second = {
        **reference_chunk,
        "chunk_id": "def456",
        "endpoint": "/v1/pages/{page_id}",
        "text": "GET /v1/pages/{page_id} retrieves a page.",
    }

    evidence = {
        "evidence_sufficient": True,
        "chunks": [reference_chunk, second],
    }

    response = FakeResponse(
        '{"answer":"A","used_chunk_ids":["abc123","def456"]}'
    )

    with patch(
        "src.generation.client.models.generate_content",
        return_value=response,
    ):
        result = generate_answer("How?", evidence)

    assert result["status"] == "found"
    assert result["used_chunk_ids"] == [
        "abc123",
        "def456",
    ]

    assert len(result["citations"]) == 2

    assert result["citations"][0] == (
        "[Source: reference | /v1/pages | version 2025-09-03]"
    )

    assert result["citations"][1] == (
        "[Source: reference | /v1/pages/{page_id} | version 2025-09-03]"
    )