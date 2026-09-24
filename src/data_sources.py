# Dataset manifest for the ingestion pipeline: one record per dataset file,
# each pairing the file's path with its doc type. Ordered, not keyed — build a
# dict from it if you need lookup by path.
#
# Version strings and doc-type labels come from constants.py so that adding a
# version there is enough to pick up its migration guide here. The download URLs
# for these same files live in scripts/download_dataset.py.

try:
    from .constants import (
        DOC_TYPE_CHANGELOG,
        DOC_TYPE_MIGRATION,
        DOC_TYPE_REFERENCE,
        KNOWN_VERSIONS,
    )
except ImportError:  # imported as a top-level module rather than a package
    from constants import (
        DOC_TYPE_CHANGELOG,
        DOC_TYPE_MIGRATION,
        DOC_TYPE_REFERENCE,
        KNOWN_VERSIONS,
    )

DATA_SOURCES = [
    {"path": "data/reference/openapi.json", "doc_type": DOC_TYPE_REFERENCE},
    {"path": "data/changelog/changelog.md", "doc_type": DOC_TYPE_CHANGELOG},
    {"path": "data/changelog/historical-changelog.md", "doc_type": DOC_TYPE_CHANGELOG},
] + [
    {"path": f"data/migrations/{version}.md", "doc_type": DOC_TYPE_MIGRATION}
    for version in KNOWN_VERSIONS
]
