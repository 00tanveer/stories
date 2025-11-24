from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.retrieval import Retriever
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Stories Search API", version="1.0")

# Enable frontend access (localhost dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---- Initialize the Retriever (singleton)

retriever = Retriever()
# Try loading an existing index; fallback to rebuild


# ---- Request/Response Models ----
class QueryRequest(BaseModel):
    query: str
    top_k: int = 20

# ---- Routes ----
@app.get("/")
def root():
    return {"message": "Stories Indexer API is live 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/search")
def search(request: QueryRequest):
    """Perform a semantic search against indexed questions."""
    try:
        results = retriever.search(request.query, top_k=request.top_k)
        return {"query": request.query, "results": results}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
