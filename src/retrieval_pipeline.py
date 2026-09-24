"""
Embedding pipeline + Chroma vector store + BM25 sparse index +
hybrid retrieval (hard filter -> dense + BM25 -> reciprocal rank fusion).
"""
import os
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv
from src.router import route_query
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
    from src.router import route_query

    print("\n=== 1. LOAD REAL DATA ===")

    chunks = load_all_chunks()
    print(f"Total chunks: {len(chunks)}")

    if not chunks:
        raise RuntimeError("FAIL: No chunks loaded.")

    print("PASS: Real chunks loaded.")

    # ------------------------------------------------------------------
    # 2. CHROMA
    # ------------------------------------------------------------------

    print("\n=== 2. CHROMA ===")

    collection = build_chroma_collection(chunks)

    print(f"Chroma documents: {collection.count()}")

    if collection.count() != len(chunks):
        raise RuntimeError(
            "FAIL: Chroma count does not match chunks."
        )

    print("PASS: Chroma index correct.")

    # ------------------------------------------------------------------
    # 3. BM25
    # ------------------------------------------------------------------

    print("\n=== 3. BM25 ===")

    bm25 = build_bm25_index(chunks)

    print(f"BM25 documents: {len(bm25.doc_freqs)}")

    if len(bm25.doc_freqs) != len(chunks):
        raise RuntimeError(
            "FAIL: BM25 count does not match chunks."
        )

    print("PASS: BM25 index correct.")

    # ------------------------------------------------------------------
    # 4. REAL QUERY UNDERSTANDING → ROUTER → RETRIEVAL
    # ------------------------------------------------------------------

    test_queries = [
        {
            "name": "Reference lookup - supported version",
            "question": (
                "How do I query a database in "
                "Notion-Version 2025-09-03?"
            ),
            "expected_intent": "reference",
            "expected_status": "ready",
            "should_retrieve": True,
        },
        {
            "name": "Reference lookup - unavailable version",
            "question": (
                "How do I query a database in "
                "Notion-Version 2022-06-28?"
            ),
            "expected_intent": "reference",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Migration path",
            "question": (
                "How do I upgrade from "
                "2021-08-16 to 2022-06-28?"
            ),
            "expected_intent": "migration",
            "expected_status": "ready",
            "should_retrieve": False,
        },
        {
            "name": "Breaking changes",
            "question": (
                "What breaks if I move from "
                "2022-06-28 to 2025-09-03?"
            ),
            "expected_intent": "migration",
            "expected_status": "ready",
            "should_retrieve": False,
        },
        {
            "name": "Diagnostic - missing version",
            "question": (
                "Why did my request start failing "
                "with a missing_version error?"
            ),
            "expected_intent": "diagnostic",
            "expected_status": "needs_clarification",
            "should_retrieve": False,
        },
        {
            "name": "Not found - unsupported version",
            "question": (
                "How do I configure webhook retry backoff "
                "in Notion-Version 2021-05-13?"
            ),
            "expected_intent": "reference",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Not found - completely unknown version",
            "question": (
                "How do I query a database in "
                "Notion-Version 2030-01-01?"
            ),
            "expected_intent": "reference",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Clarification trigger",
            "question": "How do I query a database?",
            "expected_intent": "reference",
            "expected_status": "needs_clarification",
            "should_retrieve": False,
        },
        {
            "name": "Migration - unknown source",
            "question": (
                "How do I upgrade from "
                "2030-01-01 to 2025-09-03?"
            ),
            "expected_intent": "migration",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
        {
            "name": "Migration - unknown target",
            "question": (
                "How do I upgrade from "
                "2022-06-28 to 2030-01-01?"
            ),
            "expected_intent": "migration",
            "expected_status": "not_found",
            "should_retrieve": False,
        },
    ]

    print(
        "\n=== 4. QUERY UNDERSTANDING → ROUTER → RETRIEVAL ==="
    )

    total_tests = len(test_queries)
    passed_tests = 0
    failed_tests = 0

    for test in test_queries:

        print("\n" + "=" * 80)
        print(f"TEST:     {test['name']}")
        print(f"QUESTION: {test['question']}")
        print("=" * 80)

        # --------------------------------------------------------------
        # Query Understanding
        # --------------------------------------------------------------

        print("\n[1. Query Understanding]")

        understood = understand_query(test["question"])

        print(json.dumps(understood, indent=2))

        intent = understood.get("intent")
        version = understood.get("version")

        print(f"Intent:  {intent}")
        print(f"Version: {version}")

        if intent != test["expected_intent"]:
            print(
                f"FAIL: Expected intent "
                f"'{test['expected_intent']}', got '{intent}'"
            )
            failed_tests += 1
            continue

        print("PASS: Intent correct.")

        # --------------------------------------------------------------
        # Router
        # --------------------------------------------------------------

        print("\n[2. Router]")

        routing = route_query(understood)

        print(json.dumps(routing, indent=2))

        status = routing.get("status")

        print(f"Router status: {status}")

        if status != test["expected_status"]:
            print(
                f"FAIL: Expected router status "
                f"'{test['expected_status']}', got '{status}'"
            )
            failed_tests += 1
            continue

        print("PASS: Router status correct.")

        # --------------------------------------------------------------
        # Verify early-stop behavior
        # --------------------------------------------------------------

        if not test["should_retrieve"]:

            if status in {"needs_clarification", "not_found"}:
                print(
                    "\nPASS: Retrieval correctly skipped by router."
                )
            elif intent == "migration" and status == "ready":
                print(
                    "\nPASS: Migration correctly stops before "
                    "direct retrieval and will use multi-hop flow."
                )
            else:
                print(
                    "\nFAIL: Test expected retrieval to be skipped."
                )
                failed_tests += 1
                continue

            passed_tests += 1
            continue

        # --------------------------------------------------------------
        # 3. Normal retrieval
        # --------------------------------------------------------------

        if status != "ready":
            print(
                "\nFAIL: Expected ready status before retrieval."
            )
            failed_tests += 1
            continue

        doc_types = routing.get("doc_types", [])

        if not doc_types:
            print("FAIL: Router returned no doc_types.")
            failed_tests += 1
            continue

        print("\n[3. Retrieval]")
        print(f"Doc types: {doc_types}")
        print(f"Version filter: {version}")

        all_results = []

        for doc_type in doc_types:

            results = hybrid_retrieve(
                query=test["question"],
                collection=collection,
                bm25=bm25,
                chunks=chunks,
                doc_type=doc_type,
                version=version,
                top_k=5,
            )

            all_results.extend(results)

        print(f"Results returned: {len(all_results)}")

        # --------------------------------------------------------------
        # Retrieval must actually return something for this test
        # --------------------------------------------------------------

        if not all_results:
            print(
                "FAIL: Router said ready, but retrieval returned "
                "zero results."
            )
            failed_tests += 1
            continue

        print("PASS: Retrieval returned results.")

        # --------------------------------------------------------------
        # Verify document type filter
        # --------------------------------------------------------------

        wrong_types = [
            result
            for result in all_results
            if result.get("doc_type") not in doc_types
        ]

        if wrong_types:
            print(
                "FAIL: Retrieval returned an incorrect document type."
            )
            failed_tests += 1
            continue

        print("PASS: Document type filter correct.")

        # --------------------------------------------------------------
        # Verify version filter
        # --------------------------------------------------------------

        wrong_versions = []

        for result in all_results:

            actual_version = (
                result.get("version")
                or result.get("release_date")
            )

            if actual_version != version:
                wrong_versions.append(result)

        if wrong_versions:
            print(
                "FAIL: Retrieval returned an incorrect version."
            )
            failed_tests += 1
            continue

        print("PASS: Version filter correct.")

        # --------------------------------------------------------------
        # Print actual retrieved chunks
        # --------------------------------------------------------------

        for i, result in enumerate(all_results, start=1):

            actual_version = (
                result.get("version")
                or result.get("release_date")
            )

            print(f"\n--- Result {i} ---")
            print(f"doc_type: {result.get('doc_type')}")
            print(f"version:  {actual_version}")
            print(f"endpoint: {result.get('endpoint', '')}")
            print(f"section:  {result.get('section', '')}")
            print(
                f"text:     "
                f"{result.get('text', '')[:300]}"
            )

        passed_tests += 1

    # ------------------------------------------------------------------
    # Final result
    # ------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("PIPELINE TEST COMPLETE")
    print("=" * 80)

    print(f"Total tests:  {total_tests}")
    print(f"Passed:       {passed_tests}")
    print(f"Failed:       {failed_tests}")

    if failed_tests:
        raise AssertionError(
            f"{failed_tests} pipeline test(s) failed."
        )

    print("\nALL REAL PIPELINE TESTS PASSED.")