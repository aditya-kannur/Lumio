"""
RETRIEVAL PIPELINE TEST COVERAGE
================================

This file tests the document loading and BM25 indexing layer.

It verifies:

1. CHUNK LOADING
   - All three document types are loaded
   - Chunks are returned
   - Chunk text is valid
   - Required metadata exists
   - Chunk IDs are unique

2. DATA INTEGRITY
   - No loaded chunk has empty text
   - Every loaded chunk has a document type
   - Every loaded chunk has a persistent chunk ID

3. BM25 INDEXING
   - BM25 index can be built
   - Index size matches loaded chunk count
   - BM25 can retrieve relevant documents
   - Rebuilding the index is deterministic in size
"""

from src.retrieval_pipeline import (
    load_all_chunks,
    build_bm25_index,
)


# ==============================================================
# CHUNK LOADING
# ==============================================================


def test_load_all_chunks_returns_chunks():
    chunks = load_all_chunks()

    assert chunks
    assert isinstance(chunks, list)


def test_load_all_chunks_loads_all_document_types():
    chunks = load_all_chunks()

    types = {
        chunk["doc_type"]
        for chunk in chunks
    }

    assert {
        "reference",
        "changelog",
        "migration",
    } <= types


def test_loaded_chunks_have_non_empty_text():
    chunks = load_all_chunks()

    assert all(
        isinstance(chunk.get("text"), str)
        and chunk["text"].strip()
        for chunk in chunks
    )


def test_loaded_chunks_have_doc_type():
    chunks = load_all_chunks()

    assert all(
        isinstance(chunk.get("doc_type"), str)
        and chunk["doc_type"].strip()
        for chunk in chunks
    )


def test_loaded_chunks_have_chunk_id():
    chunks = load_all_chunks()

    assert all(
        isinstance(chunk.get("chunk_id"), str)
        and chunk["chunk_id"].strip()
        for chunk in chunks
    )


def test_loaded_chunk_ids_are_unique():
    chunks = load_all_chunks()

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in chunks
    ]

    assert len(chunk_ids) == len(set(chunk_ids))


def test_loaded_chunks_have_required_fields():
    chunks = load_all_chunks()

    required_fields = {
        "text",
        "doc_type",
        "chunk_id",
    }

    for chunk in chunks:
        assert required_fields <= chunk.keys()


# ==============================================================
# DOCUMENT TYPE DISTRIBUTION
# ==============================================================


def test_loaded_chunks_have_non_zero_count_for_each_type():
    chunks = load_all_chunks()

    counts = {}

    for chunk in chunks:
        doc_type = chunk["doc_type"]
        counts[doc_type] = counts.get(doc_type, 0) + 1

    assert counts["reference"] > 0
    assert counts["changelog"] > 0
    assert counts["migration"] > 0


# ==============================================================
# BM25 INDEXING
# ==============================================================


def test_bm25_index_can_be_built():
    chunks = load_all_chunks()

    bm25 = build_bm25_index(chunks)

    assert bm25 is not None


def test_bm25_index_matches_loaded_chunk_count():
    chunks = load_all_chunks()

    bm25 = build_bm25_index(chunks)

    assert len(bm25.doc_freqs) == len(chunks)


def test_bm25_index_contains_all_loaded_documents():
    chunks = load_all_chunks()

    bm25 = build_bm25_index(chunks)

    assert len(bm25.doc_freqs) == len(chunks)
    assert len(bm25.doc_len) == len(chunks)


def test_bm25_index_can_retrieve_a_known_term():
    chunks = load_all_chunks()

    bm25 = build_bm25_index(chunks)

    results = bm25.get_top_n(
        ["database"],
        chunks,
        n=5,
    )

    assert results
    assert all(
        isinstance(result, dict)
        for result in results
    )


def test_bm25_index_retrieval_results_have_text():
    chunks = load_all_chunks()

    bm25 = build_bm25_index(chunks)

    results = bm25.get_top_n(
        ["database"],
        chunks,
        n=5,
    )

    assert all(
        result["text"].strip()
        for result in results
    )


def test_bm25_index_is_deterministic_in_size():
    chunks = load_all_chunks()

    first_index = build_bm25_index(chunks)
    second_index = build_bm25_index(chunks)

    assert len(first_index.doc_freqs) == len(
        second_index.doc_freqs
    )

    assert len(first_index.doc_len) == len(
        second_index.doc_len
    )