"""
FastAPI application entry point.

The lifespan context manager handles startup and shutdown:
- Startup: initialize Redis client, store on app.state so all routes can access it
- Shutdown: close Redis connection cleanly

Why app.state.redis instead of a module-level global:
Module-level async clients can cause issues with event loop lifetime in tests.
app.state is the FastAPI-idiomatic way to share resources across requests.
"""
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared resources on startup, clean up on shutdown."""
    # Startup
    app.state.redis = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,  # Return strings, not bytes
    )
    yield
    # Shutdown
    await app.state.redis.aclose()


app = FastAPI(
    title="SecAi",
    description="Private local AI assistant with RAG pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — open for local development, lock this down if ever deployed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/health")
async def health() -> dict:
    """Health check — confirms the server is running."""
    return {"status": "ok"}