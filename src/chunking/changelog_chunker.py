import re
from src.chunking.chunk_id import make_chunk_id

# Matches <Update label="...">...</Update> blocks, across multiple lines.
# re.DOTALL: lets '.' match newlines too (body spans multiple lines).
# .*? (non-greedy): stops at the FIRST </Update>, not the last one in the file.
UPDATE_PATTERN = re.compile(
    r'<Update label="([^"]+)">(.*?)</Update>',
    re.DOTALL
)

# Matches a '###' header line. Same shape as Day 2's '##' pattern,
# but one level deeper. ^\s* allows leading whitespace before the header.
SUBHEADER_SPLIT_PATTERN = re.compile(r'^###\s+(.+)$', re.MULTILINE)


def split_by_subheader(body: str):
    """
    Day 2's '##' splitter, reused at the '###' level.
    Returns a list of (section_title, section_text) tuples.
    If there are no '###' headers, returns [(None, whole_body)].
    """
    parts = SUBHEADER_SPLIT_PATTERN.split(body)

    if len(parts) == 1:
        # No '###' headers found — split() returns the original string
        # untouched in a list of length 1. Whole block is one chunk.
        return [(None, body.strip())]

    # parts = [intro(discard), title1, text1, title2, text2, ...]
    # Same alternating shape as Day 2 — loop in pairs, starting after index 0.
    sections = []
    for i in range(1, len(parts), 2):
        title = parts[i]
        text = parts[i + 1].strip()
        sections.append((title, text))
    return sections


def chunk_changelog(text: str, doc_type: str = "changelog"):
    """
    Shared chunker for changelog.md and historical-changelog.md.
    doc_type is passed in by the caller so both files can reuse this
    function but still tag their chunks correctly if you ever need to
    tell them apart later.
    """
    chunks = []

    for match in UPDATE_PATTERN.finditer(text):
        release_date = match.group(1)   # the label attribute
        body = match.group(2)           # everything between the tags

        for section_title, section_text in split_by_subheader(body):
            if not section_text:
                continue  # skip empty sections defensively

            chunk_text = section_text
            if section_title:
                # keep the ### title attached to its own chunk's text
                chunk_text = f"{section_title}\n\n{section_text}"

            # Flat dict — no nested "metadata" key. retrieval_pipeline.py
            # and Chroma both expect every field (including text) at the
            # top level so filtering and embedding work without extra unwrapping.
            chunk = {
                "text": chunk_text,
                "doc_type": doc_type,
                "release_date": release_date,
            }

            chunk["chunk_id"] = make_chunk_id(
                doc_type,
                release_date,
                section_title or "default",
            )

            chunks.append(chunk)

    return chunks



if __name__ == "__main__":
    from pathlib import Path

    changelog_path = Path("data/changelog/changelog.md")

    if not changelog_path.exists():
        raise FileNotFoundError(
            f"Changelog file not found: {changelog_path}"
        )

    text = changelog_path.read_text(
        encoding="utf-8"
    )

    chunks = chunk_changelog(text)

    print("\n=== CHANGELOG CHUNKER TEST ===")
    print(f"File: {changelog_path}")
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError(
            "FAIL: No chunks were created."
        )

    print("PASS: Chunks created.")

    # --------------------------------------------------------------
    # Validate every chunk
    # --------------------------------------------------------------

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        required_fields = {
            "text",
            "doc_type",
            "release_date",
            "chunk_id",
        }

        missing = required_fields - chunk.keys()

        if missing:
            raise RuntimeError(
                f"FAIL: Chunk {index} missing fields: {missing}"
            )

        if not chunk["chunk_id"]:
            raise RuntimeError(
                f"FAIL: Chunk {index} has empty chunk_id."
            )

    print(
        "PASS: Every chunk contains "
        "text, doc_type, release_date, and chunk_id."
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

    print("PASS: All chunk_ids are unique.")

    # --------------------------------------------------------------
    # Show first 10 chunks
    # --------------------------------------------------------------

    print("\n=== SAMPLE CHUNKS ===")

    for index, chunk in enumerate(
        chunks[:10],
        start=1,
    ):
        print(f"\n--- Chunk {index} ---")
        print(f"chunk_id:     {chunk['chunk_id']}")
        print(f"release_date: {chunk['release_date']}")
        print(f"doc_type:     {chunk['doc_type']}")
        print(f"text length:  {len(chunk['text'])}")
        print("text:")
        print(chunk["text"])

    # --------------------------------------------------------------
    # Verify deterministic IDs
    # --------------------------------------------------------------

    chunks_again = chunk_changelog(text)

    ids_again = [
        chunk["chunk_id"]
        for chunk in chunks_again
    ]

    if chunk_ids != ids_again:
        raise RuntimeError(
            "FAIL: chunk_ids changed when the same "
            "input was processed again."
        )

    print(
        "\nPASS: chunk_ids are deterministic."
    )

    print(
        "\nALL CHANGELOG CHUNKER TESTS PASSED."
    )