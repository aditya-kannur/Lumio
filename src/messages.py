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
    "The evidence grading service could not validate the retrieved "
    "evidence. Please try again."
)

LLM_SERVICE_ERROR_MESSAGE = (
    "The language model service is currently unavailable. "
    "Please try again."
)


GENERATION_ERROR_MESSAGE = (
    "I couldn't generate an answer from the available "
    "documentation. Please try again."
)


VERIFICATION_ERROR_MESSAGE = (
    "I couldn't verify the generated answer against "
    "the documentation. No unverified answer will be returned."
)


RETRIEVAL_ERROR_MESSAGE = (
    "I couldn't retrieve or evaluate the relevant "
    "documentation. Please try again."
)


UNDERSTANDING_ERROR_MESSAGE = (
    "I couldn't reliably understand the request. "
    "Please try rephrasing your question."
)


ROUTING_ERROR_MESSAGE = (
    "I couldn't determine which documentation path "
    "to use for your request."
)