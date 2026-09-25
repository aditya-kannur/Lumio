"""
Reusable local Chroma cache for repeated pipeline tests.

First run:
    chunks -> embeddings -> data/chroma/

Later runs:
    chunks -> existing Chroma index
             no chunk re-embedding

The cache is invalidated if the chunk content or embedding model changes.
"""

import hashlib
import json
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction,
)

from src.chroma_config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    EMBEDDING_MODEL_NAME,
)


CACHE_DIR = Path(CHROMA_PERSIST_DIR)
MANIFEST_PATH = CACHE_DIR / "cache_manifest.json"


def _chunks_hash(chunks):
    """
    Create a stable hash of the actual chunk content + metadata.
    """

    normalized = []

    for chunk in chunks:
        normalized.append(
            {
                key: value
                for key, value in sorted(chunk.items())
            }
        )

    payload = json.dumps(
        normalized,
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


def _load_manifest():
    if not MANIFEST_PATH.exists():
        return None

    try:
        with open(
            MANIFEST_PATH,
            "r",
            encoding="utf-8",
        ) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _save_manifest(chunks):
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest = {
        "chunk_count": len(chunks),
        "chunks_hash": _chunks_hash(chunks),
        "embedding_model": EMBEDDING_MODEL_NAME,
        "collection": CHROMA_COLLECTION_NAME,
    }

    with open(
        MANIFEST_PATH,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            manifest,
            f,
            indent=2,
        )


def _cache_is_valid(
    chunks,
    collection,
):
    manifest = _load_manifest()

    if not manifest:
        return False

    if manifest.get("embedding_model") != EMBEDDING_MODEL_NAME:
        return False

    if manifest.get("collection") != CHROMA_COLLECTION_NAME:
        return False

    if manifest.get("chunk_count") != len(chunks):
        return False

    if manifest.get("chunks_hash") != _chunks_hash(chunks):
        return False

    if collection.count() != len(chunks):
        return False

    return True


def get_chroma_collection(chunks):
    """
    Load the persistent Chroma collection.

    If the cache is valid:
        reuse existing embeddings.

    If the cache is missing/stale:
        rebuild the collection once.
    """

    print(
        f"  Chroma cache: {CHROMA_PERSIST_DIR}"
    )

    ef = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )

    client = chromadb.PersistentClient(
        path=CHROMA_PERSIST_DIR
    )

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=ef,
    )

    # --------------------------------------------------------------
    # CACHE HIT
    # --------------------------------------------------------------

    if _cache_is_valid(
        chunks,
        collection,
    ):
        print(
            f"  Chroma: cache hit — "
            f"{collection.count()} chunks, "
            f"embeddings reused."
        )
        return collection

    # --------------------------------------------------------------
    # CACHE MISS / STALE CACHE
    # --------------------------------------------------------------

    print(
        "  Chroma: cache miss or stale index."
    )

    print(
        f"  Chroma: rebuilding {len(chunks)} chunks..."
    )

    existing = collection.get(
        include=[]
    )["ids"]

    if existing:
        collection.delete(
            ids=existing
        )

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    metadatas = []

    for chunk in chunks:

        metadata = {
            key: value
            for key, value in chunk.items()
            if key != "text"
        }

        for key, value in metadata.items():

            if isinstance(
                value,
                list,
            ):
                metadata[key] = ", ".join(
                    str(item)
                    for item in value
                )

        metadatas.append(metadata)

    ids = [
        f"chunk_{i}"
        for i in range(len(chunks))
    ]

    batch_size = 50

    for start in range(
        0,
        len(chunks),
        batch_size,
    ):

        end = min(
            start + batch_size,
            len(chunks),
        )

        collection.add(
            ids=ids[start:end],
            documents=texts[start:end],
            metadatas=metadatas[start:end],
        )

        print(
            f"    indexed {end}/{len(chunks)}"
        )

    _save_manifest(chunks)

    print(
        "  Chroma: cache saved."
    )

    return collection