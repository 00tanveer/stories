from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.services.retrieval import Retriever
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from posthog import Posthog, new_context, identify_context, set_context_session
import time

posthog = Posthog(
  project_api_key='phc_dZbOlokpJRnkDjyK8ZAyLRhcBlF5f4VSJwXLexQVaId',
  host='https://us.i.posthog.com',
  enable_exception_autocapture=True
)



app = FastAPI(title="Stories Search API", version="1.0")

# Enable frontend access (localhost dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Posthog middleway to track requests
@app.middleware("http")
async def posthog_middleware(request: Request, call_next):
    start_time = time.time()
    user_id = request.headers.get("X-User-ID", request.client.host)
    session_id = request.headers.get("X-POSTHOG-SESSION-ID")
    
    with new_context():
        identify_context(user_id)
        set_context_session(session_id)
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            if request.url.path != "/health":
                posthog.capture(
                    event="api_request",
                    properties={
                        "path": request.url.path,
                        "method": request.method,
                        "status_code": response.status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "success": True
                    }
                )
            
            return response
        except Exception as e:
            duration = time.time() - start_time
            
            posthog.capture_exception(
                e,
                properties={
                    "path": request.url.path,
                    "method": request.method,
                    "duration_ms": round(duration * 1000, 2)
                }
            )
            raise
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
        posthog.capture_exception(error, 'user_distinct_id', properties=additional_properties)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
