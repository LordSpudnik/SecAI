"""
FastAPI application entry point — Phase 2 update.

Startup now initializes three shared resources:
  - Redis client        (Phase 1)
  - ChromaDB client     (Phase 2) — one shared HTTP connection to ChromaDB container
  - Embedding model     (Phase 2) — loads all-MiniLM-L6-v2 into RAM once (~2s, ~80MB)

The model download happens on first boot. Subsequent boots use the Docker volume cache.
"""
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, files
from app.services.chroma import load_chroma_client
from app.services.embedding import load_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all shared resources on startup. Clean up on shutdown."""
    app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    load_chroma_client()
    load_embedding_model()
    yield
    await app.state.redis.aclose()


app = FastAPI(
    title="SecAi",
    description="Private local AI assistant with RAG pipeline",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(files.router, prefix="/api/files", tags=["files"])


@app.get("/health")
async def health() -> dict:
    """Health check — verifies ChromaDB is reachable in addition to the server being up."""
    from app.services.chroma import get_chroma_client
    try:
        get_chroma_client().heartbeat()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {e}"
    return {"status": "ok", "chromadb": chroma_status}