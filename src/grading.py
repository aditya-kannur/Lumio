"""
LLM grading for one retrieved evidence group.

Flow:

    RRF retrieval
        ↓
    complete reranked chunk set
        ↓
    ONE Gemini grading call
        ↓
    group-level evidence decision
        ↓
    sufficient → return selected evidence
    insufficient → rewrite query → retrieve again

Maximum Gemini grading calls:
    MAX_RETRIES + 1

With MAX_RETRIES = 2:
    Attempt 1
    Attempt 2
    Attempt 3
"""

import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.grading_config import MAX_RETRIES, MAX_GRADING_CHUNKS
from src.messages import (
    NOT_FOUND_MESSAGE,
    RETRIEVAL_NOT_FOUND_MESSAGE,
    GRADER_ERROR_MESSAGE,
)


load_dotenv()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL = "gemini-3.5-flash-lite"


# ---------------------------------------------------------------------------
# GROUP GRADING PROMPT
# ---------------------------------------------------------------------------

GROUP_GRADING_PROMPT = """
You are the evidence grader for a version-aware developer documentation
assistant.

You are given ONE complete reranked retrieval result set for ONE user
question.

You must judge the evidence as a GROUP, not as independent retrieval
decisions.

User question:
{question}

Expected API version:
{expected_version}

Expected document type:
{expected_doc_type}

Search query used for this retrieval attempt:
{search_query}

Retrieved candidates, in RRF/reranked order:
{candidates}

For every candidate evaluate:

1. relevant
   Does the chunk contain information that helps answer the question?

2. version_correct
   Does the chunk match the expected API version?

3. doc_type_correct
   Is the chunk an appropriate document type for this question?

Then evaluate the COMPLETE SET together.

Determine:

4. evidence_sufficient
   Is the selected evidence collectively sufficient to answer the user's
   question without guessing or using outside knowledge?

5. selected_candidate_ids
   Which candidates should be passed to generation?

6. rewritten_question
   If the evidence is insufficient, provide ONE better search query for
   the next retrieval attempt.

Return ONLY valid JSON:

{{
  "evidence_sufficient": true,
  "selected_candidate_ids": [0, 2],
  "results": [
    {{
      "candidate_id": 0,
      "relevant": true,
      "version_correct": true,
      "doc_type_correct": true
    }}
  ],
  "rewritten_question": null,
  "reason": "short explanation"
}}

Rules:

- Include one result for every candidate.
- Never select a candidate unless all three candidate checks are true.
- selected_candidate_ids may contain only valid candidate IDs.
- evidence_sufficient is a GROUP decision.
- Do NOT require every candidate to be relevant.
- Some retrieved chunks may be irrelevant while the overall evidence is
  still sufficient.
- The selected chunks must collectively contain enough information to answer
  the question.
- Do not invent versions, endpoints, behavior, or facts.
- If evidence is insufficient, rewritten_question must target the missing
  information.
- If evidence is sufficient, rewritten_question must be null.
"""


# ---------------------------------------------------------------------------
# FORMAT RRF RESULTS
# ---------------------------------------------------------------------------

def _format_candidates(
    question,
    expected_version,
    expected_doc_type,
    chunks,
):
    """
    Convert the complete RRF result set into one grading group.
    """

    candidates = []

    for candidate_id, chunk in enumerate(chunks):

       candidates.append(
    {
        "candidate_id": candidate_id,
        "chunk_id": chunk.get("chunk_id"),
        "question": question,
        "expected_version": expected_version,
        "expected_doc_type": expected_doc_type,
        "chunk_metadata": {
            key: value
            for key, value in chunk.items()
            if key != "text"
        },
        "chunk_text": chunk.get("text", ""),
    }
    )

    return candidates


# ---------------------------------------------------------------------------
# PARSE GRADER RESPONSE
# ---------------------------------------------------------------------------

def _parse_grade_response(
    response_text,
    candidate_count,
):
    """
    Validate and normalize the Gemini group-grading response.
    """

    result = json.loads(
        response_text.strip()
    )

    raw_results = result.get(
        "results",
        [],
    )

    results = {}

    for item in raw_results:

        candidate_id = item.get(
            "candidate_id"
        )

        if not isinstance(
            candidate_id,
            int,
        ):
            continue

        if not (
            0 <= candidate_id < candidate_count
        ):
            continue

        results[candidate_id] = {
            "relevant": bool(
                item.get(
                    "relevant",
                    False,
                )
            ),
            "version_correct": bool(
                item.get(
                    "version_correct",
                    False,
                )
            ),
            "doc_type_correct": bool(
                item.get(
                    "doc_type_correct",
                    False,
                )
            ),
        }

    selected_ids = []

    for candidate_id in result.get(
        "selected_candidate_ids",
        [],
    ):

        if not isinstance(
            candidate_id,
            int,
        ):
            continue

        if not (
            0 <= candidate_id < candidate_count
        ):
            continue

        checks = results.get(
            candidate_id,
            {},
        )

        if (
            checks.get("relevant", False)
            and checks.get("version_correct", False)
            and checks.get("doc_type_correct", False)
        ):
            selected_ids.append(
                candidate_id
            )

    evidence_sufficient = bool(
        result.get(
            "evidence_sufficient",
            False,
        )
    )

    # Never allow "sufficient" with zero usable evidence.
    if not selected_ids:
        evidence_sufficient = False

    rewritten_question = result.get(
        "rewritten_question"
    )

    if (
        not isinstance(
            rewritten_question,
            str,
        )
        or not rewritten_question.strip()
    ):
        rewritten_question = None

    return {
        "evidence_sufficient": evidence_sufficient,
        "selected_candidate_ids": selected_ids,
        "results": results,
        "rewritten_question": rewritten_question,
        "reason": str(
            result.get(
                "reason",
                "",
            )
        ).strip(),
    }


# ---------------------------------------------------------------------------
# ONE GROUP = ONE GEMINI CALL
# ---------------------------------------------------------------------------

def _grade_group(
    question,
    expected_version,
    expected_doc_type,
    search_query,
    chunks,
):
    """
    Grade the COMPLETE RRF result set in exactly one Gemini call.
    """

    if not chunks:

        return {
            "status": "no_candidates",
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "selected_chunks": [],
            "rewritten_question": None,
            "reason": (
                "Retrieval returned no candidates."
            ),
        }

    candidates = _format_candidates(
        question,
        expected_version,
        expected_doc_type,
        chunks,
    )

    prompt = GROUP_GRADING_PROMPT.format(
        question=question,
        expected_version=expected_version,
        expected_doc_type=expected_doc_type,
        search_query=search_query,
        candidates=json.dumps(
            candidates,
            ensure_ascii=False,
        ),
    )

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )

        parsed = _parse_grade_response(
            response.text,
            len(chunks),
        )

    except (
        json.JSONDecodeError,
        AttributeError,
        TypeError,
        KeyError,
        ValueError,
    ) as exc:

        return {
            "status": "grader_error",
            "error_type": "invalid_grader_response",
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "selected_chunks": [],
            "rewritten_question": None,
            "reason": "Grader response could not be validated.",
        }

    except Exception:
        return {
            "status": "grader_error",
            "error_type": "grader_service_error",
            "evidence_sufficient": False,
            "selected_candidate_ids": [],
            "selected_chunks": [],
            "rewritten_question": None,
            "reason": "The grading service failed.",
        }

    selected_chunks = [
        chunks[candidate_id]
        for candidate_id
        in parsed["selected_candidate_ids"]
    ]

    return {
        "status": (
            "found"
            if parsed["evidence_sufficient"]
            else "insufficient"
        ),
        **parsed,
        "selected_chunks": selected_chunks,
    }


# ---------------------------------------------------------------------------
# RETRIEVE → GRADE → RETRY
# ---------------------------------------------------------------------------

def retrieve_and_grade(
    question,
    expected_version,
    expected_doc_type,
    retrieve_fn,
    on_attempt=None,
):
    """
    Retrieve and globally grade one evidence group.

    The original user question is preserved.

    search_query is the query actually sent to retrieval.

    On insufficient evidence, Gemini may rewrite search_query.

    Maximum attempts:
        MAX_RETRIES + 1
    """

    original_question = question
    search_query = question

    for attempt in range(
        1,
        MAX_RETRIES + 2,
    ):

        # --------------------------------------------------------------
        # RETRIEVAL
        # --------------------------------------------------------------

        retrieved = retrieve_fn(
            search_query,
            expected_version=expected_version,
        )

        if isinstance(
            retrieved,
            dict,
        ):
            chunks = retrieved.get(
                "chunks",
                [],
            )
        else:
            chunks = retrieved

        if not isinstance(
            chunks,
            list,
        ):
            chunks = []

        # Retrieval is already RRF-ranked.
        chunks = chunks[
            :MAX_GRADING_CHUNKS
        ]

        if on_attempt:
            on_attempt(
                {
                    "attempt": attempt,
                    "search_query": search_query,
                    "retrieved_chunks": chunks,
                }
            )

        # --------------------------------------------------------------
        # NO RETRIEVAL RESULTS
        # --------------------------------------------------------------

        if not chunks:

            if attempt == MAX_RETRIES + 1:
                return {
                    "status": "not_found",
                    "message": RETRIEVAL_NOT_FOUND_MESSAGE,
                    "attempts": attempt,
                    "original_question": original_question,
                    "search_query": search_query,
                }

            # Retry retrieval using the same query.
            continue

        # --------------------------------------------------------------
        # ONE GLOBAL GRADING CALL
        # --------------------------------------------------------------

        grading = _grade_group(
            question=original_question,
            expected_version=expected_version,
            expected_doc_type=expected_doc_type,
            search_query=search_query,
            chunks=chunks,
        )

        # --------------------------------------------------------------
        # SUCCESS
        # --------------------------------------------------------------

        if grading["status"] == "found":
            return {
                "status": "found",
                "message": "Evidence found.",
                "attempts": attempt,
                "original_question": original_question,
                "search_query": search_query,
                "chunks": grading.get(
                    "selected_chunks",
                    [],
                ),
                "selected_candidate_ids": grading.get(
                    "selected_candidate_ids",
                    [],
                ),
                "grading_reason": grading.get(
                    "reason",
                    "",
                ),
            }

        # --------------------------------------------------------------
        # GRADER ERROR
        # --------------------------------------------------------------

        if grading["status"] == "grader_error":

            if attempt == MAX_RETRIES + 1:
                return {
                    "status": "grading_error",
                    "message": GRADER_ERROR_MESSAGE,
                    "attempts": attempt,
                    "original_question": original_question,
                    "search_query": search_query,
                    "error_type": grading.get(
                        "error_type",
                        "grader_error",
                    ),
                }

            continue

        # --------------------------------------------------------------
        # INSUFFICIENT EVIDENCE
        # --------------------------------------------------------------

        rewritten_question = grading.get(
            "rewritten_question"
        )

        if rewritten_question:
            search_query = rewritten_question

        # --------------------------------------------------------------
        # FINAL FAILURE
        # --------------------------------------------------------------

        if attempt == MAX_RETRIES + 1:
            return {
                "status": "not_found",
                "message": NOT_FOUND_MESSAGE,
                "attempts": attempt,
                "original_question": original_question,
                "search_query": search_query,
                "grading_reason": grading.get(
                    "reason",
                    "",
                ),
            }

    return {
        "status": "not_found",
        "message": NOT_FOUND_MESSAGE,
        "attempts": MAX_RETRIES + 1,
        "original_question": original_question,
        "search_query": search_query,
    }


# ---------------------------------------------------------------------------
# LEGACY MULTI-GROUP API
# ---------------------------------------------------------------------------
#
# This is deliberately retained for the current migration implementation.
#
# Migration will be changed in the next step so that all migration-hop
# evidence is combined and globally graded as ONE evidence set.
#
# Do not use this path for normal reference grading.
# ---------------------------------------------------------------------------


def _format_legacy_candidates(groups):

    candidates = []

    candidate_id = 0

    for group in groups:

        for chunk in group["chunks"]:

            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "question": group["question"],
                    "expected_version": group[
                        "expected_version"
                    ],
                    "expected_doc_type": group[
                        "expected_doc_type"
                    ],
                    "chunk_metadata": {
                        key: value
                        for key, value in chunk.items()
                        if key != "text"
                    },
                    "chunk_text": chunk["text"],
                }
            )

            candidate_id += 1

    return candidates


def _grade_batch(groups):
    """
    Legacy migration grading path.

    This remains temporarily so migration code does not break while we
    redesign migration to use one combined evidence group.
    """

    candidates = _format_legacy_candidates(
        groups
    )

    if not candidates:
        return {}, {}

    prompt = """
You are grading retrieved document chunks.

Candidates:
{candidates}

Return ONLY valid JSON:

{{
  "results": [
    {{
      "candidate_id": 0,
      "relevant": true,
      "version_correct": true,
      "doc_type_correct": true
    }}
  ],
  "rewritten_questions": []
}}

A candidate passes only if all three checks are true.
""".format(
        candidates=json.dumps(
            candidates,
            ensure_ascii=False,
        )
    )

    try:

        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )

        result = json.loads(
            response.text.strip()
        )

        grades = {
            item["candidate_id"]: (
                item.get(
                    "relevant",
                    False,
                )
                and item.get(
                    "version_correct",
                    False,
                )
                and item.get(
                    "doc_type_correct",
                    False,
                )
            )
            for item in result.get(
                "results",
                [],
            )
        }

        rewrites = {
            item["candidate_id"]: item[
                "question"
            ]
            for item in result.get(
                "rewritten_questions",
                [],
            )
            if item.get("question")
        }

        return grades, rewrites

    except (
        json.JSONDecodeError,
        AttributeError,
        TypeError,
        KeyError,
        ValueError,
    ):
        return {}, {}


def _retrieve_groups(
    groups,
    retrieve_fn,
):
    """
    Legacy migration retrieval helper.
    """

    retrieved = []

    for group in groups:

        result = retrieve_fn(
            group["question"],
            expected_version=group[
                "expected_version"
            ],
        )

        if isinstance(
            result,
            dict,
        ):
            chunks = result.get(
                "chunks",
                [],
            )
        else:
            chunks = result

        if not isinstance(
            chunks,
            list,
        ):
            chunks = []

        retrieved.append(
            {
                **group,
                "chunks": chunks[
                    :MAX_GRADING_CHUNKS
                ],
            }
        )

    return retrieved


def retrieve_and_grade_batch(
    groups,
    retrieve_fn,
):
    """
    Legacy multi-group API.

    Kept temporarily for migration.

    It will be replaced by a migration-wide global evidence grader in the
    next architecture step.
    """

    current_groups = [
        dict(group)
        for group in groups
    ]

    for attempt in range(
        MAX_RETRIES + 1
    ):

        current_groups = _retrieve_groups(
            current_groups,
            retrieve_fn,
        )

        grades, rewrites = _grade_batch(
            current_groups
        )

        passed_groups = []

        candidate_id = 0

        rewrite_by_group = {}

        for group_index, group in enumerate(
            current_groups
        ):

            passed_chunks = []

            for chunk in group["chunks"]:

                if grades.get(
                    candidate_id,
                    False,
                ):
                    passed_chunks.append(
                        chunk
                    )

                if candidate_id in rewrites:
                    rewrite_by_group[
                        group_index
                    ] = rewrites[
                        candidate_id
                    ]

                candidate_id += 1

            if passed_chunks:

                passed_groups.append(
                    {
                        **group,
                        "chunks": passed_chunks,
                    }
                )

        if (
            len(passed_groups)
            == len(current_groups)
            and current_groups
        ):

            return {
                "status": "found",
                "groups": passed_groups,
            }

        if attempt >= MAX_RETRIES:
            break

        current_groups = [
            {
                **group,
                "question": rewrite_by_group.get(
                    i,
                    group["question"],
                ),
            }
            for i, group
            in enumerate(current_groups)
        ]

    return {
        "status": "not_found",
        "message": NOT_FOUND_MESSAGE,
    }


