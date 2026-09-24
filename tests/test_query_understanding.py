from unittest.mock import patch
import pytest

from src.query_understanding import understand_query, MODEL

def test_query_understanding_uses_one_structured_llm_call():
    class R: text = '{"intent":"reference","version":"2025-09-03"}'
    with patch("src.query_understanding.client.models.generate_content", return_value=R()) as call:
        result = understand_query("How do I create a page in 2025-09-03?")
    assert result == {"intent":"reference","version":"2025-09-03"}
    assert call.call_count == 1
    assert call.call_args.kwargs["model"] == MODEL

def test_query_understanding_supports_migration_shape():
    class R: text = '{"intent":"migration","from_version":"2021-08-16","to_version":"2022-06-28"}'
    with patch("src.query_understanding.client.models.generate_content", return_value=R()):
        result = understand_query("How do I upgrade?")
    assert result["intent"] == "migration"
    assert result["from_version"] == "2021-08-16"
    assert result["to_version"] == "2022-06-28"

def test_query_understanding_rejects_non_json_model_output():
    class R: text = "not json"
    with patch("src.query_understanding.client.models.generate_content", return_value=R()):
        with pytest.raises(ValueError):
            understand_query("question")
