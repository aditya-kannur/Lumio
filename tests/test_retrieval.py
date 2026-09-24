from src.retrieval_pipeline import reciprocal_rank_fusion, hybrid_retrieve, build_bm25_index

def test_rrf_rewards_documents_appearing_in_multiple_rankings():
    result = reciprocal_rank_fusion([["a","b","c"],["b","a","d"]])
    assert set(result[:2]) == {"a","b"}

def test_bm25_index_can_score_query():
    bm25 = build_bm25_index([
        {"text": "query database"},
        {"text": "query database"},
        {"text": "query database"},
        {"text": "create page"},
    ])

    scores = bm25.get_scores(["page"])

    assert len(scores) == 4
    assert scores[3] > max(scores[:3])

def test_hybrid_retrieval_hard_filters_before_ranking():
    chunks = [
        {"text":"wrong version","doc_type":"reference","version":"2022-06-28"},
        {"text":"target","doc_type":"reference","version":"2025-09-03"},
        {"text":"wrong type","doc_type":"migration","version":"2025-09-03"},
    ]
    class Collection:
        def query(self, **kwargs):
            return {"ids":[["chunk_0","chunk_1","chunk_2"]]}
    class BM25:
        def get_scores(self, query): return [100, 1, 100]
    result = hybrid_retrieve("target", Collection(), BM25(), chunks, doc_type="reference", version="2025-09-03", top_k=5)
    assert result == [chunks[1]]

def test_hybrid_retrieval_returns_empty_for_no_hard_filter_match():
    chunks = [{"text":"x","doc_type":"reference","version":"2025-09-03"}]
    class Collection:
        def query(self, **kwargs): raise AssertionError("dense retrieval should not run")
    class BM25:
        def get_scores(self, query): raise AssertionError("BM25 should not run")
    assert hybrid_retrieve("q", Collection(), BM25(), chunks, doc_type="migration", version="2025-09-03") == []
