from unittest.mock import patch
from fastapi.testclient import TestClient

import main
from src.graph import retrieve_node

def test_api_clarification_response_uses_standard_message():
    class G:
        def invoke(self,state): return {"status":"needs_clarification"}
    main._pipeline["graph"] = G()
    r=TestClient(main.app).post("/ask",json={"question":"How?"})
    assert r.status_code == 200
    assert r.json()["type"] == "clarification"

def test_api_not_found_response():
    class G:
        def invoke(self,state): return {"status":"not_found"}
    main._pipeline["graph"] = G()
    r=TestClient(main.app).post("/ask",json={"question":"x"})
    assert r.json()["type"] == "not_found"

def test_api_answer_response_includes_citations():
    class G:
        def invoke(self,state): return {"status":"ok","answer":"a","citations":["c"]}
    main._pipeline["graph"] = G()
    r=TestClient(main.app).post("/ask",json={"question":"x"})
    assert r.json()=={"type":"answer","answer":"a","citations":["c"]}

def test_api_backend_error_becomes_500_json():
    class G:
        def invoke(self,state): raise RuntimeError("boom")
    main._pipeline["graph"] = G()
    r=TestClient(main.app).post("/ask",json={"question":"x"})
    assert r.status_code == 500
    assert r.json()["type"] == "error"
    assert "boom" in r.json()["message"]

def test_graph_route_stops_before_generation_on_clarification():
    from src.graph import build_graph
    with patch("src.graph.understand_query",return_value={"intent":"reference","version":None}), patch("src.graph.generate_answer") as gen:
        graph=build_graph(None,None,[])
        result=graph.invoke({"question":"How?","status":"pending"})
    assert result["status"] == "needs_clarification"
    gen.assert_not_called()
