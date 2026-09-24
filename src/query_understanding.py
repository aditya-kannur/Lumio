"""
Query understanding — classifies intent (reference/diagnostic/migration)
and extracts version(s) from the developer's question, using Gemini.
"""

import os
import json

from google import genai
from google.genai import types
from dotenv import load_dotenv

from src.prompts.system_prompt import SYSTEM_PROMPT
from src.constants import KNOWN_VERSIONS

load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-3.5-flash-lite"

def understand_query(user_question: str) -> dict:
    """
    Returns a dict like:
      {"intent": "reference", "version": "2022-06-28"}
      {"intent": "migration", "from_version": "2021-08-16", "to_version": "2022-06-28"}
      {"intent": "reference", "version": None}
    """

    prompt = f"""
{SYSTEM_PROMPT}

Known versions: {", ".join(KNOWN_VERSIONS)}

Developer question: "{user_question}"
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        ),
    )

    raw_text = response.text.strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        raise ValueError(
            f"Could not parse model output as JSON: {raw_text}"
        )