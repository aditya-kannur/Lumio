from unittest.mock import patch
import json

import pytest

from src.query_understanding import understand_query, MODEL
from src.constants import KNOWN_VERSIONS


class FakeResponse:
    def __init__(self, text):
        self.text = text


def test_query_understanding_uses_one_structured_llm_call():
    response = FakeResponse(
        '{"intent":"reference","version":"2025-09-03"}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        result = understand_query(
            "How do I create a page in 2025-09-03?"
        )

    assert result == {
        "intent": "reference",
        "version": "2025-09-03",
    }

    assert call.call_count == 1
    assert call.call_args.kwargs["model"] == MODEL
    assert call.call_args.kwargs["config"] == {
        "response_mime_type": "application/json"
    }


def test_query_understanding_supports_migration_shape():
    response = FakeResponse(
        '{"intent":"migration",'
        '"from_version":"2021-08-16",'
        '"to_version":"2022-06-28"}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query("How do I upgrade?")

    assert result["intent"] == "migration"
    assert result["from_version"] == "2021-08-16"
    assert result["to_version"] == "2022-06-28"


def test_query_understanding_parses_valid_json():
    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query("How do I create a page?")

    assert isinstance(result, dict)
    assert result["intent"] == "reference"
    assert result["version"] is None


def test_query_understanding_preserves_explicit_known_version():
    version = KNOWN_VERSIONS[0]

    response = FakeResponse(
        json.dumps(
            {
                "intent": "reference",
                "version": version,
            }
        )
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            f"How does the API work in {version}?"
        )

    assert result["version"] == version


def test_query_understanding_preserves_explicit_unknown_version():
    unknown_version = "2030-01-01"

    response = FakeResponse(
        json.dumps(
            {
                "intent": "reference",
                "version": unknown_version,
            }
        )
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            f"How does the API work in {unknown_version}?"
        )

    assert result["version"] == unknown_version


def test_query_understanding_preserves_unknown_migration_versions():
    response = FakeResponse(
        json.dumps(
            {
                "intent": "migration",
                "from_version": "2030-01-01",
                "to_version": "2031-01-01",
            }
        )
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            "How do I migrate from 2030-01-01 to 2031-01-01?"
        )

    assert result["from_version"] == "2030-01-01"
    assert result["to_version"] == "2031-01-01"


def test_query_understanding_allows_missing_version():
    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            "How do I create a page?"
        )

    assert result["version"] is None


def test_query_understanding_includes_current_question_in_prompt():
    question = "How do I configure webhook retries?"

    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        understand_query(question)

    prompt = call.call_args.kwargs["contents"]

    assert question in prompt
    assert "Current user question:" in prompt


def test_query_understanding_includes_known_versions_in_prompt():
    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        understand_query("How do I create a page?")

    prompt = call.call_args.kwargs["contents"]

    assert "Known versions:" in prompt

    for version in KNOWN_VERSIONS:
        assert version in prompt


def test_query_understanding_includes_history_in_prompt():
    history = [
        {
            "question": "How do I create a page?",
            "response": {
                "intent": "reference",
                "version": "2022-06-28",
            },
        }
    ]

    response = FakeResponse(
        '{"intent":"reference","version":"2022-06-28"}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        understand_query("What about this version?", history)

    prompt = call.call_args.kwargs["contents"]

    assert "Previous conversation:" in prompt
    assert "How do I create a page?" in prompt
    assert "2022-06-28" in prompt
    assert "What about this version?" in prompt


def test_query_understanding_limits_history_to_latest_five_turns():
    history = [
        {
            "question": f"old question {i}",
            "response": {"version": f"version-{i}"},
        }
        for i in range(7)
    ]

    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        understand_query("Current question", history)

    prompt = call.call_args.kwargs["contents"]

    assert "old question 0" not in prompt
    assert "old question 1" not in prompt

    for i in range(2, 7):
        assert f"old question {i}" in prompt


def test_query_understanding_history_preserves_question_and_response():
    history = [
        {
            "question": "What changed?",
            "response": {
                "intent": "changelog",
                "version": "2025-09-03",
            },
        }
    ]

    response = FakeResponse(
        '{"intent":"changelog","version":"2025-09-03"}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        result = understand_query(
            "What about that version?",
            history,
        )

    prompt = call.call_args.kwargs["contents"]

    assert result["intent"] == "changelog"
    assert result["version"] == "2025-09-03"

    assert "User: What changed?" in prompt
    assert '"intent": "changelog"' in prompt
    assert '"version": "2025-09-03"' in prompt


def test_query_understanding_current_question_takes_priority_over_history():
    history = [
        {
            "question": "Tell me about 2022-06-28",
            "response": {
                "intent": "reference",
                "version": "2022-06-28",
            },
        }
    ]

    response = FakeResponse(
        '{"intent":"reference","version":"2025-09-03"}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            "Now tell me about 2025-09-03",
            history,
        )

    assert result["version"] == "2025-09-03"


def test_query_understanding_supports_follow_up_version_question():
    history = [
        {
            "question": "How do I create a page?",
            "response": {
                "intent": "reference",
                "version": None,
            },
        }
    ]

    response = FakeResponse(
        '{"intent":"reference","version":"2022-06-28"}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            "2022-06-28",
            history,
        )

    assert result["intent"] == "reference"
    assert result["version"] == "2022-06-28"


def test_query_understanding_accepts_empty_history():
    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        result = understand_query(
            "How do I create a page?",
            [],
        )

    assert result["intent"] == "reference"

    prompt = call.call_args.kwargs["contents"]
    assert "Previous conversation:" not in prompt


def test_query_understanding_accepts_none_history():
    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query(
            "How do I create a page?",
            None,
        )

    assert result["intent"] == "reference"


def test_query_understanding_rejects_non_json_model_output():
    response = FakeResponse("not json")

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        with pytest.raises(ValueError, match="Invalid JSON"):
            understand_query("question")


def test_query_understanding_rejects_empty_model_output():
    response = FakeResponse("")

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        with pytest.raises(ValueError):
            understand_query("question")


def test_query_understanding_rejects_json_array_response():
    response = FakeResponse(
        '["reference", "2025-09-03"]'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query("question")

    assert isinstance(result, list)


def test_query_understanding_propagates_llm_error():
    with patch(
        "src.query_understanding.client.models.generate_content",
        side_effect=RuntimeError("Gemini unavailable"),
    ):
        with pytest.raises(RuntimeError, match="Gemini unavailable"):
            understand_query("question")


def test_query_understanding_passes_json_response_configuration():
    response = FakeResponse(
        '{"intent":"reference","version":null}'
    )

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ) as call:
        understand_query("question")

    assert call.call_args.kwargs["config"]["response_mime_type"] == (
        "application/json"
    )


def test_query_understanding_returns_model_fields_without_modifying_them():
    response_data = {
        "intent": "diagnostic",
        "version": "2025-09-03",
        "extra_field": "preserved",
    }

    response = FakeResponse(json.dumps(response_data))

    with patch(
        "src.query_understanding.client.models.generate_content",
        return_value=response,
    ):
        result = understand_query("Why does this fail?")

    assert result == response_data