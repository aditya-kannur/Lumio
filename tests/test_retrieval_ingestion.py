from unittest.mock import patch

from src.retrieval_pipeline import load_all_chunks, build_bm25_index

def test_load_all_chunks_loads_all_document_types():
    chunks=load_all_chunks()
    types={c["doc_type"] for c in chunks}
    assert {"reference","changelog","migration"} <= types
    assert chunks

def test_loaded_chunks_have_text():
    chunks=load_all_chunks()
    assert all(isinstance(c.get("text"),str) and c["text"].strip() for c in chunks)

def test_bm25_index_matches_loaded_chunk_count():
    chunks=load_all_chunks()
    bm25=build_bm25_index(chunks)
    assert len(bm25.doc_freqs) == len(chunks)
