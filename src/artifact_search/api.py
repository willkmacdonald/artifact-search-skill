"""FastAPI backend for the artifact search skill."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from artifact_search.models import AppSource, Artifact, SearchResult
from artifact_search.search import ArtifactSearchEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global search engine instance
_search_engine: ArtifactSearchEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global _search_engine
    _search_engine = ArtifactSearchEngine()
    logger.info("Search engine initialized")
    yield
    if _search_engine:
        await _search_engine.close()
        logger.info("Search engine closed")


app = FastAPI(
    title="Artifact Search API",
    description="Multi-app artifact search for MedTech risk management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    """Search request from frontend."""

    query: str = Field(..., min_length=1, max_length=1000)
    context: dict[str, Any] | None = None


class ChatMessage(BaseModel):
    """Chat message for conversation history."""

    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    """Chat request with conversation history."""

    message: str = Field(..., min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    configured_sources: list[str]
    connections: dict[str, bool]


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health and connection status."""
    if not _search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    connections = await _search_engine.test_connections()
    sources = [s.value for s in _search_engine.get_configured_sources()]

    return HealthResponse(
        status="healthy",
        configured_sources=sources,
        connections=connections,
    )


@app.post("/search", response_model=SearchResult)
async def search(request: SearchRequest) -> SearchResult:
    """Search for artifacts across configured applications."""
    if not _search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        result = await _search_engine.search(request.query)
        return result
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Search failed: {str(e)}"
        ) from e


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, Any]:
    """Chat endpoint that searches and provides conversational responses."""
    if not _search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        # Search for relevant artifacts
        search_result = await _search_engine.search(request.message)

        # Build response with artifacts and summary
        response = {
            "message": search_result.summary or "Here's what I found:",
            "artifacts": [
                {
                    "id": a.id,
                    "source": a.source.value,
                    "type": a.artifact_type.value,
                    "title": a.title,
                    "content": a.content[:500] if a.content else "",
                    "url": a.url,
                }
                for a in search_result.artifacts[:10]
            ],
            "sources_searched": [s.value for s in search_result.sources_searched],
            "total_results": search_result.total_results,
        }

        return response

    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Chat failed: {str(e)}"
        ) from e


@app.get("/artifact/{source}/{artifact_id}", response_model=Artifact)
async def get_artifact(source: str, artifact_id: str) -> Artifact:
    """Get a specific artifact by source and ID."""
    if not _search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    try:
        app_source = AppSource(source)
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid source: {source}"
        ) from e

    artifact = await _search_engine.get_artifact(app_source, artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifact


@app.get("/sources")
async def get_sources() -> dict[str, list[str]]:
    """Get list of configured sources."""
    if not _search_engine:
        raise HTTPException(status_code=503, detail="Search engine not initialized")

    return {
        "configured": [s.value for s in _search_engine.get_configured_sources()],
        "available": [s.value for s in AppSource],
    }
