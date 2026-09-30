# src/chunking/reference_chunker.py
"""
Splits openapi.json into one chunk per endpoint (path + method pair).
Structure confirmed from the actual file: top-level "paths" object,
each key is a path, each path has one or more HTTP method keys.
"""
import json
from src.chunking.chunk_id import make_chunk_id


def chunk_reference_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        spec = json.load(f)

    chunks = []
    paths = spec.get("paths", {})

    for path, methods in paths.items():
        for method, operation in methods.items():
            # skip non-HTTP-method keys if any ever show up (defensive)
            if method not in ("get", "post", "patch", "delete", "put"):
                continue

            summary = operation.get("summary", "")
            tags = operation.get("tags", [])

            # Build a readable text block from the operation's own fields —
            # this is what gets embedded, so it needs to read like a sentence,
            # not raw JSON.
            text_parts = [f"{method.upper()} {path} — {summary}."]
            if "parameters" in operation:
                param_names = [p.get("name", "") for p in operation["parameters"] if "name" in p]
                if param_names:
                    text_parts.append(f"Parameters: {', '.join(param_names)}.")
            if "requestBody" in operation:
                text_parts.append("Accepts a request body.")

            chunk = {
                "doc_type": "reference",
                "endpoint": path,
                "method": method,
                "tags": ", ".join(tags) if tags else "",
                "summary": summary,
                "version": "2025-09-03",
                "text": " ".join(text_parts),
            }

            chunk["chunk_id"] = make_chunk_id(
                "reference",
                "2025-09-03",
                method,
                path,
            )

            chunks.append(chunk)

    return chunks

if __name__ == "__main__":
    from pathlib import Path

    reference_path = Path(
        "data/reference/openapi.json"
    )

    if not reference_path.exists():
        raise FileNotFoundError(
            f"Reference file not found: "
            f"{reference_path}"
        )

    chunks = chunk_reference_file(
        str(reference_path)
    )

    print("\n=== REFERENCE CHUNKER TEST ===")
    print(f"File: {reference_path}")
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "FAIL: No reference chunks created."
        )

    print("PASS: Chunks created.")

    # --------------------------------------------------------------
    # Validate every chunk
    # --------------------------------------------------------------

    required_fields = {
        "doc_type",
        "endpoint",
        "method",
        "tags",
        "summary",
        "version",
        "text",
        "chunk_id",
    }

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        missing = (
            required_fields - chunk.keys()
        )

        if missing:
            raise RuntimeError(
                f"FAIL: Chunk {index} "
                f"missing fields: {missing}"
            )

        if not chunk["chunk_id"]:
            raise RuntimeError(
                f"FAIL: Chunk {index} "
                "has empty chunk_id."
            )

    print(
        "PASS: Every chunk contains "
        "all required fields."
    )

    # --------------------------------------------------------------
    # Validate chunk IDs are unique
    # --------------------------------------------------------------

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise RuntimeError(
            "FAIL: Duplicate chunk_ids detected."
        )

    print(
        "PASS: All chunk_ids are unique."
    )

    # --------------------------------------------------------------
    # Validate endpoint/method identity
    # --------------------------------------------------------------

    identities = [
        (
            chunk["version"],
            chunk["method"],
            chunk["endpoint"],
        )
        for chunk in chunks
    ]

    if len(identities) != len(set(identities)):
        raise RuntimeError(
            "FAIL: Duplicate "
            "version/method/endpoint combinations detected."
        )

    print(
        "PASS: Endpoint identities are unique."
    )

    # --------------------------------------------------------------
    # Show first 10 chunks
    # --------------------------------------------------------------

    print("\n=== SAMPLE CHUNKS ===")

    for index, chunk in enumerate(
        chunks[:10],
        start=1,
    ):
        print(f"\n--- Chunk {index} ---")
        print(
            f"chunk_id: {chunk['chunk_id']}"
        )
        print(
            f"endpoint: {chunk['endpoint']}"
        )
        print(
            f"method:   {chunk['method']}"
        )
        print(
            f"version:  {chunk['version']}"
        )
        print(
            f"summary:  {chunk['summary']}"
        )
        print(
            f"text:     {chunk['text']}"
        )

    # --------------------------------------------------------------
    # Deterministic ID test
    # --------------------------------------------------------------

    chunks_again = chunk_reference_file(
        str(reference_path)
    )

    ids_again = [
        chunk["chunk_id"]
        for chunk in chunks_again
    ]

    if chunk_ids != ids_again:
        raise RuntimeError(
            "FAIL: chunk_ids changed when the "
            "same reference file was processed twice."
        )

    print(
        "\nPASS: chunk_ids are deterministic."
    )

    print(
        "\nALL REFERENCE CHUNKER TESTS PASSED."
    )