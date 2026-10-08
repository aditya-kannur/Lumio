"""
RETRIEVAL PIPELINE TEST COVERAGE
================================

This file tests the actual hybrid retrieval behavior.

Retrieval architecture being tested:

    Query
      |
      v
    Hard filters
    (doc_type + version)
      |
      +------------------+
      |                  |
      v                  v
   Dense/Chroma        BM25
      |                  |
      +--------+---------+
               |
               v
        Reciprocal Rank
           Fusion
               |
               v
             top_k
               |
               v
        Retrieved chunks

The tests cover:

1. RECIPROCAL RANK FUSION
   - Documents appearing in multiple rankings are promoted
   - Documents appearing once are still retained
   - Duplicate IDs are merged
   - Empty rankings are handled
   - Ranking is deterministic

2. HARD FILTERING
   - doc_type filtering
   - version filtering
   - changelog release_date filtering
   - both filters together
   - no-match behavior

3. HYBRID RETRIEVAL
   - Dense and BM25 rankings are combined
   - Results are returned as original chunks
   - Results contain valid chunk IDs
   - Duplicate results are not returned
   - top_k is respected
   - no-filter retrieval works

4. RETRIEVAL INTEGRITY
   - Returned chunks satisfy requested filters
   - Same input produces stable ordering
"""


from src.retrieval_pipeline import (
    reciprocal_rank_fusion,
    hybrid_retrieve,
    build_bm25_index,
)


# ==============================================================
# TEST HELPERS
# ==============================================================


class MockCollection:
    """
    Minimal Chroma-like collection used for retrieval unit tests.
    """

    def __init__(self, ids):
        self.ids = ids
        self.query_calls = []

    def query(self, **kwargs):
        self.query_calls.append(kwargs)

        return {
            "ids": [self.ids],
        }


class FailingCollection:
    """
    Collection that fails if dense retrieval is unexpectedly called.
    """

    def query(self, **kwargs):
        raise AssertionError(
            "Dense retrieval should not run."
        )


class FailingBM25:
    """
    BM25 object that fails if scoring is unexpectedly called.
    """

    def get_scores(self, query):
        raise AssertionError(
            "BM25 retrieval should not run."
        )


# ==============================================================
# RECIPROCAL RANK FUSION
# ==============================================================


def test_rrf_rewards_documents_appearing_in_multiple_rankings():
    result = reciprocal_rank_fusion(
        [
            ["a", "b", "c"],
            ["b", "a", "d"],
        ]
    )

    assert set(result[:2]) == {"a", "b"}


def test_rrf_retains_documents_present_in_only_one_ranking():
    result = reciprocal_rank_fusion(
        [
            ["a", "b"],
            ["c", "d"],
        ]
    )

    assert set(result) == {
        "a",
        "b",
        "c",
        "d",
    }


def test_rrf_removes_duplicate_document_ids():
    result = reciprocal_rank_fusion(
        [
            ["a", "a", "b"],
            ["b", "c"],
        ]
    )

    assert len(result) == len(set(result))
    assert set(result) == {
        "a",
        "b",
        "c",
    }


def test_rrf_handles_empty_rankings():
    result = reciprocal_rank_fusion(
        [
            [],
            ["a", "b"],
        ]
    )

    assert result == ["a", "b"]


def test_rrf_handles_all_empty_rankings():
    result = reciprocal_rank_fusion(
        [
            [],
            [],
        ]
    )

    assert result == []


def test_rrf_is_deterministic():
    rankings = [
        ["a", "b", "c"],
        ["b", "a", "d"],
    ]

    first = reciprocal_rank_fusion(rankings)
    second = reciprocal_rank_fusion(rankings)

    assert first == second


def test_rrf_k_parameter_does_not_create_duplicate_results():
    result = reciprocal_rank_fusion(
        [
            ["a", "b"],
            ["b", "c"],
        ],
        k=10,
    )

    assert len(result) == len(set(result))


# ==============================================================
# BM25 RETRIEVAL BEHAVIOR
# ==============================================================


def test_bm25_index_can_score_query():
    chunks = [
        {"text": "query database"},
        {"text": "query database"},
        {"text": "query database"},
        {"text": "create page"},
    ]

    bm25 = build_bm25_index(chunks)

    scores = bm25.get_scores(["page"])

    assert len(scores) == 4
    assert scores[3] > max(scores[:3])


# ==============================================================
# HARD FILTERING
# ==============================================================


def test_hybrid_retrieval_filters_by_doc_type_before_ranking():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "wrong version",
            "doc_type": "reference",
            "version": "2022-06-28",
        },
        {
            "chunk_id": "chunk_1",
            "text": "target",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "chunk_2",
            "text": "wrong type",
            "doc_type": "migration",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
            "chunk_2",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "target",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        top_k=5,
    )

    assert result
    assert all(
        chunk["doc_type"] == "reference"
        for chunk in result
    )


def test_hybrid_retrieval_filters_by_version():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "old target",
            "doc_type": "reference",
            "version": "2022-06-28",
        },
        {
            "chunk_id": "chunk_1",
            "text": "new target",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "target",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    assert result == [chunks[1]]


def test_hybrid_retrieval_uses_release_date_for_changelog():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "old change",
            "doc_type": "changelog",
            "release_date": "2024-01-01",
        },
        {
            "chunk_id": "chunk_1",
            "text": "new change",
            "doc_type": "changelog",
            "release_date": "2025-01-01",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "change",
        collection,
        bm25,
        chunks,
        doc_type="changelog",
        version="2025-01-01",
        top_k=5,
    )

    assert result == [chunks[1]]


def test_hybrid_retrieval_applies_doc_type_and_version_together():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "wrong type",
            "doc_type": "migration",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "chunk_1",
            "text": "wrong version",
            "doc_type": "reference",
            "version": "2022-06-28",
        },
        {
            "chunk_id": "chunk_2",
            "text": "correct",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
            "chunk_2",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "correct",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    assert result == [chunks[2]]


def test_hybrid_retrieval_returns_empty_for_no_hard_filter_match():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "reference content",
            "doc_type": "reference",
            "version": "2025-09-03",
        }
    ]

    assert (
        hybrid_retrieve(
            "query",
            FailingCollection(),
            FailingBM25(),
            chunks,
            doc_type="migration",
            version="2025-09-03",
        )
        == []
    )


# ==============================================================
# HYBRID RETRIEVAL
# ==============================================================


def test_hybrid_retrieval_returns_original_chunks():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "database query",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "chunk_1",
            "text": "page creation",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database query",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    assert result
    assert all(
        result_chunk in chunks
        for result_chunk in result
    )


def test_hybrid_retrieval_returns_valid_chunk_ids():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "database query",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "chunk_1",
            "text": "page creation",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database query",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    chunk_ids = [
        chunk["chunk_id"]
        for chunk in result
    ]

    assert all(chunk_ids)
    assert len(chunk_ids) == len(set(chunk_ids))


def test_hybrid_retrieval_respects_top_k():
    chunks = [
        {
            "chunk_id": f"chunk_{i}",
            "text": f"database query {i}",
            "doc_type": "reference",
            "version": "2025-09-03",
        }
        for i in range(10)
    ]

    collection = MockCollection(
        [
            chunk["chunk_id"]
            for chunk in chunks
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database query",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=3,
    )

    assert len(result) <= 3


def test_hybrid_retrieval_does_not_return_duplicate_chunks():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "database query",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "chunk_1",
            "text": "database page",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
            "chunk_0",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    ids = [
        chunk["chunk_id"]
        for chunk in result
    ]

    assert len(ids) == len(set(ids))


def test_hybrid_retrieval_can_use_both_dense_and_bm25_rankings():
    chunks = [
        {
            "chunk_id": "dense",
            "text": "unrelated words",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "bm25",
            "text": "database database database",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "dense",
            "bm25",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=2,
    )

    ids = [
        chunk["chunk_id"]
        for chunk in result
    ]

    assert "dense" in ids
    assert "bm25" in ids


def test_hybrid_retrieval_without_filters_can_search_all_chunks():
    chunks = [
        {
            "chunk_id": "reference_1",
            "text": "database query reference",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "migration_1",
            "text": "database migration",
            "doc_type": "migration",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "reference_1",
            "migration_1",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        top_k=5,
    )

    assert result
    assert {
        chunk["chunk_id"]
        for chunk in result
    } <= {
        "reference_1",
        "migration_1",
    }


# ==============================================================
# RETRIEVAL RESULT INTEGRITY
# ==============================================================


def test_retrieval_results_respect_doc_type_filter():
    chunks = [
        {
            "chunk_id": "reference",
            "text": "database reference",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "migration",
            "text": "database migration",
            "doc_type": "migration",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "reference",
            "migration",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    assert all(
        chunk["doc_type"] == "reference"
        for chunk in result
    )


def test_retrieval_results_respect_version_filter():
    chunks = [
        {
            "chunk_id": "old",
            "text": "database old",
            "doc_type": "reference",
            "version": "2022-06-28",
        },
        {
            "chunk_id": "new",
            "text": "database new",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "old",
            "new",
        ]
    )

    bm25 = build_bm25_index(chunks)

    result = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    assert all(
        chunk["version"] == "2025-09-03"
        for chunk in result
    )


def test_retrieval_result_order_is_deterministic():
    chunks = [
        {
            "chunk_id": "chunk_0",
            "text": "database query",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
        {
            "chunk_id": "chunk_1",
            "text": "database page",
            "doc_type": "reference",
            "version": "2025-09-03",
        },
    ]

    collection = MockCollection(
        [
            "chunk_0",
            "chunk_1",
        ]
    )

    bm25 = build_bm25_index(chunks)

    first = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    second = hybrid_retrieve(
        "database",
        collection,
        bm25,
        chunks,
        doc_type="reference",
        version="2025-09-03",
        top_k=5,
    )

    first_ids = [
        chunk["chunk_id"]
        for chunk in first
    ]

    second_ids = [
        chunk["chunk_id"]
        for chunk in second
    ]

    assert first_ids == second_ids