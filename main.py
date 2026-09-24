from contextlib import asynccontextmanager
import traceback
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()

from src.retrieval_pipeline import load_all_chunks, build_chroma_collection, build_bm25_index
from src.graph import build_graph
from src.messages import CLARIFICATION_QUESTION, NOT_FOUND_MESSAGE

_pipeline: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading pipeline...")
    chunks = load_all_chunks()
    collection = build_chroma_collection(chunks)
    bm25 = build_bm25_index(chunks)
    graph = build_graph(collection, bm25, chunks, embed_model=None)
    _pipeline["graph"] = graph
    print("Ready.")
    yield


app = FastAPI(lifespan=lifespan)


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(req: AskRequest):
    try:
        result = _pipeline["graph"].invoke({"question": req.question, "status": "pending"})
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)  # visible in the backend terminal
        return JSONResponse(status_code=500, content={"type": "error", "message": str(e), "traceback": tb})

    if result["status"] == "needs_clarification":
        return {"type": "clarification", "message": CLARIFICATION_QUESTION}
    if result["status"] in ("not_found", "hallucination_flagged"):
        return {"type": "not_found", "message": NOT_FOUND_MESSAGE}

    return {"type": "answer", "answer": result["answer"], "citations": result.get("citations", [])}
