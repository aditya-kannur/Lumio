import json
import os

from google import genai
from dotenv import load_dotenv


load_dotenv()


client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"]
)

MODEL = "gemini-3.5-flash-lite"


VERIFY_PROMPT = """
You are the final verification layer for a version-aware developer
documentation QA system.

Verify the generated answer against ONLY the supplied evidence.

Question:
{question}

Generated answer:
{answer}

Evidence used by generation:
{source_text}

Check all of the following:

1. supported
   Are all factual claims in the answer supported by the evidence?

2. version_mixed
   Does the answer mix information from different API versions?

3. irrelevant_evidence
   Does the answer rely on evidence that does not actually support
   the claims being made?

4. citation_supported
   Do the cited/used chunks actually support the answer?

5. hallucination
   Does the answer contain information that is not present in the evidence?

6. failure_type

   Use "none" when the answer is fully supported.

   Use "generation_issue" when:
   - the supplied evidence contains enough information to answer the question,
   - but Generation misunderstood, misused, or invented information.

   Use "evidence_issue" when:
   - the supplied evidence does not contain enough information to answer
     the question,
   - the required information is missing,
   - or the retrieved evidence is fundamentally insufficient or wrong.

7. confidence
   Return a number from 0.0 to 1.0.

Return ONLY valid JSON:

{{
  "verified": true,
  "supported": true,
  "version_mixed": false,
  "irrelevant_evidence": false,
  "citation_supported": true,
  "hallucination": false,
  "failure_type": "none",
  "confidence": 0.95,
  "reason": "short explanation"
}}

Rules:
- verified is true ONLY when all checks pass.
- Do not use outside knowledge.
- Do not rewrite the answer.
- Distinguish an incorrect answer from insufficient evidence.
"""


def _parse_verification_response(response_text):
    raw = response_text.strip()

    if raw.startswith("```"):
        raw = raw.replace("```json", "", 1)
        raw = raw.replace("```", "", 1).strip()

    data = json.loads(raw)

    failure_type = data.get(
        "failure_type",
        "none",
    )

    if failure_type not in {
        "none",
        "generation_issue",
        "evidence_issue",
    }:
        failure_type = "generation_issue"

    return {
        "verified": bool(
            data.get("verified", False)
        ),
        "supported": bool(
            data.get("supported", False)
        ),
        "version_mixed": bool(
            data.get("version_mixed", False)
        ),
        "irrelevant_evidence": bool(
            data.get("irrelevant_evidence", False)
        ),
        "citation_supported": bool(
            data.get("citation_supported", False)
        ),
        "hallucination": bool(
            data.get("hallucination", False)
        ),
        "failure_type": failure_type,
        "confidence": data.get(
            "confidence",
            0.0,
        ),
        "reason": str(
            data.get("reason", "")
        ).strip(),
    }


def verify_answer(
    question,
    answer_text,
    chunks,
):
    """
    Verify a generated answer against the exact evidence
    used for generation.
    """

    if not answer_text:
        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": False,
            "citation_supported": False,
            "hallucination": True,
            "failure_type": "generation_issue",
            "confidence": 0.0,
            "reason": "Generated answer is empty.",
        }

    if not chunks:
        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": True,
            "citation_supported": False,
            "hallucination": True,
            "failure_type": "evidence_issue",
            "confidence": 0.0,
            "reason": "No evidence was supplied for verification.",
        }

    source_text = "\n\n".join(
        (
            f"Chunk ID: {chunk.get('chunk_id', '')}\n"
            f"Version: "
            f"{chunk.get('version') or chunk.get('release_date', '')}\n"
            f"Text: {chunk.get('text', '')}"
        )
        for chunk in chunks
    )

    prompt = VERIFY_PROMPT.format(
        question=question,
        answer=answer_text,
        source_text=source_text,
    )

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
        )
    except Exception:
        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": False,
            "citation_supported": False,
            "hallucination": False,
            "failure_type": "verification_error",
            "confidence": 0.0,
            "reason": (
                "The verification service is unavailable."
            ),
        }

    try:
        result = _parse_verification_response(
            response.text
        )
    except (
        json.JSONDecodeError,
        AttributeError,
        TypeError,
        ValueError,
    ):
        return {
            "verified": False,
            "supported": False,
            "version_mixed": False,
            "irrelevant_evidence": False,
            "citation_supported": False,
            "hallucination": False,
            "failure_type": "verification_error",
            "confidence": 0.0,
            "reason": (
                "The verification response could not be validated."
            ),
        }

    confidence = result.get(
        "confidence",
        0.0,
    )

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(
        0.0,
        min(1.0, confidence),
    )

    supported = bool(
        result.get("supported", False)
    )

    version_mixed = bool(
        result.get("version_mixed", False)
    )

    irrelevant_evidence = bool(
        result.get("irrelevant_evidence", False)
    )

    citation_supported = bool(
        result.get("citation_supported", False)
    )

    hallucination = bool(
        result.get("hallucination", False)
    )

    verified = (
        supported
        and not version_mixed
        and not irrelevant_evidence
        and citation_supported
        and not hallucination
    )

    failure_type = result.get(
        "failure_type",
        "none",
    )

    if verified:
        failure_type = "none"
    elif failure_type == "none":
        failure_type = "generation_issue"

    return {
        "verified": verified,
        "supported": supported,
        "version_mixed": version_mixed,
        "irrelevant_evidence": irrelevant_evidence,
        "citation_supported": citation_supported,
        "hallucination": hallucination,
        "failure_type": failure_type,
        "confidence": confidence,
        "reason": str(
            result.get("reason", "")
        ).strip(),
    }


def generate_verified_answer(
    query,
    graded_result,
    generation_result,
):
    """
    Final Generation → Verification step.

    Grading provides:
        - final/re-written query
        - graded chunks

    Generation provides:
        - generated answer
        - used chunk IDs
        - citations

    Verification validates the generated answer against
    only the chunks actually used by Generation.
    """

    if graded_result.get("status") != "found":
        return {
            "status": "not_found",
            "answer": None,
            "citations": [],
            "confidence": 0.0,
        }

    if generation_result.get("status") != "found":
        return {
            "status": "not_found",
            "answer": None,
            "citations": [],
            "confidence": 0.0,
        }

    graded_chunks = graded_result.get(
        "chunks",
        [],
    )

    used_chunk_ids = set(
        generation_result.get(
            "used_chunk_ids",
            [],
        )
    )

    if not used_chunk_ids:
        return {
            "status": "hallucination_flagged",
            "answer": None,
            "citations": [],
            "used_chunk_ids": [],
            "confidence": 0.0,
            "verification": {
                "verified": False,
                "failure_type": "generation_issue",
                "reason": (
                    "Generation returned no supporting chunk IDs."
                ),
            },
        }

    used_chunks = [
        chunk
        for chunk in graded_chunks
        if chunk.get("chunk_id") in used_chunk_ids
    ]

    if len(used_chunks) != len(used_chunk_ids):
        return {
            "status": "hallucination_flagged",
            "answer": None,
            "citations": [],
            "used_chunk_ids": list(
                used_chunk_ids
            ),
            "confidence": 0.0,
            "verification": {
                "verified": False,
                "failure_type": "generation_issue",
                "reason": (
                    "Generation referenced a chunk ID that was "
                    "not present in graded evidence."
                ),
            },
        }

    verdict = verify_answer(
        question=query,
        answer_text=generation_result["answer"],
        chunks=used_chunks,
    )

    if not verdict["verified"]:
        return {
            "status": (
                "verification_error"
                if verdict.get("failure_type") == "verification_error"
                else "verification_failed"
            ),
            "answer": None,
            "citations": [],
            "used_chunk_ids": generation_result.get(
                "used_chunk_ids",
                [],
            ),
            "confidence": verdict["confidence"],
            "verification": verdict,
        }

    return {
        "status": "ok",
        "answer": generation_result["answer"],
        "citations": generation_result.get(
            "citations",
            [],
        ),
        "used_chunk_ids": generation_result.get(
            "used_chunk_ids",
            [],
        ),
        "confidence": verdict["confidence"],
        "verification": verdict,
    }

