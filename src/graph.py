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

from src.messages import (
    GENERATION_ERROR_MESSAGE,
    RETRIEVAL_ERROR_MESSAGE,
    ROUTING_ERROR_MESSAGE,
    UNDERSTANDING_ERROR_MESSAGE,
    VERIFICATION_ERROR_MESSAGE,
)


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
        state["message"] = UNDERSTANDING_ERROR_MESSAGE

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
        state["message"] = ROUTING_ERROR_MESSAGE

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
        state["message"] = RETRIEVAL_ERROR_MESSAGE

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
            state["status"] = generation_result.get(
                "status",
                "generation_error",
            )
            state["message"] = generation_result.get(
                "answer"
            ) or GENERATION_ERROR_MESSAGE
            return state

        state["status"] = "generated"
        state["message"] = (
            "Answer generated successfully from graded evidence."
        )

    except Exception:
        state["status"] = "generation_error"
        state["message"] = GENERATION_ERROR_MESSAGE

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

        state["status"] = verified_result.get(
            "status",
            "verification_failed",
        )

        state["message"] = (
            verification.get("reason")
            or VERIFICATION_ERROR_MESSAGE
        )

    except Exception:
        state["status"] = "verification_error"
        state["message"] = VERIFICATION_ERROR_MESSAGE

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

