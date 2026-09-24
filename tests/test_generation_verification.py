from unittest.mock import patch

from src.generation import format_chunk_for_prompt, build_citation, generate_answer
from src.verification import verify_answer, generate_verified_answer

def ref():
    return {"text":"Use POST /v1/pages","doc_type":"reference","version":"2025-09-03","endpoint":"/v1/pages","section":"Pages"}

def test_generation_prompt_contains_chunk_metadata_and_text():
    formatted=format_chunk_for_prompt(ref())
    assert "2025-09-03" in formatted
    assert "/v1/pages" in formatted
    assert "Use POST" in formatted

def test_citation_contains_source_identifier_and_version():
    c=build_citation(ref())
    assert c == "[Source: reference | /v1/pages | version 2025-09-03]"

def test_generation_returns_answer_and_one_citation_per_chunk():
    class R: text="Grounded answer"
    with patch("src.generation.client.models.generate_content", return_value=R()) as call:
        r=generate_answer("How?",[ref(),{**ref(),"endpoint":"/v1/other"}])
    assert r["answer"] == "Grounded answer"
    assert len(r["citations"]) == 2
    assert call.call_count == 1

def test_verification_parses_supported_verdict():
    class R: text='{"supported":true,"version_mixed":false}'
    with patch("src.verification.client.models.generate_content", return_value=R()):
        assert verify_answer("answer",[ref()]) == {"supported":True,"version_mixed":False}

def test_verification_invalid_json_is_rejected():
    class R: text="invalid"
    with patch("src.verification.client.models.generate_content", return_value=R()):
        assert verify_answer("answer",[ref()]) == {"supported":False,"version_mixed":True}

def test_generate_verified_answer_returns_ok_when_supported():
    with patch("src.verification.verify_answer", return_value={"supported":True,"version_mixed":False}):
        r=generate_verified_answer("q",[ref()],lambda q,c:{"answer":"a","citations":["c"]})
    assert r == {"status":"ok","answer":"a","citations":["c"]}

def test_generate_verified_answer_flags_unsupported_answer():
    with patch("src.verification.verify_answer", return_value={"supported":False,"version_mixed":False}):
        r=generate_verified_answer("q",[ref()],lambda q,c:{"answer":"a","citations":["c"]})
    assert r == {"status":"hallucination_flagged","answer":None}
