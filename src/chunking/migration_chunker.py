# src/chunking/migration_chunker.py
"""
Splits a migration/version markdown file into one chunk per discrete
change, using ## headers as the boundary — confirmed structure: each
version doc has multiple ## sections, one per breaking change.
"""
import re
import os

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
        chunks.append({
            "doc_type": "migration",
            "version": version,
            "section": header,
            "breaking": True,
            "text": body,
        })
    return chunks

if __name__ == "__main__":
    import json
    data_dir = "data/migrations"
    all_chunks = []
    for filename in sorted(os.listdir(data_dir)):
        if filename.endswith(".md"):
            all_chunks.extend(chunk_migration_file(os.path.join(data_dir, filename)))
    print(f"Produced {len(all_chunks)} chunks from {len(os.listdir(data_dir))} files")
    with open("data/chunks_migration.json", "w") as f:
        json.dump(all_chunks, f, indent=2)