import json
import os

from google import genai

from src.constants import KNOWN_VERSIONS
from src.prompts.system_prompt import SYSTEM_PROMPT


client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

MODEL = "gemini-3.5-flash-lite"


def understand_query(question: str, history=None):
    """
    Understand the current question using previous conversation context.

    history is expected to be a list like:
    [
        {
            "question": "...",
            "response": {...}
        }
    ]
    """

    history = history or []

    history_text = ""

    if history:
        history_text = "\n\nPrevious conversation:\n"

        for item in history[-5:]:
            previous_question = item.get("question", "")
            previous_response = item.get("response", {})

            history_text += (
                f"User: {previous_question}\n"
                f"Assistant: {json.dumps(previous_response)}\n"
            )

        history_text += (
            "\nUse this previous conversation only to resolve "
            "references, missing versions, or follow-up questions. "
            "The current question takes priority.\n"
        )

    prompt = f"""
{SYSTEM_PROMPT}

Known versions:
{json.dumps(KNOWN_VERSIONS)}

{history_text}

Current user question:
{question}

Interpret the current question in the context of the previous conversation.

If the current question is a follow-up containing only a version,
such as "2022-06-28", use the previous conversation to determine
what the user is asking about.

Return JSON only.
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
        },
    )

    try:
        result = json.loads(response.text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            f"Invalid JSON returned by query understanding: {response.text}"
        ) from exc

    return result