from unittest.mock import patch

from src.graph import (
    build_graph,
    generate_node,
    retrieve_node,
    route_after_generation,
    route_after_retrieval,
    route_after_routing,
    route_after_understanding,
    route_after_verification,
    route_node,
    understand_node,
    verify_node,
)


# ---------------------------------------------------------------------------
# ROUTING EDGE CONTRACTS
# ---------------------------------------------------------------------------


def test_understanding_success_routes_to_route():
    assert route_after_understanding(
        {"status": "understood"}
    ) == "route"


def test_understanding_failure_stops_graph():
    assert route_after_understanding(
        {"status": "understanding_error"}
    ) == "end"


def test_routing_success_routes_to_retrieval():
    assert route_after_routing(
        {"status": "ready"}
    ) == "retrieve"


def test_routing_clarification_stops_graph():
    assert route_after_routing(
        {"status": "needs_clarification"}
    ) == "end"


def test_routing_not_found_stops_graph():
    assert route_after_routing(
        {"status": "not_found"}
    ) == "end"


def test_retrieval_success_routes_to_generation():
    assert route_after_retrieval(
        {"status": "found"}
    ) == "generate"


def test_retrieval_failure_stops_graph():
    assert route_after_retrieval(
        {"status": "not_found"}
    ) == "end"


def test_generation_success_routes_to_verification():
    assert route_after_generation(
        {"status": "generated"}
    ) == "verify"


def test_generation_failure_stops_graph():
    assert route_after_generation(
        {"status": "generation_error"}
    ) == "end"


def test_verification_success_ends_graph():
    assert route_after_verification(
        {"status": "ok"}
    ) == "end"


def test_verification_error_ends_graph():
    assert route_after_verification(
        {"status": "verification_error"}
    ) == "end"


# ---------------------------------------------------------------------------
# VERIFICATION RETRY ROUTING
# ---------------------------------------------------------------------------


def test_verification_evidence_issue_retries_retrieval():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "evidence_issue",
        "retrieval_attempts": 1,
    }

    assert route_after_verification(state) == "retrieve"


def test_verification_generation_issue_retries_generation():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "generation_issue",
        "generation_attempts": 1,
    }

    assert route_after_verification(state) == "generate"


def test_verification_evidence_retry_stops_at_limit():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "evidence_issue",
        "retrieval_attempts": 2,
    }

    assert route_after_verification(state) == "end"
    assert state["status"] == "verification_failed_final"


def test_verification_generation_retry_stops_at_limit():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "generation_issue",
        "generation_attempts": 2,
    }

    assert route_after_verification(state) == "end"
    assert state["status"] == "verification_failed_final"


def test_unknown_verification_failure_type_ends_graph():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "unknown",
    }

    assert route_after_verification(state) == "end"


# ---------------------------------------------------------------------------
# UNDERSTANDING NODE
# ---------------------------------------------------------------------------


def test_understand_node_success_updates_state():
    with patch(
        "src.graph.understand_query",
        return_value={
            "intent": "reference",
            "version": "2025-09-03",
        },
    ) as understand:
        state = {
            "question": "How do I search?",
            "history": [],
            "status": "starting",
        }

        result = understand_node(state)

    assert result["status"] == "understood"
    assert result["understood"]["intent"] == "reference"
    assert result["understood"]["version"] == "2025-09-03"
    understand.assert_called_once_with(
        "How do I search?",
        [],
    )


def test_understand_node_passes_history():
    history = [
        {
            "role": "user",
            "content": "I use 2025-09-03.",
        }
    ]

    with patch(
        "src.graph.understand_query",
        return_value={
            "intent": "reference",
            "version": "2025-09-03",
        },
    ) as understand:
        state = {
            "question": "What endpoint?",
            "history": history,
            "status": "starting",
        }

        understand_node(state)

    understand.assert_called_once_with(
        "What endpoint?",
        history,
    )


def test_understand_node_handles_error():
    with patch(
        "src.graph.understand_query",
        side_effect=RuntimeError("understanding failed"),
    ):
        state = {
            "question": "How?",
            "history": [],
            "status": "starting",
        }

        result = understand_node(state)

    assert result["status"] == "understanding_error"
    assert "message" in result


# ---------------------------------------------------------------------------
# ROUTING NODE
# ---------------------------------------------------------------------------


def test_route_node_ready_updates_state():
    with patch(
        "src.graph.route_query",
        return_value={
            "status": "ready",
            "version": "2025-09-03",
            "doc_types": ["reference"],
        },
    ):
        state = {
            "question": "How?",
            "understood": {
                "intent": "reference",
                "version": "2025-09-03",
            },
            "status": "understood",
        }

        result = route_node(state)

    assert result["status"] == "ready"
    assert result["routing"]["doc_types"] == ["reference"]


def test_route_node_clarification_updates_state():
    with patch(
        "src.graph.route_query",
        return_value={
            "status": "needs_clarification",
            "message": "Please provide a version.",
        },
    ):
        state = {
            "question": "How?",
            "understood": {
                "intent": "reference",
                "version": None,
            },
            "status": "understood",
        }

        result = route_node(state)

    assert result["status"] == "needs_clarification"
    assert result["message"] == "Please provide a version."


def test_route_node_not_found_updates_state():
    with patch(
        "src.graph.route_query",
        return_value={
            "status": "not_found",
        },
    ):
        state = {
            "question": "How?",
            "understood": {
                "intent": "reference",
                "version": "1900-01-01",
            },
            "status": "understood",
        }

        result = route_node(state)

    assert result["status"] == "not_found"


def test_route_node_does_nothing_before_understanding():
    with patch(
        "src.graph.route_query"
    ) as route:
        state = {
            "question": "How?",
            "understood": None,
            "status": "starting",
        }

        result = route_node(state)

    assert result["status"] == "starting"
    route.assert_not_called()


# ---------------------------------------------------------------------------
# RETRIEVAL NODE
# ---------------------------------------------------------------------------


def test_retrieve_node_does_nothing_before_ready():
    with patch(
        "src.graph.retrieve_and_grade"
    ) as retrieve:
        state = {
            "question": "How?",
            "understood": {
                "intent": "reference",
                "version": "2025-09-03",
            },
            "routing": {
                "version": "2025-09-03",
                "doc_types": ["reference"],
            },
            "status": "understood",
        }

        result = retrieve_node(
            state,
            None,
            None,
            [],
        )

    assert result["status"] == "understood"
    retrieve.assert_not_called()


def test_retrieve_node_requires_document_type():
    state = {
        "question": "How?",
        "understood": {
            "intent": "reference",
            "version": "2025-09-03",
        },
        "routing": {
            "version": "2025-09-03",
            "doc_types": [],
        },
        "status": "ready",
        "retrieval_attempts": 0,
    }

    result = retrieve_node(
        state,
        None,
        None,
        [],
    )

    assert result["retrieval_attempts"] == 0

    assert result["status"] == "retrieval_error"


def test_retrieve_node_handles_not_found():
    with patch(
        "src.graph.retrieve_and_grade",
        return_value={
            "status": "not_found",
            "message": "No evidence found.",
        },
    ):
        state = {
            "question": "Unknown question",
            "understood": {
                "intent": "reference",
                "version": "2025-09-03",
            },
            "routing": {
                "version": "2025-09-03",
                "doc_types": ["reference"],
            },
            "status": "ready",
            "retrieval_attempts": 0,
        }

        result = retrieve_node(
            state,
            None,
            None,
            [],
        )

    assert result["status"] == "not_found"
    assert result["message"] == "No evidence found."
    assert result["retrieval_attempts"] == 1


def test_retrieve_node_requires_chunks_when_grading_succeeds():
    with patch(
        "src.graph.retrieve_and_grade",
        return_value={
            "status": "found",
            "message": "Evidence found.",
            "chunks": [],
        },
    ):
        state = {
            "question": "How?",
            "understood": {
                "intent": "reference",
                "version": "2025-09-03",
            },
            "routing": {
                "version": "2025-09-03",
                "doc_types": ["reference"],
            },
            "status": "ready",
            "retrieval_attempts": 0,
        }

        result = retrieve_node(
            state,
            None,
            None,
            [],
        )

    assert result["status"] == "not_found"


def test_retrieve_node_success_preserves_graded_evidence():
    chunks = [
        {
            "chunk_id": "chunk-1",
            "text": "Use POST /pages.",
        }
    ]

    graded_result = {
        "status": "found",
        "message": "Evidence found.",
        "chunks": chunks,
        "search_query": "create page",
    }

    with patch(
        "src.graph.retrieve_and_grade",
        return_value=graded_result,
    ):
        state = {
            "question": "How do I create a page?",
            "understood": {
                "intent": "reference",
                "version": "2025-09-03",
            },
            "routing": {
                "version": "2025-09-03",
                "doc_types": ["reference"],
            },
            "status": "ready",
            "retrieval_attempts": 0,
        }

        result = retrieve_node(
            state,
            None,
            None,
            chunks,
        )

    assert result["status"] == "found"
    assert result["chunks"] == chunks
    assert result["graded_result"] == graded_result
    assert result["search_query"] == "create page"
    assert result["retrieval_attempts"] == 1


def test_retrieve_node_handles_retrieval_exception():
    with patch(
        "src.graph.retrieve_and_grade",
        side_effect=RuntimeError("retrieval failed"),
    ):
        state = {
            "question": "How?",
            "understood": {
                "intent": "reference",
                "version": "2025-09-03",
            },
            "routing": {
                "version": "2025-09-03",
                "doc_types": ["reference"],
            },
            "status": "ready",
            "retrieval_attempts": 0,
        }

        result = retrieve_node(
            state,
            None,
            None,
            [],
        )

    assert result["status"] == "retrieval_error"
    assert result["retrieval_attempts"] == 1


def test_migration_stops_at_graph_boundary():
    state = {
        "question": "How do I migrate?",
        "understood": {
            "intent": "migration",
            "from_version": "2021-08-16",
            "to_version": "2022-06-28",
        },
        "routing": {
            "version": None,
            "doc_types": ["migration"],
        },
        "status": "ready",
        "retrieval_attempts": 0,
    }

    result = retrieve_node(
        state,
        None,
        None,
        [],
    )

    assert result["status"] == "unsupported_graph_flow"
    assert "Migration hop execution" in result["message"]


# ---------------------------------------------------------------------------
# GENERATION NODE
# ---------------------------------------------------------------------------


def test_generate_node_does_nothing_before_found():
    with patch(
        "src.graph.generate_answer"
    ) as generate:
        state = {
            "question": "How?",
            "status": "ready",
        }

        result = generate_node(state)

    assert result["status"] == "ready"
    generate.assert_not_called()


def test_generate_node_receives_graded_result():
    graded_result = {
        "status": "found",
        "chunks": [
            {
                "chunk_id": "chunk-1",
                "text": "Evidence",
            }
        ],
    }

    generation_result = {
        "status": "found",
        "answer": "Use the endpoint.",
        "used_chunk_ids": ["chunk-1"],
    }

    with patch(
        "src.graph.generate_answer",
        return_value=generation_result,
    ) as generate:
        state = {
            "question": "How?",
            "graded_result": graded_result,
            "status": "found",
            "generation_attempts": 0,
        }

        result = generate_node(state)

    assert result["status"] == "generated"
    assert result["generation_result"] == generation_result
    assert result["generation_attempts"] == 1

    generate.assert_called_once_with(
        "How?",
        graded_result,
    )


def test_generate_node_handles_generation_failure():
    with patch(
        "src.graph.generate_answer",
        return_value={
            "status": "generation_error",
            "answer": "Generation failed.",
        },
    ):
        state = {
            "question": "How?",
            "graded_result": {
                "status": "found",
                "chunks": [],
            },
            "status": "found",
            "generation_attempts": 0,
        }

        result = generate_node(state)

    assert result["status"] == "generation_error"
    assert result["generation_attempts"] == 1


def test_generate_node_handles_exception():
    with patch(
        "src.graph.generate_answer",
        side_effect=RuntimeError("generation failed"),
    ):
        state = {
            "question": "How?",
            "graded_result": {
                "status": "found",
                "chunks": [],
            },
            "status": "found",
            "generation_attempts": 0,
        }

        result = generate_node(state)

    assert result["status"] == "generation_error"
    assert result["generation_attempts"] == 1


# ---------------------------------------------------------------------------
# VERIFICATION NODE
# ---------------------------------------------------------------------------


def test_verify_node_does_nothing_before_generated():
    with patch(
        "src.graph.generate_verified_answer"
    ) as verify:
        state = {
            "question": "How?",
            "status": "found",
        }

        result = verify_node(state)

    assert result["status"] == "found"
    verify.assert_not_called()


def test_verify_node_success_produces_final_answer():
    verified_result = {
        "status": "ok",
        "answer": "Use POST /pages.",
        "citations": ["citation-1"],
        "used_chunk_ids": ["chunk-1"],
        "confidence": 0.95,
        "verification": {
            "verified": True,
        },
    }

    with patch(
        "src.graph.generate_verified_answer",
        return_value=verified_result,
    ) as verify:
        state = {
            "question": "How?",
            "graded_result": {
                "status": "found",
                "chunks": [
                    {
                        "chunk_id": "chunk-1",
                        "text": "Evidence",
                    }
                ],
            },
            "generation_result": {
                "status": "found",
                "answer": "Use POST /pages.",
                "used_chunk_ids": ["chunk-1"],
            },
            "status": "generated",
        }

        result = verify_node(state)

    assert result["status"] == "ok"
    assert result["answer"] == "Use POST /pages."
    assert result["citations"] == ["citation-1"]
    assert result["used_chunk_ids"] == ["chunk-1"]
    assert result["confidence"] == 0.95
    assert result["verification"]["verified"] is True

    verify.assert_called_once_with(
        query="How?",
        graded_result=state["graded_result"],
        generation_result=state["generation_result"],
    )


def test_verify_node_classifies_evidence_failure():
    verified_result = {
        "status": "verification_failed",
        "verification": {
            "verified": False,
            "failure_type": "evidence_issue",
            "reason": "Evidence does not support the answer.",
        },
        "confidence": 0.2,
    }

    with patch(
        "src.graph.generate_verified_answer",
        return_value=verified_result,
    ):
        state = {
            "question": "How?",
            "graded_result": {
                "status": "found",
                "chunks": [],
            },
            "generation_result": {
                "status": "found",
                "answer": "Unsupported answer.",
            },
            "status": "generated",
        }

        result = verify_node(state)

    assert result["status"] == "verification_failed"
    assert result["verification_failure_type"] == "evidence_issue"
    assert result["confidence"] == 0.2
    assert result["answer"] is not None if "answer" in result else True


def test_verify_node_classifies_generation_failure():
    verified_result = {
        "status": "verification_failed",
        "verification": {
            "verified": False,
            "failure_type": "generation_issue",
            "reason": "Generation needs to be retried.",
        },
        "confidence": 0.1,
    }

    with patch(
        "src.graph.generate_verified_answer",
        return_value=verified_result,
    ):
        state = {
            "question": "How?",
            "graded_result": {
                "status": "found",
                "chunks": [],
            },
            "generation_result": {
                "status": "found",
                "answer": "Answer.",
            },
            "status": "generated",
        }

        result = verify_node(state)

    assert result["status"] == "verification_failed"
    assert result["verification_failure_type"] == "generation_issue"


def test_verify_node_handles_exception():
    with patch(
        "src.graph.generate_verified_answer",
        side_effect=RuntimeError("verification failed"),
    ):
        state = {
            "question": "How?",
            "graded_result": {
                "status": "found",
                "chunks": [],
            },
            "generation_result": {
                "status": "found",
                "answer": "Answer.",
            },
            "status": "generated",
        }

        result = verify_node(state)

    assert result["status"] == "verification_error"


# ---------------------------------------------------------------------------
# FULL GRAPH CONTRACTS
# ---------------------------------------------------------------------------


def test_graph_stops_before_retrieval_on_clarification():
    with patch(
        "src.graph.understand_query",
        return_value={
            "intent": "reference",
            "version": None,
        },
    ), patch(
        "src.graph.route_query",
        return_value={
            "status": "needs_clarification",
            "message": "Please provide a version.",
        },
    ), patch(
        "src.graph.retrieve_and_grade"
    ) as retrieve:
        graph = build_graph(
            None,
            None,
            [],
        )

        result = graph.invoke(
            {
                "question": "How?",
                "history": [],
                "status": "starting",
                "generation_attempts": 0,
                "retrieval_attempts": 0,
            }
        )

    assert result["status"] == "needs_clarification"
    retrieve.assert_not_called()


def test_graph_stops_after_retrieval_not_found():
    with patch(
        "src.graph.understand_query",
        return_value={
            "intent": "reference",
            "version": "2025-09-03",
        },
    ), patch(
        "src.graph.route_query",
        return_value={
            "status": "ready",
            "version": "2025-09-03",
            "doc_types": ["reference"],
        },
    ), patch(
        "src.graph.retrieve_and_grade",
        return_value={
            "status": "not_found",
            "message": "No evidence found.",
        },
    ), patch(
        "src.graph.generate_answer"
    ) as generate:
        graph = build_graph(
            None,
            None,
            [],
        )

        result = graph.invoke(
            {
                "question": "Unknown question",
                "history": [],
                "status": "starting",
                "generation_attempts": 0,
                "retrieval_attempts": 0,
            }
        )

    assert result["status"] == "not_found"
    generate.assert_not_called()


def test_graph_reaches_generation_with_graded_evidence():
    graded_result = {
        "status": "found",
        "message": "Evidence found.",
        "chunks": [
            {
                "chunk_id": "chunk-1",
                "text": "Use POST /pages.",
            }
        ],
        "search_query": "create page",
    }

    generation_result = {
        "status": "found",
        "answer": "Use POST /pages.",
        "used_chunk_ids": ["chunk-1"],
    }

    with patch(
        "src.graph.understand_query",
        return_value={
            "intent": "reference",
            "version": "2025-09-03",
        },
    ), patch(
        "src.graph.route_query",
        return_value={
            "status": "ready",
            "version": "2025-09-03",
            "doc_types": ["reference"],
        },
    ), patch(
        "src.graph.retrieve_and_grade",
        return_value=graded_result,
    ), patch(
        "src.graph.generate_answer",
        return_value=generation_result,
    ) as generate, patch(
        "src.graph.generate_verified_answer",
        return_value={
            "status": "ok",
            "answer": "Use POST /pages.",
            "citations": ["citation"],
            "used_chunk_ids": ["chunk-1"],
            "confidence": 0.95,
            "verification": {
                "verified": True,
            },
        },
    ):
        graph = build_graph(
            None,
            None,
            [],
        )

        result = graph.invoke(
            {
                "question": "How do I create a page?",
                "history": [],
                "status": "starting",
                "generation_attempts": 0,
                "retrieval_attempts": 0,
            }
        )

    assert result["status"] == "ok"
    assert result["graded_result"] == graded_result
    assert result["generation_result"] == generation_result

    generate.assert_called_once_with(
        "How do I create a page?",
        graded_result,
    )


def test_graph_verification_evidence_issue_routes_back_to_retrieval():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "evidence_issue",
        "retrieval_attempts": 1,
    }

    assert route_after_verification(state) == "retrieve"


def test_graph_verification_generation_issue_routes_back_to_generation():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "generation_issue",
        "generation_attempts": 1,
    }

    assert route_after_verification(state) == "generate"


def test_graph_does_not_retry_retrieval_after_limit():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "evidence_issue",
        "retrieval_attempts": 2,
    }

    assert route_after_verification(state) == "end"
    assert state["status"] == "verification_failed_final"


def test_graph_does_not_retry_generation_after_limit():
    state = {
        "status": "verification_failed",
        "verification_failure_type": "generation_issue",
        "generation_attempts": 2,
    }

    assert route_after_verification(state) == "end"
    assert state["status"] == "verification_failed_final"


def test_graph_compiles():
    graph = build_graph(
        None,
        None,
        [],
    )

    assert graph is not None
    assert hasattr(graph, "invoke")