"""
Embedding pipeline + Chroma vector store + BM25 sparse index +
hybrid retrieval (hard filter -> dense + BM25 -> reciprocal rank fusion).
"""
import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
load_dotenv()

# Force HuggingFace to use local cache — prevents network calls on startup
# when the model is already downloaded.
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from src.chroma_config import CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME
from src.chunking.migration_chunker import chunk_migration_file
from src.chunking.changelog_chunker import chunk_changelog
from src.chunking.reference_chunker import chunk_reference_file
from src.data_sources import DATA_SOURCES


# ---------------------------------------------------------------------------
# 1. Load + chunk everything
# ---------------------------------------------------------------------------

def load_all_chunks():
    all_chunks = []
    for source in DATA_SOURCES:
        doc_type = source["doc_type"]
        path = source["path"]
        if doc_type == "migration":
            chunks = chunk_migration_file(path)
        elif doc_type == "changelog":
            chunks = chunk_changelog(open(path, encoding="utf-8").read(), doc_type="changelog")
        elif doc_type == "reference":
            chunks = chunk_reference_file(path)
        else:
            continue
        all_chunks.extend(chunks)
    return all_chunks


# ---------------------------------------------------------------------------
# 2. Embed + store in Chroma  (skips re-indexing if already populated)
# ---------------------------------------------------------------------------

def build_chroma_collection(chunks, embed_model=None):
    """
    Uses Chroma's built-in SentenceTransformerEmbeddingFunction so embedding
    happens inside Chroma's optimised path. Skips re-indexing entirely when
    the collection already has the right number of documents.
    embed_model param kept for API compatibility but not used here.
    """
    ef = SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=ef,
    )

    # Fast path: already indexed — nothing to do.
    if collection.count() == len(chunks):
        print(f"  Chroma: {collection.count()} chunks already indexed, skipping.")
        return collection

    print(f"  Chroma: indexing {len(chunks)} chunks...")

    # Clear stale data before re-adding.
    existing = collection.get(include=[])["ids"]
    if existing:
        collection.delete(ids=existing)

    texts = [c["text"] for c in chunks]

    metadatas = []
    for c in chunks:
        meta = {k: v for k, v in c.items() if k != "text"}
        for key, val in meta.items():
            if isinstance(val, list):
                meta[key] = ", ".join(str(v) for v in val)
        metadatas.append(meta)

    ids = [f"chunk_{i}" for i in range(len(chunks))]

    # Add in batches of 50 so Chroma doesn't choke on large payloads.
    batch = 50
    for start in range(0, len(chunks), batch):
        end = min(start + batch, len(chunks))
        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )
        print(f"    indexed {end}/{len(chunks)}")

    return collection


# ---------------------------------------------------------------------------
# 3. BM25 sparse index (in-memory)
# ---------------------------------------------------------------------------

def build_bm25_index(chunks):
    tokenized_corpus = [c["text"].lower().split() for c in chunks]
    return BM25Okapi(tokenized_corpus)


# ---------------------------------------------------------------------------
# 4. Hybrid retrieval: hard filter -> dense + BM25 -> RRF merge
# ---------------------------------------------------------------------------

def reciprocal_rank_fusion(rank_lists, k=60):
    scores = {}
    for ranked_ids in rank_lists:
        for rank, doc_id in enumerate(ranked_ids):
            scores[doc_id] = scores.get(doc_id, 0) + 1.0 / (k + rank + 1)
    return sorted(scores.keys(), key=lambda doc_id: scores[doc_id], reverse=True)


def hybrid_retrieve(query, collection, bm25, chunks, model=None, doc_type=None, version=None, top_k=5):
    """
    Hard filter first, then dense + BM25 over the filtered set, merged via RRF.
    """
    # --- Hard filter ---
    filtered_indices = [
        i for i, c in enumerate(chunks)
        if (doc_type is None or c.get("doc_type") == doc_type)
        and (version is None or c.get("version") == version or c.get("release_date") == version)
    ]
    if not filtered_indices:
        return []

    filtered_ids = {f"chunk_{i}" for i in filtered_indices}

    # --- Dense retrieval: small n_results, filter by doc_type in Chroma ---
    n_dense = min(top_k * 4, len(filtered_indices))
    where = {"doc_type": doc_type} if doc_type else None
    dense_results = collection.query(
        query_texts=[query],
        n_results=n_dense,
        where=where,
    )
    dense_ranked = [doc_id for doc_id in dense_results["ids"][0] if doc_id in filtered_ids]

    # --- BM25 retrieval ---
    tokenized_query = query.lower().split()
    bm25_scores = bm25.get_scores(tokenized_query)
    bm25_ranked_all = sorted(range(len(chunks)), key=lambda i: bm25_scores[i], reverse=True)
    bm25_ranked = [f"chunk_{i}" for i in bm25_ranked_all if f"chunk_{i}" in filtered_ids]

    # --- Fuse ---
    fused_ids = reciprocal_rank_fusion([dense_ranked, bm25_ranked])[:top_k]
    fused_indices = [int(doc_id.split("_")[1]) for doc_id in fused_ids]
    return [chunks[i] for i in fused_indices]
