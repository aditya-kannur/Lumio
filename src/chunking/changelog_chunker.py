import re

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
            chunks.append({
                "text": chunk_text,
                "doc_type": doc_type,
                "release_date": release_date,
            })

    return chunks



# if __name__ == "__main__":
#     from pathlib import Path

#     changelog_path = Path("data/changelog/changelog.md")

#     text = changelog_path.read_text(encoding="utf-8")
#     chunks = chunk_changelog(text)

#     print(f"File: {changelog_path}")
#     print(f"Total chunks: {len(chunks)}")
#     print()

#     for i, chunk in enumerate(chunks[:10], start=1):
#         print(f"--- Chunk {i} ---")
#         print(f"release_date: {chunk['release_date']}")
#         print(f"doc_type:     {chunk['doc_type']}")
#         print(f"text length:  {len(chunk['text'])}")
#         print("text:")
#         print(chunk["text"])
#         print()