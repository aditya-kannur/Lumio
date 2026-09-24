# Known Notion API versions, in chronological order.
# Used for multi-hop migration chaining — only these versions exist,
# no intermediate versions should ever be invented.
KNOWN_VERSIONS = [
    "2021-05-13",
    "2021-08-16",
    "2022-02-22",
    "2022-06-28",
    "2025-09-03",
    "2026-03-11",
]

# Versions that have full API reference data (see PRD Section 3 limitation).
REFERENCE_AVAILABLE_VERSIONS = [
    "2025-09-03",
    "2026-03-11",
]

# Document type labels used throughout ingestion and retrieval.
DOC_TYPE_REFERENCE = "reference"
DOC_TYPE_CHANGELOG = "changelog"
DOC_TYPE_MIGRATION = "migration"
