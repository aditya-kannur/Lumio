from pathlib import Path

from src.constants import KNOWN_VERSIONS, REFERENCE_AVAILABLE_VERSIONS, DOC_TYPE_REFERENCE, DOC_TYPE_CHANGELOG, DOC_TYPE_MIGRATION
from src.data_sources import DATA_SOURCES

def test_known_versions_are_ordered_and_reference_versions_are_known():
    assert KNOWN_VERSIONS == sorted(KNOWN_VERSIONS)
    assert set(REFERENCE_AVAILABLE_VERSIONS) <= set(KNOWN_VERSIONS)

def test_dataset_manifest_contains_reference_changelogs_and_every_migration():
    paths = {x["path"] for x in DATA_SOURCES}
    assert "data/reference/openapi.json" in paths
    assert "data/changelog/changelog.md" in paths
    assert "data/changelog/historical-changelog.md" in paths
    for version in KNOWN_VERSIONS:
        assert f"data/migrations/{version}.md" in paths

def test_all_manifest_files_exist():
    root = Path(__file__).resolve().parents[1]
    for source in DATA_SOURCES:
        assert (root / source["path"]).exists(), source["path"]

def test_doc_type_constants_are_distinct():
    assert len({DOC_TYPE_REFERENCE, DOC_TYPE_CHANGELOG, DOC_TYPE_MIGRATION}) == 3
