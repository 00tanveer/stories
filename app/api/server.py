from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.services.retrieval import Retriever
from app.services.podcasts import get_podcasts_by_category, get_podcast_by_id
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from posthog import Posthog, new_context, identify_context, set_context_session
import time
import logging
import json
from pathlib import Path
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# ---- Initialize the Retriever (lazy-loaded singleton)

retriever = None

def get_retriever():
    """Lazy load the retriever only when needed."""
    global retriever
    if retriever is None:
        logger.info("🔄 Initializing Retriever for the first time (this may take 30-60 seconds)...")
        retriever = Retriever()
        logger.info("✅ Retriever initialized successfully!")
    return retriever


# ---- Request/Response Models ----
class QueryRequest(BaseModel):
    # Core search inputs
    query: str
    top_k: int = 20

    # Data-rich context (optional; populated at route layer from FastAPI Request)
    user_id: str | None = None
    session_id: str | None = None
    path: str | None = None
    method: str | None = None
    client_ip: str | None = None
    user_agent: str | None = None
    timestamp_ms: int | None = None

# ---- Routes ----
@app.get("/")
def root():
    return {"message": "Stories Indexer API is live 🚀"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/pods/{genre}")
async def get_podcasts_by_genre(genre: str, page: int = 1, page_size: int = 20):
    """Get podcasts by genre with pagination from PostgreSQL."""
    try:
        result = await get_podcasts_by_category(genre, page, page_size)
        
        return {
            "genre": genre,
            "page": result["page"],
            "page_size": result["page_size"],
            "total": result["total"],
            "total_pages": result["total_pages"],
            "podcasts": result["podcasts"]
        }
    except Exception as e:
        logger.error(f"Error fetching podcasts for genre {genre}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pods/{genre}/{feed_id}")
async def get_podcast_by_id_route(genre: str, feed_id: str):
    """Get a single podcast by genre and feedId from PostgreSQL."""
    try:
        podcast = await get_podcast_by_id(feed_id)
        
        if not podcast:
            raise HTTPException(status_code=404, detail=f"Podcast with feedId '{feed_id}' not found")
        
        return podcast
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching podcast {feed_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/episodes/{feed_id}")
async def get_episodes(feed_id: str, limit: int = 50, offset: int = 0):
    """Get episodes for a specific podcast feed ID."""
    try:
        from app.services.episodes import get_episodes_by_podcast_id
        
        episodes = await get_episodes_by_podcast_id(feed_id, limit=limit, offset=offset)
        
        return {
            "feed_id": feed_id,
            "total": len(episodes),
            "episodes": episodes
        }
    except Exception as e:
        logger.error(f"Error fetching episodes for podcast {feed_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search(request: QueryRequest, req: Request):
    """Perform a semantic search against indexed questions."""
    try:
        # Enrich the request model with HTTP context for downstream services/analytics
        request.path = str(req.url.path)
        request.method = req.method
        request.session_id = req.headers.get("X-POSTHOG-SESSION-ID")
        request.user_id = req.headers.get("X-User-ID", req.client.host)
        request.client_ip = req.client.host if req.client else None
        request.user_agent = req.headers.get("User-Agent")
        request.timestamp_ms = int(time.time() * 1000)

        results = get_retriever().hybrid_search(request.query, top_k=request.top_k)
        return {
            "query": request.query,
            "context": {
                "path": request.path,
                "method": request.method,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "client_ip": request.client_ip,
                "user_agent": request.user_agent,
                "timestamp_ms": request.timestamp_ms,
            },
            "results": results,
        }
    except Exception as e:
        print(e)
        logger.error(f"Search error: {e}")
        # Use enriched request context for error analytics
        posthog.capture_exception(
            e,
            properties={
                "path": request.path or str(req.url.path),
                "method": request.method or req.method,
                "user_id": request.user_id,
                "session_id": request.session_id,
                "client_ip": request.client_ip,
                "user_agent": request.user_agent,
                "timestamp_ms": request.timestamp_ms,
            },
        )
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
