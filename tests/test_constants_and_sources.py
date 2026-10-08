"""
DATA SOURCE / DATASET MANIFEST TEST COVERAGE
=============================================

This file tests the dataset configuration and manifest layer.

It verifies:

1. VERSION CONFIGURATION
   - KNOWN_VERSIONS is ordered
   - Reference versions are known versions
   - Known versions have migration entries

2. DATASET MANIFEST
   - Reference data is registered
   - Changelog data is registered
   - Historical changelog data is registered
   - Every known migration is registered
   - Manifest paths actually exist
   - Manifest paths are unique
   - Manifest entries have required metadata

3. DOCUMENT TYPES
   - Reference, changelog and migration constants are distinct
   - Document type constants are non-empty
"""

from pathlib import Path

from src.constants import (
    KNOWN_VERSIONS,
    REFERENCE_AVAILABLE_VERSIONS,
    DOC_TYPE_REFERENCE,
    DOC_TYPE_CHANGELOG,
    DOC_TYPE_MIGRATION,
)
from src.data_sources import DATA_SOURCES


ROOT = Path(__file__).resolve().parents[1]


# ==============================================================
# VERSION CONFIGURATION
# ==============================================================


def test_known_versions_are_ordered():
    assert KNOWN_VERSIONS == sorted(KNOWN_VERSIONS)


def test_known_versions_are_unique():
    assert len(KNOWN_VERSIONS) == len(set(KNOWN_VERSIONS))


def test_reference_versions_are_known():
    assert set(REFERENCE_AVAILABLE_VERSIONS) <= set(
        KNOWN_VERSIONS
    )


def test_reference_versions_are_unique():
    assert len(REFERENCE_AVAILABLE_VERSIONS) == len(
        set(REFERENCE_AVAILABLE_VERSIONS)
    )


# ==============================================================
# DATASET MANIFEST
# ==============================================================


def test_dataset_manifest_contains_required_sources():
    paths = {
        source["path"]
        for source in DATA_SOURCES
    }

    assert "data/reference/openapi.json" in paths
    assert "data/changelog/changelog.md" in paths
    assert "data/changelog/historical-changelog.md" in paths


def test_dataset_manifest_contains_every_migration():
    paths = {
        source["path"]
        for source in DATA_SOURCES
    }

    for version in KNOWN_VERSIONS:
        assert (
            f"data/migrations/{version}.md"
            in paths
        )


def test_all_manifest_paths_are_unique():
    paths = [
        source["path"]
        for source in DATA_SOURCES
    ]

    assert len(paths) == len(set(paths))


def test_all_manifest_files_exist():
    for source in DATA_SOURCES:
        path = ROOT / source["path"]

        assert path.exists(), source["path"]
        assert path.is_file(), source["path"]


def test_manifest_entries_have_required_fields():
    required_fields = {
        "path",
        "doc_type",
    }

    for source in DATA_SOURCES:
        assert required_fields <= source.keys()


def test_manifest_paths_are_non_empty():
    for source in DATA_SOURCES:
        assert isinstance(source["path"], str)
        assert source["path"].strip()


# ==============================================================
# DOCUMENT TYPE CONFIGURATION
# ==============================================================


def test_doc_type_constants_are_distinct():
    doc_types = {
        DOC_TYPE_REFERENCE,
        DOC_TYPE_CHANGELOG,
        DOC_TYPE_MIGRATION,
    }

    assert len(doc_types) == 3


def test_doc_type_constants_are_non_empty():
    assert DOC_TYPE_REFERENCE
    assert DOC_TYPE_CHANGELOG
    assert DOC_TYPE_MIGRATION


def test_manifest_uses_known_doc_types():
    valid_doc_types = {
        DOC_TYPE_REFERENCE,
        DOC_TYPE_CHANGELOG,
        DOC_TYPE_MIGRATION,
    }

    for source in DATA_SOURCES:
        assert source["doc_type"] in valid_doc_types


# ==============================================================
# MANIFEST / VERSION CONSISTENCY
# ==============================================================


def test_all_migration_manifest_entries_match_known_versions():
    migration_paths = {
        source["path"]
        for source in DATA_SOURCES
        if source["doc_type"] == DOC_TYPE_MIGRATION
    }

    expected_paths = {
        f"data/migrations/{version}.md"
        for version in KNOWN_VERSIONS
    }

    assert migration_paths == expected_paths


def test_reference_manifest_entry_is_registered_as_reference():
    reference_entries = [
        source
        for source in DATA_SOURCES
        if source["path"]
        == "data/reference/openapi.json"
    ]

    assert len(reference_entries) == 1
    assert (
        reference_entries[0]["doc_type"]
        == DOC_TYPE_REFERENCE
    )


def test_changelog_manifest_entries_have_changelog_type():
    changelog_paths = {
        "data/changelog/changelog.md",
        "data/changelog/historical-changelog.md",
    }

    changelog_entries = [
        source
        for source in DATA_SOURCES
        if source["path"] in changelog_paths
    ]

    assert len(changelog_entries) == 2

    assert all(
        source["doc_type"] == DOC_TYPE_CHANGELOG
        for source in changelog_entries
    )