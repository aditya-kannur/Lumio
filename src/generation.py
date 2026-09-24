import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-3.5-flash-lite"

CITATION_TEMPLATE = "[Source: {doc_type} | {identifier} | version {version}]"

GEN_PROMPT = """Answer the developer's question using ONLY the information in the
provided document chunks. Do not use any outside knowledge. If the chunks don't
fully answer the question, say so honestly.

Question: "{question}"

Chunks:
{chunks_text}

Write a clear, direct answer grounded strictly in the chunks above."""


def format_chunk_for_prompt(chunk):
    meta = {k: v for k, v in chunk.items() if k != "text"}
    return f"---\nMetadata: {meta}\nText: {chunk['text']}\n---"


def build_citation(chunk):
    doc_type = chunk.get("doc_type", "unknown")
    version = chunk.get("version") or chunk.get("release_date", "unknown")
    identifier = chunk.get("endpoint") or chunk.get("section") or chunk.get("summary", "")[:50]
    return CITATION_TEMPLATE.format(doc_type=doc_type, identifier=identifier, version=version)


def generate_answer(question, chunks):
    chunks_text = "\n".join(format_chunk_for_prompt(c) for c in chunks)
    prompt = GEN_PROMPT.format(question=question, chunks_text=chunks_text)
    response = client.models.generate_content(model=MODEL, contents=prompt)
    answer_text = response.text.strip()
    citations = [build_citation(c) for c in chunks]
    return {"answer": answer_text, "citations": citations}


if __name__ == "__main__":
    test_chunks = [
        {
            "doc_type": "reference",
            "endpoint": "/v1/pages",
            "method": "get",
            "summary": "Retrieve a page",
            "version": "2025-09-03",
            "text": "GET /v1/pages — Retrieve a page. Parameters: page_id.",
        }
    ]

    question = "How do I retrieve a page?"

    result = generate_answer(question, test_chunks)

    print("=== Generated Answer ===")
    print(result["answer"])

    print("\n=== Citations ===")
    for citation in result["citations"]:
        print(citation)

    print("\n=== Test Result ===")
    if result["answer"] and result["citations"]:
        print("PASS: generation produced an answer and citation.")
    else:
        print("FAIL: generation did not produce the expected output.")