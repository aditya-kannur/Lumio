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



if __name__ == "__main__":
    import json

    from src.query_understanding import understand_query

    print("\n=== 1. Loading real chunks ===")

    chunks = load_all_chunks()
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError("FAIL: No chunks loaded.")

    print("PASS: Real chunks loaded.")


    print("\n=== 2. Building Chroma ===")

    collection = build_chroma_collection(chunks)

    if collection.count() != len(chunks):
        raise RuntimeError(
            f"FAIL: Chroma has {collection.count()} documents, "
            f"expected {len(chunks)}."
        )

    print(f"Chroma documents: {collection.count()}")
    print("PASS: Chroma contains all chunks.")


    print("\n=== 3. Building BM25 ===")

    bm25 = build_bm25_index(chunks)

    if len(bm25.doc_freqs) != len(chunks):
        raise RuntimeError("FAIL: BM25 count does not match chunks.")

    print(f"BM25 documents: {len(bm25.doc_freqs)}")
    print("PASS: BM25 contains all chunks.")


    test_queries = [
        {
            "name": "Reference lookup",
            "question": "How do I query a database in Notion-Version 2022-06-28?",
            "expected_intent": "reference",
            "expected_doc_type": "reference",
            "expected_version": "2022-06-28",
        },
        {
            "name": "Migration path",
            "question": "How do I upgrade from 2021-08-16 to 2022-06-28?",
            "expected_intent": "migration",
            "expected_doc_type": "migration",
            "expected_version": None,
            "expected_from_version": "2021-08-16",
            "expected_to_version": "2022-06-28",
        },
        {
            "name": "Breaking changes",
            "question": "What breaks if I move from 2022-06-28 to 2025-09-03?",
            "expected_intent": "migration",
            "expected_doc_type": "migration",
            "expected_version": None,
            "expected_from_version": "2022-06-28",
            "expected_to_version": "2025-09-03",
        },
        {
            "name": "Diagnostic",
            "question": "Why did my request start failing with a missing_version error?",
            "expected_intent": "diagnostic",
            "expected_doc_type": "changelog",
            "expected_version": None,
        },
        {
            "name": "Not found",
            "question": "How do I configure webhook retry backoff in Notion-Version 2021-05-13?",
            "expected_intent": "reference",
            "expected_doc_type": "reference",
            "expected_version": "2021-05-13",
        },
        {
            "name": "Clarification trigger",
            "question": "How do I query a database?",
            "expected_intent": None,
            "expected_doc_type": None,
            "expected_version": None,
        },
    ]


    print("\n=== 4. Query Understanding → Retrieval Tests ===")

    for test in test_queries:
        print("\n" + "=" * 70)
        print(f"TEST: {test['name']}")
        print(f"QUESTION: {test['question']}")
        print("=" * 70)

        understood = understand_query(test["question"])

        print("\nQuery Understanding:")
        print(json.dumps(understood, indent=2))

        intent = understood.get("intent")
        version = understood.get("version")

        from_version = understood.get("from_version")
        to_version = understood.get("to_version")

        print(f"\nIntent:       {intent}")
        print(f"Version:      {version}")
        print(f"From version: {from_version}")
        print(f"To version:   {to_version}")

        # Validate intent when the test has an expected intent.
        if test["expected_intent"] is not None:
            if intent != test["expected_intent"]:
                print(
                    f"WARNING: Expected intent "
                    f"{test['expected_intent']}, got {intent}"
                )
            else:
                print("PASS: Intent is correct.")

        # Migration queries need both versions but don't use
        # a single version as the retrieval filter.
        if intent == "migration":
            if from_version != test.get("expected_from_version"):
                print(
                    f"WARNING: Expected from_version "
                    f"{test.get('expected_from_version')}, "
                    f"got {from_version}"
                )

            if to_version != test.get("expected_to_version"):
                print(
                    f"WARNING: Expected to_version "
                    f"{test.get('expected_to_version')}, "
                    f"got {to_version}"
                )

            print("\nMigration query detected.")
            print("Skipping direct single-version retrieval.")
            continue

        # Clarification query should not be retrieved.
        if test["expected_doc_type"] is None:
            print("\nExpected clarification.")
            print("Skipping retrieval.")
            continue

        doc_type = test["expected_doc_type"]

        results = hybrid_retrieve(
            query=test["question"],
            collection=collection,
            bm25=bm25,
            chunks=chunks,
            doc_type=doc_type,
            version=version,
            top_k=5,
        )

        print(f"\nRetrieved {len(results)} results.")

        if not results:
            print("WARNING: No results returned.")
            continue

        for i, result in enumerate(results, start=1):
            actual_version = (
                result.get("version")
                or result.get("release_date")
            )

            print(f"\n--- Result {i} ---")
            print(f"doc_type: {result.get('doc_type')}")
            print(f"version:  {actual_version}")
            print(f"endpoint: {result.get('endpoint', '')}")
            print(f"section:  {result.get('section', '')}")
            print(f"text:     {result.get('text', '')[:250]}")

        # Verify hard filters.
        wrong_type = [
            r for r in results
            if r.get("doc_type") != doc_type
        ]

        if wrong_type:
            print("FAIL: Wrong doc_type passed the filter.")
        else:
            print("PASS: doc_type filter is correct.")

        if version:
            wrong_version = [
                r for r in results
                if (
                    r.get("version") or r.get("release_date")
                ) != version
            ]

            if wrong_version:
                print("FAIL: Wrong version passed the filter.")
            else:
                print("PASS: version filter is correct.")

    print("\n" + "=" * 70)
    print("RETRIEVAL TEST SUITE COMPLETE")
    print("=" * 70)