# src/chunking/reference_chunker.py
"""
Splits openapi.json into one chunk per endpoint (path + method pair).
Structure confirmed from the actual file: top-level "paths" object,
each key is a path, each path has one or more HTTP method keys.
"""
import json

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

            chunks.append({
                "doc_type": "reference",
                "endpoint": path,
                "method": method,
                # Chroma metadata values must be scalars — join list to string.
                "tags": ", ".join(tags) if tags else "",
                "summary": summary,
                # Reference chunks don't have a version date of their own;
                # leave it as an empty string so version-filter logic can
                # still compare without crashing on a missing key.
                "version": "",
                "text": " ".join(text_parts),
            })

    return chunks

if __name__ == "__main__":
    chunks = chunk_reference_file("data/reference/openapi.json")
    print(f"Produced {len(chunks)} chunks from openapi.json")
    with open("data/chunks_reference.json", "w") as f:
        json.dump(chunks, f, indent=2)