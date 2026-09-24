# Standard user-facing messages shared across the pipeline.
# Centralised here so router, grading, and main all show the exact same text.

CLARIFICATION_QUESTION = (
    "Could you clarify which Notion API version you're asking about? "
    "Known versions are: 2021-05-13, 2021-08-16, 2022-02-22, 2022-06-28, "
    "2025-09-03, and 2026-03-11."
)

NOT_FOUND_MESSAGE = (
    "Sorry, I couldn't find a reliable answer for that in the available "
    "Notion API documentation. Please double-check the version and try "
    "rephrasing your question."
)
