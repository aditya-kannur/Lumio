# Standard user-facing messages shared across the pipeline.


CLARIFICATION_QUESTION = (
    "Could you clarify which Notion API version you're asking about? "
    "Known versions are: 2021-05-13, 2021-08-16, 2022-02-22, 2022-06-28, "
    "2025-09-03, and 2026-03-11."
)


NOT_FOUND_MESSAGE = (
    "Not found in docs for this version. "
    "I could not establish sufficient supporting evidence after the maximum "
    "number of retrieval and grading attempts."
)


RETRIEVAL_NOT_FOUND_MESSAGE = (
    "Not found in docs for this version. "
    "Retrieval returned no matching evidence for the requested version."
)


GRADER_ERROR_MESSAGE = (
    "Not found in docs for this version. "
    "The evidence grader could not validate the retrieved evidence after "
    "the maximum number of grading attempts."
)