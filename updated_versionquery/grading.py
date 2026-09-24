"""Batched LLM grading: one Gemini call grades all retrieved chunks per attempt."""

import os
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

from src.grading_config import MAX_RETRIES, MAX_GRADING_CHUNKS
from src.messages import NOT_FOUND_MESSAGE


client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"


BATCH_GRADING_PROMPT = """You are grading retrieved document chunks for a developer documentation assistant.

For every candidate, check:
1. relevant: the chunk addresses the candidate question;
2. version_correct: the chunk matches the expected version;
3. doc_type_correct: the chunk matches the expected document type.

Candidates:
{candidates}

Return ONLY valid JSON in this exact shape:
{{
  "results": [
    {{"candidate_id": 0, "relevant": true, "version_correct": true, "doc_type_correct": true}}
  ],
  "rewritten_questions": [
    {{"candidate_id": 0, "question": "clearer search question"}}
  ]
}}

Include one result for every candidate. Only include a rewritten question for
candidates that do not pass all three checks. Do not invent facts or versions.
"""


def _format_candidates(groups):
    candidates = []
    candidate_id = 0
    for group in groups:
        for chunk in group["chunks"]:
            candidates.append({
                "candidate_id": candidate_id,
                "question": group["question"],
                "expected_version": group["expected_version"],
                "expected_doc_type": group["expected_doc_type"],
                "chunk_metadata": {k: v for k, v in chunk.items() if k != "text"},
                "chunk_text": chunk["text"],
            })
            candidate_id += 1
    return candidates


def _grade_batch(groups):
    candidates = _format_candidates(groups)
    if not candidates:
        return {}, {}

    prompt = BATCH_GRADING_PROMPT.format(
        candidates=json.dumps(candidates, ensure_ascii=False)
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(response_mime_type="application/json"),
        )
        result = json.loads(response.text.strip())

        grades = {
            item["candidate_id"]: (
                item.get("relevant", False)
                and item.get("version_correct", False)
                and item.get("doc_type_correct", False)
            )
            for item in result.get("results", [])
        }
        rewrites = {
            item["candidate_id"]: item["question"]
            for item in result.get("rewritten_questions", [])
            if item.get("question")
        }
        return grades, rewrites
    except (json.JSONDecodeError, AttributeError, TypeError, KeyError):
        return {}, {}


def _retrieve_groups(groups, retrieve_fn):
    retrieved = []
    for group in groups:
        chunks = retrieve_fn(
            group["question"],
            expected_version=group["expected_version"],
        )[:MAX_GRADING_CHUNKS]
        retrieved.append({**group, "chunks": chunks})
    return retrieved


def retrieve_and_grade_batch(groups, retrieve_fn):
    """At most MAX_RETRIES + 1 Gemini grading calls for the whole request."""
    current_groups = [dict(group) for group in groups]

    for attempt in range(MAX_RETRIES + 1):
        current_groups = _retrieve_groups(current_groups, retrieve_fn)
        grades, rewrites = _grade_batch(current_groups)

        passed_groups = []
        candidate_id = 0
        rewrite_by_group = {}

        for group_index, group in enumerate(current_groups):
            passed_chunks = []
            for chunk in group["chunks"]:
                if grades.get(candidate_id, False):
                    passed_chunks.append(chunk)
                if candidate_id in rewrites:
                    rewrite_by_group[group_index] = rewrites[candidate_id]
                candidate_id += 1

            if passed_chunks:
                passed_groups.append({**group, "chunks": passed_chunks})

        if len(passed_groups) == len(current_groups) and current_groups:
            return {"status": "found", "groups": passed_groups}

        if attempt < MAX_RETRIES:
            current_groups = [
                {
                    **group,
                    "question": rewrite_by_group.get(i, group["question"]),
                }
                for i, group in enumerate(current_groups)
            ]

    return {"status": "not_found", "message": NOT_FOUND_MESSAGE}


def retrieve_and_grade(question, expected_version, expected_doc_type, retrieve_fn):
    """Backward-compatible wrapper for non-migration queries."""
    result = retrieve_and_grade_batch([
        {
            "question": question,
            "expected_version": expected_version,
            "expected_doc_type": expected_doc_type,
        }
    ], retrieve_fn)

    if result["status"] != "found":
        return result

    return {"status": "found", "chunks": result["groups"][0]["chunks"]}
