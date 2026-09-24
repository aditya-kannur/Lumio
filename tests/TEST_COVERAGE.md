# Test coverage

These tests are based on the current README and current source tree.

- Query understanding: intent/version extraction, JSON parsing, one LLM call.
- Clarification/routing: reference, diagnostic, migration, missing-version, unknown intent.
- Ingestion: dataset manifest, migration/reference/changelog chunking.
- Retrieval: BM25, dense+BM25 fusion, hard version/doc-type filtering.
- Grading: relevance/version/doc-type checks, batching, chunk cap, retry budget, wrapper.
- Migration: hop sequencing, invalid ranges, global batch, explicit per-hop context.
- Generation: grounded prompt formatting, answer generation, citations.
- Verification: supported/unsupported verdicts and hallucination flagging.
- API/graph: clarification, not-found, answer, error, graph stop behavior.
- Dataset/evaluation: sample query file sanity.

One regression test intentionally asserts that clarification follow-ups preserve previous-question context. The current API only sends `question` to the graph, so that test is expected to fail until conversation memory/session context is implemented.
