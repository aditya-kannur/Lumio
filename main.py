from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse

from fastapi import FastAPI
from pydantic import BaseModel
import traceback

from src.retrieval_pipeline import (
    load_all_chunks,
    build_chroma_collection,
    build_bm25_index,
)

from src.graph import build_graph


class AskRequest(BaseModel):
    question: str
    session_id: str = "default"


_pipeline = {}

# In-memory conversation history.
# Each session has its own conversation.
_conversation_history = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    chunks = load_all_chunks()

    collection = build_chroma_collection(chunks)
    bm25 = build_bm25_index(chunks)

    graph = build_graph(
        collection=collection,
        bm25=bm25,
        chunks=chunks,
    )

    _pipeline["graph"] = graph
    _pipeline["chunks"] = chunks
    _pipeline["collection"] = collection
    _pipeline["bm25"] = bm25

    yield


app = FastAPI(lifespan=lifespan)


@app.post("/ask")
def ask(req: AskRequest):
    try:
        session_id = req.session_id

        history = _conversation_history.setdefault(
            session_id,
            [],
        )

        state = {
            "question": req.question,
            "status": "pending",
            "history": history.copy(),
        }

        result = _pipeline["graph"].invoke(state)

        history.append({
            "question": req.question,
            "response": result,
        })

        # Keep only the latest 10 exchanges.
        if len(history) > 10:
            del history[:-10]

        status = result.get("status")

        if status == "needs_clarification":
            return {
                "type": "clarification",
                "message": result.get("message"),
            }

        if status == "not_found":
            return {
                "type": "not_found",
                "message": result.get("message"),
            }

        if status in {"error", "failed"}:
            return {
                "type": "error",
                "message": result.get("message"),
            }

        return {
            "type": "answer",
            "answer": result.get("answer"),
            "citations": result.get("citations", []),
        }

    except Exception as exc:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "type": "error",
                "message": str(exc),
            },
        )