import os
import json
from google import genai
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

VERIFY_PROMPT = """Check if the ANSWER below is fully supported by the SOURCE text,
and check that it doesn't mix in information from a different API version.

SOURCE:
{source_text}

ANSWER:
{answer}

Respond with ONLY JSON: {{"supported": bool, "version_mixed": bool}}"""


def verify_answer(answer_text, chunks):
    source_text = "\n".join(c["text"] for c in chunks)
    prompt = VERIFY_PROMPT.format(source_text=source_text, answer=answer_text)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    raw = response.text.strip().strip("`").removeprefix("json").strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {"supported": False, "version_mixed": True}
    return result


def generate_verified_answer(question, chunks, generate_fn):
    result = generate_fn(question, chunks)
    verdict = verify_answer(result["answer"], chunks)
    if not verdict.get("supported") or verdict.get("version_mixed"):
        return {"status": "hallucination_flagged", "answer": None}
    return {"status": "ok", "answer": result["answer"], "citations": result["citations"]}
