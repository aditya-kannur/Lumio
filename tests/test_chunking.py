"""
CHUNKING TEST COVERAGE
======================

This file tests all three document-specific chunking methods:

1. CHANGELOG
   Source:
       data/changelog/changelog.md
       data/changelog/historical-changelog.md
   Chunk boundary:
       <Update> blocks + ### subheaders

2. MIGRATION
   Source:
       data/migrations/*.md
   Chunk boundary:
       ## section headers
   Expected behavior:
       one chunk per migration section

3. REFERENCE / OPENAPI
   Source:
       data/reference/openapi.json
   Chunk boundary:
       one chunk per HTTP method + endpoint

The tests cover:

- Input -> output correctness
- Expected chunk count
- Chunk content
- Logical chunk boundaries
- Chunk ordering
- Content coverage
- Empty/invalid input behavior
- Required metadata fields
- Metadata correctness
- Non-empty chunks
- Chunk IDs
- Chunk ID uniqueness
- Chunk ID determinism
- Cross-file ID uniqueness
- Duplicate logical identities
- Overlap / duplicated section content

NOTE:
The current chunkers are semantic-boundary chunkers, not fixed-size
chunkers. Therefore there is no arbitrary min/max character limit
being asserted. A future size-based chunking implementation should
add explicit size and overlap thresholds.
"""

import json
from pathlib import Path

import pytest

from src.chunking.changelog_chunker import (
    chunk_changelog,
    split_by_subheader,
)
from src.chunking.migration_chunker import (
    chunk_migration_file,
    extract_version_from_filename,
)
from src.chunking.reference_chunker import (
    chunk_reference_file,
)


ROOT = Path(__file__).resolve().parents[1]

CHANGELOG_DIR = ROOT / "data" / "changelog"
MIGRATION_DIR = ROOT / "data" / "migrations"
REFERENCE_FILE = ROOT / "data" / "reference" / "openapi.json"


# ==============================================================
# Shared helpers
# ==============================================================


def assert_non_empty_chunks(chunks):
    """Every generated chunk must contain non-empty text."""
    assert chunks

    for chunk in chunks:
        assert isinstance(chunk["text"], str)
        assert chunk["text"].strip()


def assert_unique_chunk_ids(chunks):
    """Every chunk must have a unique persistent ID."""
    ids = [chunk["chunk_id"] for chunk in chunks]

    assert all(ids)
    assert len(ids) == len(set(ids))


def assert_deterministic_chunk_ids(chunker, *args):
    """Same input must produce the same chunk IDs."""
    first = chunker(*args)
    second = chunker(*args)

    first_ids = [chunk["chunk_id"] for chunk in first]
    second_ids = [chunk["chunk_id"] for chunk in second]

    assert first_ids == second_ids


# ==============================================================
# CHANGELOG CHUNKING
# ==============================================================


def test_changelog_splits_updates_and_subheaders():
    text = (
        '<Update label="2025-01-01">'
        "intro\n"
        "### One\n"
        "first\n"
        "### Two\n"
        "second"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    assert len(chunks) == 2

    assert chunks[0]["release_date"] == "2025-01-01"
    assert chunks[1]["release_date"] == "2025-01-01"

    assert chunks[0]["doc_type"] == "changelog"
    assert chunks[1]["doc_type"] == "changelog"

    assert chunks[0]["text"] == "One\n\nfirst"
    assert chunks[1]["text"] == "Two\n\nsecond"


def test_changelog_preserves_chunk_order():
    text = (
        '<Update label="2025-01-01">'
        "### First\n"
        "first content\n"
        "### Second\n"
        "second content\n"
        "### Third\n"
        "third content"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    assert [chunk["text"] for chunk in chunks] == [
        "First\n\nfirst content",
        "Second\n\nsecond content",
        "Third\n\nthird content",
    ]


def test_changelog_handles_multiple_updates():
    text = (
        '<Update label="2025-01-01">'
        "### First\n"
        "first"
        "</Update>"
        '<Update label="2025-02-01">'
        "### Second\n"
        "second"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    assert len(chunks) == 2

    assert chunks[0]["release_date"] == "2025-01-01"
    assert chunks[1]["release_date"] == "2025-02-01"


def test_changelog_without_subheaders_is_one_chunk():
    assert split_by_subheader("whole body") == [
        (None, "whole body")
    ]


def test_changelog_skips_empty_sections():
    text = (
        '<Update label="2025-01-01">'
        "### Empty\n"
        "\n"
        "### Real\n"
        "real content"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    assert len(chunks) == 1
    assert chunks[0]["text"] == "Real\n\nreal content"


def test_changelog_empty_input_returns_no_chunks():
    assert chunk_changelog("") == []


def test_changelog_chunks_are_non_empty():
    text = (
        '<Update label="2025-01-01">'
        "### One\n"
        "first\n"
        "### Two\n"
        "second"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    assert_non_empty_chunks(chunks)


def test_changelog_required_fields():
    text = (
        '<Update label="2025-01-01">'
        "### One\n"
        "first"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    required_fields = {
        "text",
        "doc_type",
        "release_date",
        "chunk_id",
    }

    for chunk in chunks:
        assert required_fields <= chunk.keys()


def test_changelog_chunk_ids_are_unique():
    text = (
        '<Update label="2025-01-01">'
        "### One\n"
        "first\n"
        "### Two\n"
        "second"
        "</Update>"
        '<Update label="2025-02-01">'
        "### One\n"
        "third"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    assert_unique_chunk_ids(chunks)


def test_changelog_chunk_ids_are_deterministic():
    text = (
        '<Update label="2025-01-01">'
        "### One\n"
        "first\n"
        "### Two\n"
        "second"
        "</Update>"
    )

    assert_deterministic_chunk_ids(
        chunk_changelog,
        text,
    )


def test_changelog_sections_do_not_duplicate_content():
    text = (
        '<Update label="2025-01-01">'
        "### First\n"
        "unique first content\n"
        "### Second\n"
        "unique second content\n"
        "### Third\n"
        "unique third content"
        "</Update>"
    )

    chunks = chunk_changelog(text)

    texts = [chunk["text"] for chunk in chunks]

    assert len(texts) == len(set(texts))

    assert "unique first content" in texts[0]
    assert "unique second content" in texts[1]
    assert "unique third content" in texts[2]

    assert "unique first content" not in texts[1]
    assert "unique first content" not in texts[2]

    assert "unique second content" not in texts[0]
    assert "unique second content" not in texts[2]


def test_real_changelog_file_creates_chunks():
    path = CHANGELOG_DIR / "changelog.md"

    assert path.exists()

    text = path.read_text(encoding="utf-8")
    chunks = chunk_changelog(text)

    assert_non_empty_chunks(chunks)

    assert all(
        chunk["doc_type"] == "changelog"
        for chunk in chunks
    )


def test_real_historical_changelog_file_creates_chunks():
    path = CHANGELOG_DIR / "historical-changelog.md"

    assert path.exists()

    text = path.read_text(encoding="utf-8")
    chunks = chunk_changelog(text)

    assert_non_empty_chunks(chunks)

    assert all(
        chunk["doc_type"] == "changelog"
        for chunk in chunks
    )


# ==============================================================
# MIGRATION CHUNKING
# ==============================================================


def test_migration_version_comes_from_filename():
    assert extract_version_from_filename(
        "2022-06-28.md"
    ) == "2022-06-28"


def test_migration_chunking_is_one_chunk_per_section():
    path = MIGRATION_DIR / "2022-06-28.md"

    chunks = chunk_migration_file(str(path))

    assert chunks

    assert all(
        chunk["doc_type"] == "migration"
        for chunk in chunks
    )

    assert all(
        chunk["version"] == "2022-06-28"
        for chunk in chunks
    )

    assert all(
        chunk["breaking"] is True
        for chunk in chunks
    )

    assert all(
        chunk["section"]
        for chunk in chunks
    )


def test_migration_preserves_section_order():
    path = MIGRATION_DIR / "2022-06-28.md"

    chunks = chunk_migration_file(str(path))

    sections = [
        chunk["section"]
        for chunk in chunks
    ]

    assert sections == list(dict.fromkeys(sections))


def test_migration_chunks_are_non_empty():
    path = MIGRATION_DIR / "2022-06-28.md"

    chunks = chunk_migration_file(str(path))

    assert_non_empty_chunks(chunks)


def test_migration_required_fields():
    path = MIGRATION_DIR / "2022-06-28.md"

    chunks = chunk_migration_file(str(path))

    required_fields = {
        "doc_type",
        "version",
        "section",
        "breaking",
        "text",
        "chunk_id",
    }

    for chunk in chunks:
        assert required_fields <= chunk.keys()


def test_migration_chunk_ids_are_unique():
    path = MIGRATION_DIR / "2022-06-28.md"

    chunks = chunk_migration_file(str(path))

    assert_unique_chunk_ids(chunks)


def test_migration_chunk_ids_are_deterministic():
    path = MIGRATION_DIR / "2022-06-28.md"

    assert_deterministic_chunk_ids(
        chunk_migration_file,
        str(path),
    )


def test_migration_sections_do_not_duplicate_content():
    path = MIGRATION_DIR / "2022-06-28.md"

    chunks = chunk_migration_file(str(path))

    texts = [
        chunk["text"].strip()
        for chunk in chunks
    ]

    assert len(texts) == len(set(texts))


def test_all_migration_files_create_chunks():
    paths = sorted(MIGRATION_DIR.glob("*.md"))

    assert paths

    for path in paths:
        chunks = chunk_migration_file(str(path))

        assert_non_empty_chunks(chunks)

        expected_version = (
            extract_version_from_filename(path.name)
        )

        assert all(
            chunk["version"] == expected_version
            for chunk in chunks
        )


def test_migration_chunk_ids_are_unique_across_all_files():
    paths = sorted(MIGRATION_DIR.glob("*.md"))

    all_chunks = []

    for path in paths:
        all_chunks.extend(
            chunk_migration_file(str(path))
        )

    all_ids = [
        chunk["chunk_id"]
        for chunk in all_chunks
    ]

    assert len(all_ids) == len(set(all_ids))


def test_migration_logical_identities_are_unique_across_all_files():
    paths = sorted(MIGRATION_DIR.glob("*.md"))

    all_chunks = []

    for path in paths:
        all_chunks.extend(
            chunk_migration_file(str(path))
        )

    identities = [
        (
            chunk["version"],
            chunk["section"],
        )
        for chunk in all_chunks
    ]

    assert len(identities) == len(set(identities))


# ==============================================================
# REFERENCE / OPENAPI CHUNKING
# ==============================================================


def test_reference_chunking_is_one_chunk_per_http_operation():
    spec = json.loads(
        REFERENCE_FILE.read_text(
            encoding="utf-8"
        )
    )

    expected = sum(
        1
        for methods in spec.get("paths", {}).values()
        for method in methods
        if method in {
            "get",
            "post",
            "patch",
            "delete",
            "put",
        }
    )

    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    assert len(chunks) == expected


def test_reference_chunks_are_non_empty():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    assert_non_empty_chunks(chunks)


def test_reference_required_fields():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

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

    for chunk in chunks:
        assert required_fields <= chunk.keys()


def test_reference_metadata_is_correct():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    for chunk in chunks:
        assert chunk["doc_type"] == "reference"
        assert chunk["version"] == "2025-09-03"
        assert chunk["endpoint"]
        assert chunk["method"] in {
            "get",
            "post",
            "patch",
            "delete",
            "put",
        }


def test_reference_chunk_ids_are_unique():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    assert_unique_chunk_ids(chunks)


def test_reference_chunk_ids_are_deterministic():
    assert_deterministic_chunk_ids(
        chunk_reference_file,
        str(REFERENCE_FILE),
    )


def test_reference_endpoint_method_identities_are_unique():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    identities = [
        (
            chunk["version"],
            chunk["method"],
            chunk["endpoint"],
        )
        for chunk in chunks
    ]

    assert len(identities) == len(set(identities))


def test_reference_chunk_contains_endpoint_and_method():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    for chunk in chunks:
        expected_prefix = (
            f"{chunk['method'].upper()} "
            f"{chunk['endpoint']}"
        )

        assert chunk["text"].startswith(
            expected_prefix
        )


def test_reference_chunks_do_not_duplicate_endpoint_identity():
    chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    identities = [
        (
            chunk["method"],
            chunk["endpoint"],
        )
        for chunk in chunks
    ]

    assert len(identities) == len(set(identities))


# ==============================================================
# EDGE / ROBUSTNESS TESTS
# ==============================================================


def test_changelog_empty_input():
    assert chunk_changelog("") == []


def test_changelog_without_update_block():
    text = "ordinary text without an Update block"

    assert chunk_changelog(text) == []


def test_migration_empty_file_returns_no_chunks(tmp_path):
    path = tmp_path / "2026-01-01.md"
    path.write_text("", encoding="utf-8")

    assert chunk_migration_file(str(path)) == []


def test_migration_intro_without_sections_returns_no_chunks(
    tmp_path,
):
    path = tmp_path / "2026-01-01.md"

    path.write_text(
        "intro text only",
        encoding="utf-8",
    )

    assert chunk_migration_file(str(path)) == []


def test_reference_empty_paths_returns_no_chunks(tmp_path):
    path = tmp_path / "openapi.json"

    path.write_text(
        json.dumps({"paths": {}}),
        encoding="utf-8",
    )

    assert chunk_reference_file(str(path)) == []


def test_reference_ignores_non_http_path_keys(tmp_path):
    path = tmp_path / "openapi.json"

    spec = {
        "paths": {
            "/example": {
                "parameters": [
                    {
                        "name": "id"
                    }
                ],
                "get": {
                    "summary": "Get example"
                },
            }
        }
    }

    path.write_text(
        json.dumps(spec),
        encoding="utf-8",
    )

    chunks = chunk_reference_file(str(path))

    assert len(chunks) == 1
    assert chunks[0]["method"] == "get"
    assert chunks[0]["endpoint"] == "/example"


# ==============================================================
# CROSS-DOCUMENT ID SAFETY
# ==============================================================


def test_chunk_ids_are_unique_across_document_types():
    changelog_text = (
        '<Update label="2025-01-01">'
        "### Example\n"
        "Example changelog content"
        "</Update>"
    )

    changelog_chunks = chunk_changelog(
        changelog_text
    )

    migration_path = MIGRATION_DIR / "2022-06-28.md"
    migration_chunks = chunk_migration_file(
        str(migration_path)
    )

    reference_chunks = chunk_reference_file(
        str(REFERENCE_FILE)
    )

    all_chunks = (
        changelog_chunks
        + migration_chunks
        + reference_chunks
    )

    all_ids = [
        chunk["chunk_id"]
        for chunk in all_chunks
    ]

    assert len(all_ids) == len(set(all_ids))