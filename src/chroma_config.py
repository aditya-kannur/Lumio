# Chroma vector store configuration.
#
# Every module that opens the store — indexing, dense retrieval, evaluation —
# reads these constants, so that all of them address the same collection in the
# same directory with the same embedding model.

# Directory Chroma persists its database to, relative to the repo root.
CHROMA_PERSIST_DIR = "data/chroma"

# One collection holds reference, changelog and migration chunks together.
# doc_type stays a metadata filter rather than a separate collection, so a
# diagnostic query can search changelog and reference in a single pass.
CHROMA_COLLECTION_NAME = "versionquery_docs"

# sentence-transformers model used to embed both chunks and queries.
# Chunks and queries must be embedded with the same model or their vectors are
# not comparable. Swappable with "sentence-transformers/all-MiniLM-L6-v2",
# which is also 384-dimensional.
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Output dimensionality of EMBEDDING_MODEL_NAME. Kept here so the collection
# can be validated on open rather than failing at first query.
EMBEDDING_DIMENSIONS = 384
