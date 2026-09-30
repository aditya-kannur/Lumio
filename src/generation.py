import json
import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-3.5-flash-lite"

CITATION_TEMPLATE = (
    "[Source: {doc_type} | {identifier} | version {version}]"
)

GEN_PROMPT = """
Answer the developer's question using ONLY the provided evidence.

Do not use outside knowledge.
Do not invent facts.
Only use claims that are supported by the evidence.

Question:
{question}

Evidence:
{chunks_text}

Return ONLY valid JSON:

{{
  "answer": "clear direct answer",
  "used_chunk_ids": ["persistent_chunk_id_1"]
}}

Rules:
- used_chunk_ids must contain ONLY chunk IDs that directly support the answer.
- Do not include irrelevant chunks.
- If the evidence does not support an answer, return an empty answer
  and an empty used_chunk_ids list.
"""


def format_chunk_for_prompt(chunk):
    chunk_id = chunk.get("chunk_id", "")

    meta = {
        k: v
        for k, v in chunk.items()
        if k not in {"text", "chunk_id"}
    }

    return (
        "---\n"
        f"Chunk ID: {chunk_id}\n"
        f"Metadata: {meta}\n"
        f"Text: {chunk['text']}\n"
        "---"
    )


def build_citation(chunk):
    doc_type = chunk.get("doc_type", "unknown")

    version = (
        chunk.get("version")
        or chunk.get("release_date")
        or "unknown"
    )

    identifier = (
        chunk.get("endpoint")
        or chunk.get("section")
        or chunk.get("summary", "")[:50]
        or chunk.get("chunk_id", "unknown")
    )

    return CITATION_TEMPLATE.format(
        doc_type=doc_type,
        identifier=identifier,
        version=version,
    )


def _parse_generation_response(response_text):
    text = response_text.strip()

    if text.startswith("```"):
        text = text.replace("```json", "", 1)
        text = text.replace("```", "", 1).strip()

    return json.loads(text)


def generate_answer(question, graded_evidence):
    """
    Generate an answer only from evidence accepted by grading.

    Returns:
        {
            "status": "found" | "not_found",
            "answer": str,
            "used_chunk_ids": list[str],
            "citations": list[str]
        }
    """

    if not graded_evidence.get("evidence_sufficient"):
        return {
            "status": "not_found",
            "answer": (
                "The available evidence is insufficient "
                "to answer this question reliably."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    chunks = graded_evidence.get("chunks", [])

    if not chunks:
        return {
            "status": "not_found",
            "answer": (
                "The available evidence is insufficient "
                "to answer this question reliably."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    valid_chunk_ids = {
        chunk["chunk_id"]
        for chunk in chunks
        if chunk.get("chunk_id")
    }

    chunks_text = "\n".join(
        format_chunk_for_prompt(chunk)
        for chunk in chunks
    )

    prompt = GEN_PROMPT.format(
        question=question,
        chunks_text=chunks_text,
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
    except Exception:
        return {
            "status": "generation_error",
            "error_type": "llm_service_error",
            "answer": (
                "The answer could not be generated because "
                "the language model service is unavailable."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    try:
        result = _parse_generation_response(response.text)
    except (json.JSONDecodeError, AttributeError, TypeError):
        return {
            "status": "generation_error",
            "error_type": "invalid_llm_response",
            "answer": (
                "The generated response could not be "
                "validated against the evidence."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    answer = str(result.get("answer", "")).strip()

    used_chunk_ids = result.get("used_chunk_ids", [])

    if not isinstance(used_chunk_ids, list):
        used_chunk_ids = []

    # Only allow IDs that actually exist in graded evidence.
    used_chunk_ids = [
        chunk_id
        for chunk_id in used_chunk_ids
        if isinstance(chunk_id, str)
        and chunk_id in valid_chunk_ids
    ]

    if not answer or not used_chunk_ids:
        return {
            "status": "not_found",
            "answer": (
                "The available evidence is insufficient "
                "to generate a reliable answer."
            ),
            "used_chunk_ids": [],
            "citations": [],
        }

    chunks_by_id = {
        chunk["chunk_id"]: chunk
        for chunk in chunks
        if chunk.get("chunk_id")
    }

    citations = [
        build_citation(chunks_by_id[chunk_id])
        for chunk_id in used_chunk_ids
    ]

    return {
        "status": "found",
        "answer": answer,
        "used_chunk_ids": used_chunk_ids,
        "citations": citations,
    }
