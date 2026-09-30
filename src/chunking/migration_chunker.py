# src/chunking/migration_chunker.py
"""
Splits a migration/version markdown file into one chunk per discrete
change, using ## headers as the boundary — confirmed structure: each
version doc has multiple ## sections, one per breaking change.
"""
import re
import os
from src.chunking.chunk_id import make_chunk_id

def extract_version_from_filename(filename):
    return os.path.splitext(filename)[0] 

def chunk_migration_file(filepath):
    version = extract_version_from_filename(os.path.basename(filepath))
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    parts = re.split(r"(?m)^##\s+(.+)$", text)
    # parts[0] = intro text before first ## (discard)
    # after that: [header, body, header, body, ...]

    chunks = []
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        if not body:
            continue
        chunk = {
            "doc_type": "migration",
            "version": version,
            "section": header,
            "breaking": True,
            "text": body,
        }

        chunk["chunk_id"] = make_chunk_id(
            "migration",
            version,
            header,
        )

        chunks.append(chunk)
    return chunks

