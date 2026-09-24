from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List
from dotenv import load_dotenv

load_dotenv()

from src.query_understanding import understand_query
from src.router import route_query
from src.retrieval_pipeline import hybrid_retrieve
from src.grading import retrieve_and_grade, retrieve_and_grade_batch
from src.migration_decomposition import decompose_and_retrieve
from src.generation import generate_answer
from src.verification import verify_answer


class PipelineState(TypedDict):
    question: str
    history: Optional[List[dict]]
    understood: Optional[dict]
    routing: Optional[dict]
    chunks: Optional[List[dict]]
    answer: Optional[str]
    citations: Optional[List[str]]
    status: str


def understand_node(state):
    state["understood"] = understand_query(
        state["question"],
        state.get("history", []),
    )
    return state


def route_node(state):
    state["routing"] = route_query(state["understood"])
    state["status"] = state["routing"]["status"]
    return state


def retrieve_node(state, collection, bm25, chunks):
    routing = state["routing"]

    def retrieve_fn(q, expected_version=None, **kw):
        return hybrid_retrieve(
            q,
            collection,
            bm25,
            chunks,
            doc_type=routing["doc_types"][0],
            version=expected_version or routing.get("version"),
        )

    if state["understood"]["intent"] == "migration":
        result = decompose_and_retrieve(
            routing["from_version"],
            routing["to_version"],
            lambda q, expected_version: retrieve_fn(
                q,
                expected_version,
            ),
        )

        all_chunks = [
            c
            for hop in result.get("hops", [])
            for c in hop["chunks"]
        ]

        state["chunks"] = all_chunks
        state["status"] = result["status"]

    else:
        result = retrieve_and_grade(
            state["question"],
            routing.get("version"),
            routing["doc_types"][0],
            retrieve_fn,
        )

        state["chunks"] = result.get("chunks", [])
        state["status"] = result["status"]

    return state


def generate_node(state):
    gen = generate_answer(
        state["question"],
        state["chunks"],
    )

    verdict = verify_answer(
        gen["answer"],
        state["chunks"],
    )

    if not verdict.get("supported") or verdict.get("version_mixed"):
        state["status"] = "hallucination_flagged"
        state["answer"] = None
        state["citations"] = []
    else:
        state["status"] = "ok"
        state["answer"] = gen["answer"]
        state["citations"] = gen["citations"]

    return state


def build_graph(collection, bm25, chunks, embed_model=None):
    graph = StateGraph(PipelineState)

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
        lambda s: retrieve_node(
            s,
            collection,
            bm25,
            chunks,
        ),
    )

    graph.add_node(
        "generate",
        generate_node,
    )

    graph.set_entry_point("understand")

    graph.add_edge(
        "understand",
        "route",
    )

    graph.add_conditional_edges(
        "route",
        lambda s: s["status"],
        {
            "ready": "retrieve",
            "needs_clarification": END,
            "not_found": END,
        },
    )

    graph.add_conditional_edges(
        "retrieve",
        lambda s: s["status"],
        {
            "found": "generate",
            "not_found": END,
        },
    )

    graph.add_edge(
        "generate",
        END,
    )

    return graph.compile()