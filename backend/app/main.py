"""
FastAPI application entry point — Phase 3 update.

Startup initializes:
  - Redis client        (Phase 1) — token blacklist
  - ChromaDB client     (Phase 2) — vector search
  - Embedding model     (Phase 2) — all-MiniLM-L6-v2, loaded once into RAM
  - Ollama              (Phase 3) — no pre-load needed, ChatOllama connects on first call

Routers:
  /api/auth   — register, login, logout, /me
  /api/files  — upload, list, get, delete documents
  /api/chat   — threads CRUD, send message, SSE stream
"""
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, files
from app.routers import chat
from app.services.chroma import load_chroma_client
from app.services.embedding import load_embedding_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    load_chroma_client()
    load_embedding_model()
    yield
    await app.state.redis.aclose()


app = FastAPI(
    title="SecAI",
    description="Private local AI assistant with RAG pipeline",
    version="0.3.0",
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
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/health")
async def health() -> dict:
    from app.services.chroma import get_chroma_client
    try:
        get_chroma_client().heartbeat()
        chroma_status = "ok"
    except Exception as e:
        chroma_status = f"error: {e}"
    return {
        "status": "ok",
        "chromadb": chroma_status,
        "ollama_host": settings.OLLAMA_HOST,
        "ollama_model": settings.OLLAMA_MODEL,
    }