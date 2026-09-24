# VersionQuery

A version-aware Q&A assistant for API documentation.

VersionQuery answers developer questions strictly from versioned API documentation, retrieves only content relevant to the requested API version, and provides exact citations so every answer can be independently verified.

## Problem Statement

Software vendors maintain API references, migration guides, and changelogs across multiple product versions.

Developers integrating with or upgrading these APIs often waste time manually cross-referencing documentation and can easily make integration errors because generic documentation search and RAG systems typically:

* Default to the latest version
* Mix content from different API versions
* Retrieve documents based only on semantic similarity
* Provide answers without verifiable sources

VersionQuery addresses this by making **version correctness and source verification first-class parts of retrieval and generation**.

## Objective

### Why are we building this?

Developers need to trust that an answer about a specific API version is actually correct for that version and be able to verify the answer against the vendor's documentation.

Generic RAG-over-docs systems often fail because semantic similarity alone does not guarantee version correctness.

### What are we building?

VersionQuery is a Q&A assistant that answers developer questions strictly from a vendor's versioned documentation:

* API reference
* Migration and upgrade guides
* Changelog

Every answer is filtered to the appropriate version and includes a citation to the exact source document and section.

### Success Criteria

For this sprint, VersionQuery should demonstrate that:

1. A developer can ask a version-scoped question and receive an answer correct for that version.
2. Every answer contains a verifiable citation including the document, section, and version.
3. The system explicitly responds with **"Not found in docs for this version"** when sufficient grounding cannot be found.
4. The system can demonstrate these capabilities using the real Notion API documentation dataset.

## Target User

The target user is a developer integrating with or upgrading a versioned API.

Developers typically need to answer one of three types of questions:

### Reference Lookup

> "How do I do X in version Y?"

Example:

> How do I query a database in Notion-Version 2022-06-28?

### Diagnostic

> "Why did this break or change?"

Example:

> Why is my database query returning an empty result when it worked yesterday?

### Migration

> "How do I upgrade from version A to B?"

Example:

> How do I upgrade from 2021-08-16 to 2022-06-28?

For this sprint, Notion's public API documentation is used as the representative dataset.

Notion was selected because its documentation contains API references, changelogs, and upgrade/migration information while having a relatively small and uniform surface area suitable for a sprint-sized implementation.

## Team & Timeline

* **Team size:** 2
* **Duration:** Sprint
* **Week 1:** PRD and system design
* **Week 2+:** Implementation, testing, and presentation
* **Dataset:** Notion API documentation

## User Flow

### 1. Reference Lookup — Happy Path

The developer asks:

> How do I query a database in Notion-Version 2022-06-28?

The system:

1. Extracts the intent as `reference`.
2. Extracts the requested version as `2022-06-28`.
3. Routes the query to the API reference documents.
4. Applies a hard filter for the requested version.
5. Retrieves relevant chunks.
6. Grades the retrieved documents for relevance, version correctness, and document type.
7. Generates an answer strictly from the retrieved content.
8. Displays the answer with an exact citation containing the document, section, and version.

The developer can then verify the answer against the original source.

### 2. Missing Version — Clarification Path

The developer asks:

> How do I query a database?

The system detects that the question is version-dependent but no version was provided.

Instead of assuming the latest version, VersionQuery asks:

> Which API version are you using? (e.g. 2022-06-28)

Once the developer provides the version, retrieval continues using that version.

### 3. Diagnostic Question

The developer asks:

> Why is my database query returning an empty result when it worked yesterday?

The system:

1. Classifies the question as `diagnostic`.
2. Extracts the currently relevant version if specified.
3. Searches the changelog and API reference in parallel.
4. Grades the retrieved documents.
5. Compares the relevant reference behavior with documented changes.
6. Generates a synthesized explanation.
7. Cites the relevant changelog and API reference sections.

For example, the answer may identify a documented behavior change in a changelog entry and explain how it affects the API reference behavior.

### 4. Migration Question — Multi-Hop Retrieval

The developer asks:

> How do I upgrade from 2021-08-16 to 2022-06-28?

The system:

1. Classifies the question as `migration`.
2. Extracts `from_version = 2021-08-16`.
3. Extracts `to_version = 2022-06-28`.
4. Identifies the required version hops.
5. Retrieves the relevant migration guide for each hop.
6. Synthesizes the guides into an ordered upgrade path.
7. Lists breaking changes in sequence.
8. Provides a citation for each change.

### 5. No Grounding Found — Honest Failure

If the documentation does not cover the question or the requested version does not exist:

1. Initial retrieval is performed.
2. Retrieved documents are graded.
3. If grading fails, the query is transformed.
4. Retrieval is retried.
5. The system allows a maximum of two retrieval attempts.
6. If grounding still cannot be established, the system responds:

> **Not found in docs for this version.**

VersionQuery never falls back to general knowledge or guesses.

## Features

### Core MVP Features

#### Query Understanding

Extracts:

* Intent: `reference`, `diagnostic`, or `migration`
* Version
* Document type
* `from_version` and `to_version` for migration queries

If a required version is missing and cannot be inferred, the system asks the developer for clarification.

#### Structure-Aware Ingestion

Documents are chunked according to their natural structure rather than arbitrary token windows.

| Document Type   | Chunking Unit       |
| --------------- | ------------------- |
| API Reference   | One endpoint        |
| Migration Guide | One discrete change |
| Changelog       | One release entry   |

Each chunk is tagged with metadata such as:

* `doc_type`
* `version`
* `from_version`
* `to_version`
* `breaking`
* `release_date`
* `endpoint`

#### Hybrid Retrieval

VersionQuery combines:

* Dense vector search
* BM25 keyword search
* Reciprocal Rank Fusion (RRF)

Hard filters for version and document type are applied **before scoring**.

This ensures that a highly similar chunk from the wrong API version cannot outrank a valid chunk from the requested version.

#### Document Grading

Retrieved chunks are evaluated using LLM-based multi-dimensional grading:

* Relevance
* Version correctness
* Document-type appropriateness

If grading fails, the system rewrites the query and retries retrieval, with a maximum of two attempts.

#### Multi-Hop Migration Handling

Migration questions can span multiple API versions.

VersionQuery decomposes cross-version migration requests into individual version hops, retrieves the relevant migration information for each hop, and synthesizes the results into an ordered upgrade path.

#### Grounded Generation

Answers are generated strictly from retrieved documentation.

The model is not allowed to fill missing information using general knowledge.

#### Verification

After generation, the system verifies that:

* The answer is supported by retrieved content.
* The answer does not mix API versions.
* The cited source actually supports the claims being made.

#### Citation

Every answer contains:

* Source document
* Section
* Version

The citation should allow the developer to independently verify the answer.

## Architecture

```text
                    ┌──────────────────────┐
                    │    Developer Query   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Query Understanding │
                    │                      │
                    │ • Intent             │
                    │ • Version            │
                    │ • Doc Type           │
                    │ • Migration Versions │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Route & Retrieve     │
                    │                      │
                    │ • Version Filter     │
                    │ • Doc-Type Filter   │
                    │ • BM25               │
                    │ • Dense Retrieval    │
                    │ • RRF                 │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Document Grading    │
                    │                      │
                    │ • Relevant?          │
                    │ • Correct Version?   │
                    │ • Correct Doc Type?  │
                    └──────────┬───────────┘
                               │
                  ┌────────────┴────────────┐
                  │                         │
             Relevant                  Not Relevant
                  │                         │
                  ▼                         ▼
       ┌──────────────────┐       ┌──────────────────┐
       │ Generate Answer  │       │ Transform Query  │
       │                  │       │                  │
       │ Strictly from    │       │ Retry Retrieval  │
       │ retrieved text   │       │ Maximum 2 times  │
       └────────┬─────────┘       └────────┬─────────┘
                │                          │
                │                    Still Fails
                │                          │
                │                          ▼
                │                ┌──────────────────┐
                │                │   NOT FOUND      │
                │                │                  │
                │                │ "Not found in    │
                │                │ docs for this    │
                │                │ version"         │
                │                └──────────────────┘
                │
                ▼
       ┌──────────────────────┐
       │ Verify & Cite        │
       │                      │
       │ • Grounding Check    │
       │ • Version Check      │
       │ • Source Citation    │
       └──────────┬───────────┘
                  │
                  ▼
       ┌──────────────────────┐
       │     Final Answer     │
       └──────────────────────┘
```

## Key Design Decisions

### Hard Version Filtering Before Scoring

Version correctness is more important than semantic similarity.

A semantically similar chunk from the wrong API version can produce an incorrect answer. Therefore, version and document-type filters are applied before retrieval results are ranked.

### No Web Search Fallback

VersionQuery intentionally does not use web search or general knowledge as a fallback.

The core promise of the system is:

> Answers come from the vendor's documentation and can be verified against the cited source.

A web-search fallback would weaken this guarantee.

### Capped Retry Loop

Retrieval failures trigger query transformation and another retrieval attempt, but retries are capped at two attempts.

This prevents uncontrolled retrieval loops and prioritizes an honest **"not found"** response over an unsupported answer.

### Structure-Aware Chunking

Documentation is not treated as arbitrary text.

Endpoints, migration changes, and changelog entries are naturally meaningful units, so the ingestion pipeline preserves those boundaries and attaches type-specific metadata.

## Tech Stack

| Layer            | Technology                      | Reason                                           |
| ---------------- | ------------------------------- | ------------------------------------------------ |
| Data Source      | Notion API Docs                 | Real, public, versioned documentation            |
| Chunking         | Python rule-based parser        | Preserves natural document boundaries            |
| Dense Embeddings | BGE-small-en / all-MiniLM-L6-v2 | Free and locally executable                      |
| Sparse Retrieval | rank_bm25                       | Simple and lightweight                           |
| Vector Store     | Chroma                          | Local, free, metadata filtering                  |
| Hybrid Retrieval | Reciprocal Rank Fusion          | Simple combination of dense + sparse retrieval   |
| LLM              | Claude / GPT-4o-mini class      | Understanding, grading, generation, verification |
| Orchestration    | LangGraph                       | Conditional graph and retry flow                 |
| Backend          | FastAPI                         | Lightweight and fast to implement                |
| Frontend         | Streamlit                       | Fastest option for a usable demo                 |

## Data Model

A simplified representation of an indexed document chunk:

```json
{
  "text": "Document chunk content...",
  "metadata": {
    "doc_type": "api_reference",
    "version": "2022-06-28",
    "endpoint": "POST /v1/databases/{database_id}/query",
    "section": "Query a database",
    "source_document": "Query a database"
  }
}
```

Migration chunks may contain:

```json
{
  "text": "Migration change...",
  "metadata": {
    "doc_type": "migration",
    "from_version": "2021-08-16",
    "to_version": "2022-06-28",
    "breaking": true,
    "section": "Database query changes",
    "source_document": "Upgrade Guide"
  }
}
```

Changelog chunks may contain:

```json
{
  "text": "Release change...",
  "metadata": {
    "doc_type": "changelog",
    "version": "2022-06-28",
    "release_date": "2022-06-28",
    "section": "Database APIs",
    "source_document": "Changelog"
  }
}
```

## Retrieval Strategy

VersionQuery uses hybrid retrieval:

```text
                    User Query
                        │
              ┌─────────┴─────────┐
              │                   │
              ▼                   ▼
        Dense Retrieval       BM25 Retrieval
              │                   │
              └─────────┬─────────┘
                        │
                        ▼
             Reciprocal Rank Fusion
                        │
                        ▼
             Retrieved Candidates
                        │
                        ▼
          Version + Doc-Type Filtering
                        │
                        ▼
                Document Grading
```

The critical constraint is that version and document-type correctness must be enforced rather than relying only on ranking.

## Migration Retrieval

Migration questions require multi-hop reasoning.

For example:

```text
2021-08-16
     │
     ▼
Migration Guide
     │
     ▼
2022-06-28
     │
     ▼
Migration Guide
     │
     ▼
Next Version
     │
     ▼
...
     │
     ▼
Target Version
```

Each hop is retrieved independently and then synthesized into a single ordered response.

## Evaluation Metrics

The primary evaluation will use a hand-labeled test set containing approximately 20–30 question/version/expected-source triples.

### Retrieval & Correctness

| Metric                   | Description                                                          |
| ------------------------ | -------------------------------------------------------------------- |
| Version Correctness Rate | Percentage of answers sourced from the correct API version           |
| Citation Accuracy        | Percentage of citations pointing to the correct document and section |
| Retrieval Hit Rate       | Percentage of questions where a relevant chunk was retrieved         |

### Groundedness

| Metric             | Description                                                                                            |
| ------------------ | ------------------------------------------------------------------------------------------------------ |
| Hallucination Rate | Percentage of answers flagged by verification as unsupported by their cited source                     |
| Not-Found Honesty  | Percentage of unsupported questions correctly rejected instead of answered with fabricated information |

### Usability

* Response latency target: a few seconds rather than tens of seconds
* Qualitative feedback from the final presentation and demo

## Out of Scope

The following are explicitly not part of the MVP:

* Web search fallback
* General-knowledge answers
* Multi-vendor support
* Real-time documentation synchronization
* Cross-encoder reranking
* Multi-query fan-out
* RAG-Fusion
* User accounts
* Authentication
* Multi-tenant usage
* Production-scale infrastructure optimization
* Production-scale latency optimization

## Risks & Assumptions

### Assumption: Notion is Representative

Notion's documentation structure is assumed to be representative enough to demonstrate the core version-aware retrieval problem.

It provides API references, changelogs, and upgrade information while remaining small enough to ingest and process within the sprint.

### Risk: LLM Grading and Verification Latency

Using an LLM for grading and verification adds latency and potentially increases model usage.

Mitigation:

* Use one small/fast model across the pipeline.
* Limit retrieval retries to two attempts.
* Keep retrieved context focused.

### Risk: Structure-Aware Parsing Complexity

Different document types require different parsing logic.

Mitigation:

* Scope the ingestion logic to Notion's actual documentation structure.
* Use rule-based parsing.
* Chunk around natural documentation boundaries.

## Example Interaction

**Developer:**

> How do I query a database in Notion-Version 2022-06-28?

**VersionQuery:**

> You can query a database using the database query endpoint for Notion API version 2022-06-28.
>
> **Source:** Notion API Reference
> **Section:** Query a database
> **Version:** 2022-06-28

The exact response is generated from the retrieved source content rather than from the model's general knowledge.

## Core Principle

VersionQuery follows one central rule:

> **If the system cannot ground an answer in the correct version of the vendor's documentation, it does not answer.**

This makes version correctness, source verification, and honest failure more important than maximizing the number of questions answered.

## Project Goal

By the end of the sprint, the team should have a working demonstration showing that VersionQuery can:

1. Understand version-specific developer questions.
2. Retrieve only documentation relevant to the requested version.
3. Handle reference, diagnostic, and migration questions.
4. Perform multi-hop migration retrieval.
5. Reject unsupported questions instead of guessing.
6. Generate answers grounded exclusively in retrieved documentation.
7. Verify generated answers.
8. Provide exact, verifiable citations.
9. Demonstrate measurable improvements in version correctness and citation accuracy on a labeled test set.
