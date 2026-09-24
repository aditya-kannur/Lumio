import json
import os

from dotenv import load_dotenv
from google import genai

from src.constants import KNOWN_VERSIONS
from src.prompts.system_prompt import SYSTEM_PROMPT

load_dotenv()

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

IMPORTANT VERSION RULES:

1. If the user explicitly mentions a version string such as
   "2030-01-01", ALWAYS return that exact version string.
   Do NOT replace it with null just because it is not in Known versions.

2. Known versions are only the versions available in our dataset.
   An explicitly mentioned version that is not in Known versions
   must still be returned so the router can classify it as unknown.

3. For reference or diagnostic questions:
   return the explicitly mentioned version in the "version" field.

4. For migration questions:
   return explicitly mentioned versions in "from_version"
   and "to_version", even if either version is unknown.

5. Only return null when the user genuinely did not provide
   that version.

6. If the current question is a follow-up containing only a version,
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



if __name__ == "__main__":
    print("=== Query Understanding Test ===")

    question = "How do I configure webhook retry backoff in Notion-Version 2021-05-13?"


    print(f"\nQuestion:\n{question}\n")

    result = understand_query(question)

    print("=== Gemini Output ===")
    print(json.dumps(result, indent=2))

    print("\n=== Validation ===")

    if not isinstance(result, dict):
        raise RuntimeError("FAIL: Gemini did not return a JSON object.")

    print("PASS: Response is a JSON object.")

    required_fields = [
        "intent",
        "version",
    ]

    for field in required_fields:
        if field in result:
            print(f"PASS: '{field}' = {result[field]}")
        else:
            print(f"WARNING: '{field}' is missing.")

    if result.get("version") in KNOWN_VERSIONS:
        print("PASS: Version is a known version.")
    elif result.get("version") in (None, ""):
        print("PASS: No version specified.")
    else:
        print(f"WARNING: Unknown version returned: {result.get('version')}")