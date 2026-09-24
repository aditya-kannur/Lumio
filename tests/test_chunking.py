import json
from pathlib import Path

from src.chunking.changelog_chunker import chunk_changelog, split_by_subheader
from src.chunking.migration_chunker import chunk_migration_file, extract_version_from_filename
from src.chunking.reference_chunker import chunk_reference_file

ROOT = Path(__file__).resolve().parents[1]

def test_changelog_splits_updates_and_subheaders():
    text = '<Update label="2025-01-01">intro\n### One\nfirst\n### Two\nsecond</Update>'
    chunks = chunk_changelog(text)
    assert len(chunks) == 2
    assert chunks[0]["release_date"] == "2025-01-01"
    assert chunks[0]["doc_type"] == "changelog"
    assert "One" in chunks[0]["text"]
    assert "first" in chunks[0]["text"]

def test_changelog_without_subheaders_is_one_chunk():
    assert split_by_subheader("whole body") == [(None, "whole body")]

def test_migration_chunking_is_one_chunk_per_section():
    path = ROOT / "data" / "migrations" / "2022-06-28.md"
    chunks = chunk_migration_file(str(path))
    assert chunks
    assert all(c["doc_type"] == "migration" for c in chunks)
    assert all(c["version"] == "2022-06-28" for c in chunks)
    assert all(c["breaking"] is True for c in chunks)
    assert all(c["section"] for c in chunks)

def test_migration_version_comes_from_filename():
    assert extract_version_from_filename("2022-06-28.md") == "2022-06-28"

def test_reference_chunking_is_one_chunk_per_http_operation():
    path = ROOT / "data" / "reference" / "openapi.json"
    spec = json.loads(path.read_text(encoding="utf-8"))
    expected = sum(1 for methods in spec.get("paths", {}).values() for method in methods if method in {"get","post","patch","delete","put"})
    chunks = chunk_reference_file(str(path))
    assert len(chunks) == expected
    assert all(c["doc_type"] == "reference" for c in chunks)
    assert all(c["endpoint"] and c["method"] for c in chunks)
