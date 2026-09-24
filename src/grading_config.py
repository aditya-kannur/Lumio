# Grading pipeline configuration.
# MAX_RETRIES is the number of retries after the first grading attempt.
# 2 retries => maximum 3 Gemini grading calls for the whole request.
MAX_RETRIES = 2

# Maximum retrieved chunks sent to the grader per candidate group.
MAX_GRADING_CHUNKS = 5

# Kept for compatibility with the existing project.
RELEVANCE_THRESHOLD = 0.5
