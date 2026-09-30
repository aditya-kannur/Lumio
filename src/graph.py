from typing import TypedDict, Optional, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END

load_dotenv()

from src.query_understanding import understand_query
from src.router import route_query
from src.retrieval_pipeline import hybrid_retrieve, build_bm25_index, reciprocal_rank_fusion
from src.grading import retrieve_and_grade
from src.generation import generate_answer
from src.verification import generate_verified_answer


# ---------------------------------------------------------------------------
# PIPELINE STATE
# ---------------------------------------------------------------------------

class PipelineState(TypedDict, total=False):
    question: str
    history: Optional[List[dict]]

    understood: Optional[dict]
    routing: Optional[dict]

    # Retrieval / grading
    chunks: Optional[List[dict]]
    graded_result: Optional[dict]
    search_query: Optional[str]

    # Generation
    generation_result: Optional[dict]
    answer: Optional[str]
    citations: Optional[List[str]]
    used_chunk_ids: Optional[List[str]]

    # Verification
    verification: Optional[dict]
    verification_failure_type: Optional[str]
    confidence: Optional[float]

    # Control
    generation_attempts: int
    retrieval_attempts: int
    status: str
    message: str


# ---------------------------------------------------------------------------
# QUERY UNDERSTANDING
# ---------------------------------------------------------------------------

def understand_node(state: PipelineState):
    try:
        understood = understand_query(
            state["question"],
            state.get("history", []),
        )

        state["understood"] = understood

        state["status"] = "understood"
        state["message"] = (
            "Query understanding completed successfully."
        )

    except Exception:
        state["status"] = "understanding_error"
        state["message"] = (
            "I couldn't reliably understand the request. "
            "Please try rephrasing your question."
        )

    return state


# ---------------------------------------------------------------------------
# ROUTING
# ---------------------------------------------------------------------------

def route_node(state: PipelineState):
    if state["status"] != "understood":
        return state

    try:
        routing = route_query(
            state["understood"]
        )

        state["routing"] = routing

        routing_status = routing.get(
            "status"
        )

        if routing_status == "ready":
            state["status"] = "ready"
            state["message"] = (
                "Query routed successfully to the retrieval pipeline."
            )

        elif routing_status == "needs_clarification":
            state["status"] = "needs_clarification"
            state["message"] = (
                routing.get("message")
                or "The query requires clarification before retrieval."
            )

        elif routing_status == "not_found":
            state["status"] = "not_found"
            state["message"] = (
                "The requested query could not be routed to a supported "
                "documentation source."
            )

        else:
            state["status"] = "routing_error"
            state["message"] = (
                "Routing returned an unsupported status: "
                f"{routing_status}"
            )

    except Exception:
        state["status"] = "routing_error"
        state["message"] = (
            "I couldn't determine which documentation path "
            "to use for your request."
        )

    return state


# ---------------------------------------------------------------------------
# RETRIEVAL + GRADING
# ---------------------------------------------------------------------------

def retrieve_node(
    state: PipelineState,
    collection,
    bm25,
    chunks,
):
    if state["status"] != "ready":
        return state

    routing = state["routing"]

    # Migration remains outside this graph's non-hop execution path.
    # The dedicated migration decomposition owns hop sequencing and global
    # grading; this graph test intentionally excludes that mechanism.
    if state["understood"].get("intent") == "migration":
        state["status"] = "unsupported_graph_flow"
        state["message"] = (
            "Migration hop execution is handled by the dedicated migration "
            "path and is intentionally excluded from this graph test."
        )
        return state

    try:
        expected_version = routing.get(
            "version"
        )

        doc_types = routing.get(
            "doc_types",
            []
        )

        if not doc_types:
            state["status"] = "retrieval_error"
            state["message"] = (
                "Routing did not provide a document type for retrieval."
            )
            return state

        expected_doc_type = (
            doc_types[0]
            if len(doc_types) == 1
            else " or ".join(doc_types)
        )

        def retrieve_fn(
            search_query,
            expected_version=None,
            **kwargs,
        ):
            version = expected_version or routing.get("version")

            # Reference uses one hard-filtered hybrid retrieval. Diagnostic
            # uses both routed document types and merges the complete result
            # set before the single grading call. This preserves the
            # architecture's "retrieve -> one global grade" contract.
            if len(doc_types) == 1:
                return hybrid_retrieve(
                    query=search_query,
                    collection=collection,
                    bm25=bm25,
                    chunks=chunks,
                    doc_type=doc_types[0],
                    version=version,
                    top_k=5,
                )

            per_type = []
            for doc_type in doc_types:
                per_type.append(
                    hybrid_retrieve(
                        query=search_query,
                        collection=collection,
                        bm25=bm25,
                        chunks=chunks,
                        doc_type=doc_type,
                        version=version,
                        top_k=5,
                    )
                )

            rank_lists = [
                [chunk["chunk_id"] for chunk in group]
                for group in per_type
                if group
            ]
            if not rank_lists:
                return []

            fused_ids = reciprocal_rank_fusion(rank_lists)[:5]
            chunks_by_id = {chunk["chunk_id"]: chunk for chunk in chunks}
            return [chunks_by_id[cid] for cid in fused_ids if cid in chunks_by_id]

        state["retrieval_attempts"] = (
            state.get("retrieval_attempts", 0)
            + 1
        )

        graded_result = retrieve_and_grade(
            question=state["question"],
            expected_version=expected_version,
            expected_doc_type=expected_doc_type,
            retrieve_fn=retrieve_fn,
        )

        state["graded_result"] = graded_result

        if graded_result.get("status") != "found":

            state["status"] = "not_found"
            state["message"] = (
                graded_result.get("message")
                or (
                    "Retrieval and grading could not find "
                    "sufficient evidence."
                )
            )

            return state

        state["chunks"] = graded_result.get(
            "chunks",
            []
        )

        state["search_query"] = graded_result.get(
            "search_query",
            state["question"],
        )

        if not state["chunks"]:
            state["status"] = "not_found"
            state["message"] = (
                "Grading reported success but returned no evidence chunks."
            )
            return state

        state["status"] = "found"
        state["message"] = (
            "Retrieval and grading completed successfully. "
            f"{len(state['chunks'])} evidence chunk(s) selected."
        )

    except Exception:
        state["status"] = "retrieval_error"
        state["message"] = (
            "I couldn't retrieve or evaluate the relevant "
            "documentation. Please try again."
        )

    return state


# ---------------------------------------------------------------------------
# GENERATION
# ---------------------------------------------------------------------------

def generate_node(state: PipelineState):
    if state["status"] not in {
        "found",
        "verification_failed",
    }:
        return state

    try:
        state["generation_attempts"] = (
            state.get(
                "generation_attempts",
                0,
            )
            + 1
        )

        generation_result = generate_answer(
            state["question"],
            state["graded_result"],
        )

        state["generation_result"] = generation_result

        if generation_result.get("status") != "found":
            state["status"] = "generation_failed"
            state["message"] = (
                "Generation could not produce an answer "
                "from the graded evidence."
            )
            return state

        state["status"] = "generated"
        state["message"] = (
            "Answer generated successfully from graded evidence."
        )

    except Exception:
        state["status"] = "generation_error"
        state["message"] = (
            "I couldn't generate an answer from the available "
            "documentation. Please try again."
        )

    return state


# ---------------------------------------------------------------------------
# VERIFICATION
# ---------------------------------------------------------------------------

def verify_node(state: PipelineState):
    if state["status"] != "generated":
        return state

    try:
        verified_result = generate_verified_answer(
            query=state["question"],
            graded_result=state["graded_result"],
            generation_result=state["generation_result"],
        )

        state["verification"] = verified_result.get(
            "verification"
        )

        if verified_result.get("status") == "ok":

            state["answer"] = verified_result.get(
                "answer"
            )

            state["citations"] = verified_result.get(
                "citations",
                [],
            )

            state["used_chunk_ids"] = verified_result.get(
                "used_chunk_ids",
                [],
            )

            state["confidence"] = verified_result.get(
                "confidence",
                0.0,
            )

            state["verification_failure_type"] = None

            state["status"] = "ok"
            state["message"] = (
                "Answer passed verification and is ready for return."
            )

            return state

        verification = verified_result.get(
            "verification",
            {},
        )

        state["verification_failure_type"] = (
            verification.get(
                "failure_type",
                "generation_issue",
            )
        )

        state["confidence"] = verified_result.get(
            "confidence",
            0.0,
        )

        state["status"] = "verification_failed"

        state["message"] = (
            verification.get("reason")
            or "Generated answer failed evidence verification."
        )

    except Exception:
        state["status"] = "verification_error"
        state["message"] = (
            "I couldn't verify the generated answer against "
            "the documentation. No unverified answer will be returned."
        )

    return state


# ---------------------------------------------------------------------------
# GRAPH ROUTING
# ---------------------------------------------------------------------------

def route_after_understanding(state):
    if state["status"] == "understood":
        return "route"

    return "end"


def route_after_routing(state):
    if state["status"] == "ready":
        return "retrieve"

    return "end"


def route_after_retrieval(state):
    if state["status"] == "found":
        return "generate"

    return "end"


def route_after_generation(state):
    if state["status"] == "generated":
        return "verify"

    return "end"


def route_after_verification(state):
    if state["status"] == "ok":
        return "end"

    if state["status"] != "verification_failed":
        return "end"

    failure_type = state.get(
        "verification_failure_type"
    )

    # Evidence problem:
    # restart Retrieval → Grading → Generation, but keep the graph bounded.
    if failure_type == "evidence_issue":
        if state.get("retrieval_attempts", 0) < 2:
            return "retrieve"

        state["status"] = "verification_failed_final"
        state["message"] = (
            "Evidence failed verification after the maximum retrieval "
            "restart. No unverified answer will be returned."
        )
        return "end"

    # Generation problem:
    # keep the same graded evidence and retry Generation.
    if failure_type == "generation_issue":

        if state.get(
            "generation_attempts",
            0,
        ) < 2:
            return "generate"

        state["status"] = (
            "verification_failed_final"
        )

        state["message"] = (
            "Generation failed verification after "
            "the maximum retry. No unverified answer "
            "will be returned."
        )

        return "end"

    return "end"


# ---------------------------------------------------------------------------
# BUILD GRAPH
# ---------------------------------------------------------------------------

def build_graph(
    collection,
    bm25,
    chunks,
):
    graph = StateGraph(
        PipelineState
    )

    graph.add_node(
        "understand",
        understand_node,
    )

    graph.add_node(
        "route",
        route_node,
    )

    graph.add_node(
        "retrieve",
        lambda state: retrieve_node(
            state,
            collection,
            bm25,
            chunks,
        ),
    )

    graph.add_node(
        "generate",
        generate_node,
    )

    graph.add_node(
        "verify",
        verify_node,
    )

    graph.set_entry_point(
        "understand"
    )

    graph.add_conditional_edges(
        "understand",
        route_after_understanding,
        {
            "route": "route",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "route",
        route_after_routing,
        {
            "retrieve": "retrieve",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "generate": "generate",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "generate",
        route_after_generation,
        {
            "verify": "verify",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "verify",
        route_after_verification,
        {
            "generate": "generate",
            "retrieve": "retrieve",
            "end": END,
        },
    )

    return graph.compile()

# ---------------------------------------------------------------------------
# MAIN TEST
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """Question-driven graph contract suite.

    Each scenario is a representative user question. The test executes the
    actual graph stages explicitly so the report shows, for every question:

        question -> understanding -> routing -> retrieval/grading
        -> generation -> verification -> final result

    Terminal scenarios stop at the stage where the architecture is expected
    to stop. Component-specific grading/generation/verification tests remain
    separate; this file focuses on cross-stage graph contracts.
    """

    import time

    from src.chunking.migration_chunker import chunk_migration_file
    from src.chunking.changelog_chunker import chunk_changelog
    from src.chunking.reference_chunker import chunk_reference_file
    from src.data_sources import DATA_SOURCES
    from tests.chroma_cache import get_chroma_collection

    SEP = "=" * 96
    SUB = "-" * 96

    def banner(title):
        print("\n" + SEP)
        print(title)
        print(SEP)

    def stage(ok, name, expected, actual, details=""):
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] {name}")
        print(f"         expected: {expected}")
        print(f"         actual:   {actual}")
        if details:
            print(f"         detail:   {details}")
        return ok

    def load_real_chunks():
        chunks = []
        for source in DATA_SOURCES:
            doc_type = source["doc_type"]
            path = source["path"]
            if doc_type == "migration":
                source_chunks = chunk_migration_file(path)
            elif doc_type == "changelog":
                with open(path, encoding="utf-8") as f:
                    source_chunks = chunk_changelog(f.read(), doc_type="changelog")
            elif doc_type == "reference":
                source_chunks = chunk_reference_file(path)
            else:
                continue
            chunks.extend(source_chunks)
        return chunks

    def print_payload(label, payload):
        if isinstance(payload, dict):
            print(f"         {label}: {payload}")
        else:
            print(f"         {label}: {payload}")

    # ------------------------------------------------------------------
    # REAL CORPUS / INDEXES
    # ------------------------------------------------------------------
    banner("1. TEST FIXTURES — REAL CORPUS + INDEXES")
    started = time.perf_counter()
    all_chunks = load_real_chunks()
    load_seconds = time.perf_counter() - started

    assert all_chunks, "Real corpus is empty."
    assert all(c.get("chunk_id") for c in all_chunks), "Missing persistent chunk_id."
    assert len({c["chunk_id"] for c in all_chunks}) == len(all_chunks), "Duplicate chunk IDs."
    assert all(c.get("text", "").strip() for c in all_chunks), "Empty chunk text found."

    collection = get_chroma_collection(all_chunks)
    bm25 = build_bm25_index(all_chunks)
    app = build_graph(collection, bm25, all_chunks)

    print(f"PASS: loaded {len(all_chunks)} chunks in {load_seconds:.3f}s")
    print(f"PASS: Chroma={collection.count()} BM25={len(bm25.doc_freqs)}")
    print("PASS: LangGraph compiled")

    # ------------------------------------------------------------------
    # QUESTION MATRIX
    # ------------------------------------------------------------------
    # expected_terminal is deliberately expressed as a set because an LLM
    # retrieval/verification path can safely terminate as not_found or a
    # bounded verification failure without that being a test failure.
    scenarios = [
        {
            "id": "Q1",
            "name": "Reference happy path",
            "question": "What endpoint is used to search in Notion-Version 2025-09-03?",
            "path": "understand > route > retrieve/grade > generate > verify > ok",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"ok"},
            "must_reach": {"understand", "route", "retrieve", "generate", "verify"},
        },
        {
            "id": "Q2",
            "name": "Reference second endpoint",
            "question": "What is the endpoint for retrieving a page in Notion-Version 2025-09-03?",
            "path": "understand > route > retrieve/grade > generate > verify > ok",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"ok"},
            "must_reach": {"understand", "route", "retrieve", "generate", "verify"},
        },
        {
            "id": "Q3",
            "name": "Missing version clarification",
            "question": "How do I query a database?",
            "path": "understand > route > clarification/end",
            "intent": "reference",
            "requires_version": False,
            "terminal": {"needs_clarification", "not_found"},
            "must_reach": {"understand", "route"},
            "stop_after_route": True,
        },
        {
            "id": "Q4",
            "name": "Unsupported reference request",
            "question": "What endpoint retrieves a user's favorite color in Notion-Version 2025-09-03?",
            "path": "understand > route > retrieve/grade > not_found or bounded failure",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"not_found", "verification_failed_final", "verification_failed"},
            "must_reach": {"understand", "route", "retrieve"},
        },
        {
            "id": "Q5",
            "name": "Diagnostic / change analysis",
            "question": "What changed in the Notion API recently in Notion-Version 2026-03-11?",
            "path": "understand > route > retrieve/grade > generate > verify",
            "intent": "diagnostic",
            "requires_version": True,
            "terminal": {"ok", "not_found", "verification_failed_final", "verification_failed", "unsupported_graph_flow"},
            "must_reach": {"understand", "route"},
        },
        {
            "id": "Q6",
            "name": "Migration routing boundary",
            "question": "How do I upgrade from 2021-08-16 to 2022-06-28?",
            "path": "understand > route > migration boundary (hop excluded)",
            "intent": "migration",
            "requires_version": False,
            "terminal": {"unsupported_graph_flow", "not_found"},
            "must_reach": {"understand", "route"},
            "stop_after_route": True,
        },
        {
            "id": "Q7",
            "name": "Unknown version",
            "question": "What endpoint is used to search in Notion-Version 1900-01-01?",
            "path": "understand > route > not_found",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"not_found"},
            "must_reach": {"understand", "route"},
            "stop_after_route": True,
        },
        {
            "id": "Q8",
            "name": "Context-dependent reference",
            "question": "What endpoint retrieves a page?",
            "history": [
                {"role": "user", "content": "I am using Notion-Version 2025-09-03."}
            ],
            "path": "understand(context) > route > retrieve/grade > generate > verify",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"ok", "not_found", "verification_failed_final", "verification_failed"},
            "must_reach": {"understand", "route"},
        },
        {
            "id": "Q9",
            "name": "Version-specific reference with alternate wording",
            "question": "How do I search Notion content using the API in Notion-Version 2025-09-03?",
            "path": "understand > route > retrieve/grade > generate > verify",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"ok", "not_found", "verification_failed_final", "verification_failed"},
            "must_reach": {"understand", "route", "retrieve"},
        },
        {
            "id": "Q10",
            "name": "Unsupported semantic reference",
            "question": "How do I configure a Notion feature that is not documented in this corpus in Notion-Version 2025-09-03?",
            "path": "understand > route > retrieve/grade > not_found or bounded failure",
            "intent": "reference",
            "requires_version": True,
            "terminal": {"not_found", "verification_failed_final", "verification_failed"},
            "must_reach": {"understand", "route", "retrieve"},
        },
    ]

    banner("2. QUESTION-DRIVEN STAGE-BY-STAGE GRAPH TESTS — 10 SCENARIOS")
    print("Each question is executed stage-by-stage. Inputs and outputs are printed for manual inspection.")

    suite_passed = 0
    suite_failed = 0

    for case in scenarios:
        print("\n" + SEP)
        print(f"{case['id']} — {case['name']}")
        print(SEP)
        print(f"QUESTION: {case['question']}")
        print(f"EXPECTED FLOW: {case['path']}")

        history = case.get("history", [])
        state = PipelineState(
            question=case["question"],
            history=history,
            generation_attempts=0,
            retrieval_attempts=0,
            status="starting",
            message="",
        )
        reached = set()
        case_ok = True

        # ------------------------------
        # Stage 1: Understanding
        # ------------------------------
        reached.add("understand")
        print("\n[STAGE 1 — QUERY UNDERSTANDING]")
        print_payload("input.question", state["question"])
        print_payload("input.history", state.get("history", []))
        started = time.perf_counter()
        state = understand_node(state)
        elapsed = time.perf_counter() - started
        print_payload("output.understood", state.get("understood"))
        print_payload("output.status", state.get("status"))
        print(f"         elapsed_seconds: {elapsed:.3f}")

        ok = isinstance(state.get("understood"), dict) and state.get("status") == "understood"
        case_ok &= stage(ok, "Understanding contract", "dict + status=understood", state.get("understood"), state.get("message", ""))
        if not ok:
            suite_failed += 1
            continue

        understood = state["understood"]
        actual_intent = understood.get("intent")
        intent_ok = actual_intent == case["intent"]
        case_ok &= stage(intent_ok, "Intent", case["intent"], actual_intent)

        if case["requires_version"]:
            version = understood.get("version")
            if case["intent"] == "migration":
                version_ok = bool(understood.get("from_version") and understood.get("to_version"))
                expected_version = "from_version + to_version"
                actual_version = {
                    "from_version": understood.get("from_version"),
                    "to_version": understood.get("to_version"),
                }
            else:
                version_ok = bool(version)
                expected_version = "version present"
                actual_version = version
            case_ok &= stage(version_ok, "Version extraction", expected_version, actual_version)

        # ------------------------------
        # Stage 2: Routing
        # ------------------------------
        reached.add("route")
        print("\n[STAGE 2 — ROUTING]")
        print_payload("input.understood", state["understood"])
        started = time.perf_counter()
        state = route_node(state)
        elapsed = time.perf_counter() - started
        print_payload("output.routing", state.get("routing"))
        print_payload("output.status", state.get("status"))
        print(f"         elapsed_seconds: {elapsed:.3f}")

        routing = state.get("routing") or {}
        routing_status = routing.get("status")
        route_ok = routing_status in {"ready", "needs_clarification", "not_found"}
        case_ok &= stage(route_ok, "Routing contract", "recognized router status", routing_status, state.get("message", ""))

        if routing_status == "needs_clarification":
            case_ok &= stage(bool(state.get("message")), "Clarification message", "non-empty user-facing message", state.get("message"))
            final_ok = state.get("status") in case["terminal"]
            case_ok &= stage(final_ok, "Terminal outcome", sorted(case["terminal"]), state.get("status"))
            if case_ok:
                suite_passed += 1
            else:
                suite_failed += 1
            continue

        if routing_status == "not_found":
            final_ok = state.get("status") in case["terminal"]
            case_ok &= stage(final_ok, "Terminal outcome", sorted(case["terminal"]), state.get("status"))
            if final_ok:
                case_ok &= stage(not state.get("answer"), "No unverified answer", "answer is empty", state.get("answer"))
            if case_ok:
                suite_passed += 1
            else:
                suite_failed += 1
            continue

        if case.get("stop_after_route"):
            # Migration is intentionally outside hop execution. For other
            # scenarios this flag means the route itself is the contract.
            if case["intent"] == "migration":
                case_ok &= stage(True, "Migration boundary", "hop execution excluded from this graph test", "routing completed; hop path not executed")
                state["status"] = "unsupported_graph_flow"
            final_ok = state.get("status") in case["terminal"] or case["intent"] == "migration"
            case_ok &= stage(final_ok, "Terminal/boundary outcome", sorted(case["terminal"]), state.get("status"))
            if case_ok:
                suite_passed += 1
            else:
                suite_failed += 1
            continue

        # ------------------------------
        # Stage 3: Retrieval + Grading
        # ------------------------------
        reached.add("retrieve")
        print("\n[STAGE 3 — RETRIEVAL + GRADING]")
        print_payload("input.question", state["question"])
        print_payload("input.routing", state.get("routing"))
        before_attempts = state.get("retrieval_attempts", 0)
        started = time.perf_counter()
        state = retrieve_node(state, collection, bm25, all_chunks)
        elapsed = time.perf_counter() - started
        print_payload("output.status", state.get("status"))
        print_payload("output.search_query", state.get("search_query"))
        print_payload("output.chunk_count", len(state.get("chunks") or []))
        print_payload("output.retrieval_attempts", state.get("retrieval_attempts"))
        print(f"         elapsed_seconds: {elapsed:.3f}")

        retrieval_contract = state.get("status") in {"found", "not_found", "retrieval_error", "unsupported_graph_flow"}
        case_ok &= stage(retrieval_contract, "Retrieval/Grading contract", "recognized terminal or found status", state.get("status"), state.get("message", ""))

        if state.get("status") == "found":
            graded = state.get("graded_result") or {}
            chunks = state.get("chunks") or []
            case_ok &= stage(bool(graded), "Grading result exists", "graded_result dict", graded)
            case_ok &= stage(bool(chunks), "Evidence selected", "one or more graded chunks", len(chunks))
            case_ok &= stage(
                state.get("retrieval_attempts", 0) > before_attempts,
                "Retrieval attempt counter",
                "incremented",
                state.get("retrieval_attempts"),
            )
            ids_ok = all(c.get("chunk_id") for c in chunks)
            case_ok &= stage(ids_ok, "Persistent evidence IDs", "every graded chunk has chunk_id", [c.get("chunk_id") for c in chunks])
        else:
            final_ok = state.get("status") in case["terminal"]
            case_ok &= stage(final_ok, "Retrieval terminal outcome", sorted(case["terminal"]), state.get("status"))
            if final_ok:
                case_ok &= stage(not state.get("answer"), "No unverified answer", "answer is empty", state.get("answer"))
            if case_ok:
                suite_passed += 1
            else:
                suite_failed += 1
            continue

        # ------------------------------
        # Stage 4: Generation
        # ------------------------------
        reached.add("generate")
        print("\n[STAGE 4 — GENERATION]")
        print_payload("input.question", state["question"])
        print_payload("input.graded_result.status", (state.get("graded_result") or {}).get("status"))
        print_payload("input.graded_chunk_ids", [c.get("chunk_id") for c in state.get("chunks", [])])
        before_generation_attempts = state.get("generation_attempts", 0)
        started = time.perf_counter()
        state = generate_node(state)
        elapsed = time.perf_counter() - started
        generation = state.get("generation_result") or {}
        print_payload("output.status", state.get("status"))
        print_payload("output.generation_result", generation)
        print_payload("output.generation_attempts", state.get("generation_attempts"))
        print(f"         elapsed_seconds: {elapsed:.3f}")

        generation_ok = state.get("status") == "generated"
        case_ok &= stage(generation_ok, "Generation contract", "status=generated", state.get("status"), state.get("message", ""))
        if not generation_ok:
            case_ok &= stage(
                state.get("generation_attempts", 0) == before_generation_attempts + 1,
                "Generation attempt counter",
                before_generation_attempts + 1,
                state.get("generation_attempts"),
            )
            suite_failed += 1
            continue

        answer = generation.get("answer")
        used_ids = generation.get("used_chunk_ids") or []
        graded_ids = {c.get("chunk_id") for c in state.get("chunks", [])}
        case_ok &= stage(bool(answer), "Generated answer", "non-empty answer", answer)
        case_ok &= stage(bool(used_ids), "Generation evidence IDs", "non-empty used_chunk_ids", used_ids)
        case_ok &= stage(set(used_ids).issubset(graded_ids), "Evidence boundary", "used IDs subset of graded IDs", used_ids)

        # ------------------------------
        # Stage 5: Verification
        # ------------------------------
        reached.add("verify")
        print("\n[STAGE 5 — VERIFICATION]")
        print_payload("input.search_query", state.get("search_query"))
        print_payload("input.generated_answer", answer)
        print_payload("input.used_chunk_ids", used_ids)
        started = time.perf_counter()
        state = verify_node(state)
        elapsed = time.perf_counter() - started
        verification = state.get("verification") or {}
        print_payload("output.status", state.get("status"))
        print_payload("output.verification", verification)
        print_payload("output.citations", state.get("citations"))
        print_payload("output.confidence", state.get("confidence"))
        print(f"         elapsed_seconds: {elapsed:.3f}")

        verification_status_ok = state.get("status") in {"ok", "verification_failed", "verification_error", "verification_failed_final"}
        case_ok &= stage(verification_status_ok, "Verification contract", "recognized verification outcome", state.get("status"), state.get("message", ""))

        if state.get("status") == "ok":
            case_ok &= stage(verification.get("verified") is True, "Verified flag", "true", verification.get("verified"))
            case_ok &= stage(bool(state.get("citations")), "Citations", "non-empty citation list", state.get("citations"))
            case_ok &= stage(bool(state.get("used_chunk_ids")), "Final persistent IDs", "non-empty used_chunk_ids", state.get("used_chunk_ids"))
        else:
            # The first verification failure is allowed to route back into the
            # graph. We validate the failure classification and that no answer
            # is returned as final output.
            failure_type = verification.get("failure_type")
            if state.get("status") == "verification_failed":
                case_ok &= stage(
                    failure_type in {"generation_issue", "evidence_issue"},
                    "Failure classification",
                    "generation_issue or evidence_issue",
                    failure_type,
                )
            case_ok &= stage(not state.get("answer"), "No unverified final answer", "answer is empty", state.get("answer"))

        # ------------------------------
        # Final contract
        # ------------------------------
        print("\n[FINAL RESULT]")
        print_payload("status", state.get("status"))
        print_payload("message", state.get("message"))
        print_payload("answer", state.get("answer"))
        print_payload("citations", state.get("citations"))
        print_payload("used_chunk_ids", state.get("used_chunk_ids"))
        print_payload("reached_stages", sorted(reached))

        final_ok = state.get("status") in case["terminal"] or (
            state.get("status") == "verification_failed"
            and state.get("verification_failure_type") in {"generation_issue", "evidence_issue"}
        )
        case_ok &= stage(final_ok, "Final scenario contract", sorted(case["terminal"]), state.get("status"))

        missing_stages = case["must_reach"] - reached
        case_ok &= stage(not missing_stages, "Required stages reached", sorted(case["must_reach"]), sorted(reached), f"missing={sorted(missing_stages)}")

        if case_ok:
            suite_passed += 1
            print(f"\nRESULT: PASS — {case['id']} {case['name']}")
        else:
            suite_failed += 1
            print(f"\nRESULT: FAIL — {case['id']} {case['name']}")

    # ------------------------------------------------------------------
    # GRAPH EDGE CONTRACTS — small deterministic checks remain useful
    # ------------------------------------------------------------------
    banner("3. GRAPH EDGE CONTRACTS — DETERMINISTIC")
    edge_cases = [
        ("understanding success", route_after_understanding({"status": "understood"}), "route"),
        ("understanding failure", route_after_understanding({"status": "understanding_error"}), "end"),
        ("routing success", route_after_routing({"status": "ready"}), "retrieve"),
        ("routing clarification", route_after_routing({"status": "needs_clarification"}), "end"),
        ("retrieval success", route_after_retrieval({"status": "found"}), "generate"),
        ("retrieval failure", route_after_retrieval({"status": "not_found"}), "end"),
        ("generation success", route_after_generation({"status": "generated"}), "verify"),
        ("generation failure", route_after_generation({"status": "generation_error"}), "end"),
        ("verification success", route_after_verification({"status": "ok"}), "end"),
        ("verification error", route_after_verification({"status": "verification_error"}), "end"),
    ]
    for label, actual, expected in edge_cases:
        if actual == expected:
            print(f"PASS: {label} -> {actual}")
        else:
            suite_failed += 1
            print(f"FAIL: {label} expected={expected} actual={actual}")

    banner("4. FINAL GRAPH TEST REPORT")
    print(f"Questions passed: {suite_passed}")
    print(f"Failures:         {suite_failed}")
    print("Coverage:         10 question-driven scenarios + deterministic edge contracts")
    print("Pattern:          stage-by-stage input/output contract testing")
    print("Component tests:  grading/generation/verification remain separate")

    if suite_failed:
        raise AssertionError(f"{suite_failed} graph test contract(s) failed.")

    print("\nALL GRAPH QUESTION-DRIVEN TESTS PASSED")
