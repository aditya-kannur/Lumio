
# VersionQuery

A version-aware Q&A assistant for API documentation.

VersionQuery answers developer questions using version-specific API references, migration guides, and changelogs. It retrieves relevant documentation, generates grounded answers, verifies them, and provides citations to help developers confirm the information.

## Problem

API documentation changes between versions. Generic documentation search and RAG systems can retrieve information from the wrong version, mix incompatible behaviors, or generate answers without verifiable sources.

VersionQuery addresses this by making version correctness, evidence grounding, and source verification core parts of the retrieval and generation pipeline.

## Core Features

- **Query understanding:** Identifies the question intent, requested API version, document type, and migration source and target versions.
- **Structure-aware chunking:** Splits API references by endpoint, migration guides by change, and changelogs by release entry.
- **Hybrid retrieval:** Combines dense vector search, BM25 keyword search, and Reciprocal Rank Fusion (RRF).
- **Hard filtering:** Applies version and document-type constraints to prevent retrieval from incompatible documentation.
- **Document grading:** Evaluates retrieved evidence for relevance, version correctness, and document-type suitability.
- **Retry handling:** Transforms queries and retries retrieval when the initial evidence is insufficient, subject to retry limits.
- **Multi-hop migration retrieval:** Retrieves information across intermediate versions and organizes it into an ordered upgrade path.
- **Grounded generation:** Generates answers using retrieved documentation rather than unsupported general knowledge.
- **Answer verification:** Checks evidence support, version consistency, and citation validity.
- **Honest failure:** Returns a not-found response when sufficient supporting documentation cannot be established.
- **Citations:** Provides source information, including document, section, and version.

## Architecture

The pipeline follows this general flow:

1. Query understanding
2. Routing and document selection
3. Hybrid retrieval
4. Document grading
5. Query transformation and retry when needed
6. Answer generation
7. Answer verification and citation

Migration queries additionally use version-hop decomposition to retrieve relevant changes across the requested upgrade path.

The project uses LangGraph to coordinate pipeline stages and conditional transitions.

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python |
| Documentation dataset | Notion API documentation |
| Chunking | Rule-based, structure-aware parsing |
| Dense retrieval | Sentence-transformer embeddings |
| Sparse retrieval | BM25 (`rank_bm25`) |
| Vector store | Chroma |
| Hybrid ranking | Reciprocal Rank Fusion |
| LLM tasks | Query understanding, grading, generation, verification |
| Orchestration | LangGraph |
| Backend | FastAPI (planned integration) |
| Frontend | To be implemented |

## Data Sources

VersionQuery currently uses Notion's public API documentation as its representative dataset, including:

- API reference documentation
- Migration and upgrade guides
- Changelog entries

The ingestion and retrieval pipeline preserves document-type and version metadata so that evidence can be selected according to the question.

## Design Principles

### Version correctness first

Version and document-type constraints take priority over semantic similarity. Content from an incompatible version must not be treated as valid evidence simply because it is relevant to the wording of a question.

### Evidence-grounded answers

Generated claims must be supported by retrieved documentation. If sufficient evidence cannot be established, the system should not guess.

### Verifiable citations

Answers should identify the source document, relevant section, and API version so developers can verify the response.

### Controlled retries

Retrieval retries are bounded to avoid uncontrolled loops and to ensure that unsupported questions eventually receive an honest not-found response.

### Structure-aware retrieval

API endpoints, migration changes, and changelog entries are represented as meaningful document units rather than arbitrary text fragments.

## Scope

The current focus is a working demonstration of version-aware documentation retrieval and grounded answer generation using the Notion API dataset.

Out of scope for the MVP:

- Web search or general-knowledge fallback
- Multi-vendor support
- Real-time documentation synchronization
- Cross-encoder reranking and multi-query retrieval
- User accounts, authentication, and multi-tenant usage
- Production-scale infrastructure and latency optimization

## Core Principle

> If an answer cannot be grounded in documentation for the correct API version, VersionQuery should not answer.
