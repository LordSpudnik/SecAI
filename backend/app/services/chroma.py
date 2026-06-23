"""
ChromaDB client singleton and collection helpers.

ChromaDB answers one question efficiently: "given this query vector, what are
the N most similar vectors I've stored?" This is vector similarity search.

We configure every collection to use cosine distance, which measures the angle
between two vectors. Distance 0 = identical meaning. Distance 1 = unrelated.

This resolves the PRD conflict: cosine_distance = 1 - cosine_similarity,
so distance < 0.3 and similarity > 0.7 are the same threshold.
The threshold is enforced in Phase 3 (RAG retrieval), not here.

Per-user isolation: each user gets their own collection named user_{user_id}.
Every stored chunk also has owner_id in its metadata as a second guard —
queries in Phase 3 will always filter by owner_id even within a single collection.
"""
import asyncio
from functools import partial

import chromadb

from app.core.config import settings

from typing import Any

_client: Any | None = None


def load_chroma_client() -> chromadb.HttpClient:
    """Initialize the ChromaDB HTTP client singleton. Call once at startup."""
    global _client
    _client = chromadb.HttpClient(
        host=settings.CHROMADB_HOST,
        port=settings.CHROMADB_PORT,
    )
    return _client


def get_chroma_client() -> chromadb.HttpClient:
    """Return the already-initialized client. Raises if called before load_chroma_client()."""
    if _client is None:
        raise RuntimeError("ChromaDB client not initialized. Call load_chroma_client() at startup.")
    return _client


def collection_name_for_user(user_id) -> str:
    """
    Build the ChromaDB collection name for a user.
    Format: user_{uuid_with_hyphens} — example: user_550e8400-e29b-41d4-a716-446655440000
    Length: 41 characters. ChromaDB allows 3-63 chars; hyphens are permitted.
    """
    return f"user_{user_id}"


async def get_or_create_user_collection(user_id):
    """
    Get the ChromaDB collection for a user, creating it if it doesn't exist.

    hnsw:space=cosine MUST be set at creation time — it cannot be changed later.
    If you delete and recreate a collection, you must pass this metadata again.

    chromadb.HttpClient is synchronous, so we wrap it in run_in_executor.
    """
    loop = asyncio.get_event_loop()
    client = get_chroma_client()
    name = collection_name_for_user(user_id)

    fn = partial(
        client.get_or_create_collection,
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    return await loop.run_in_executor(None, fn)


async def delete_document_chunks(user_id, document_id: str) -> None:
    """
    Remove all ChromaDB chunks for a specific document from the user's collection.

    ChromaDB's delete(where=...) filters by metadata. We stored document_id
    in each chunk's metadata during indexing — this deletes all of them in one call.

    Only called when processing_status is ready (collection guaranteed to exist).
    """
    loop = asyncio.get_event_loop()
    client = get_chroma_client()
    name = collection_name_for_user(user_id)

    try:
        get_fn = partial(client.get_collection, name=name)
        collection = await loop.run_in_executor(None, get_fn)

        del_fn = partial(collection.delete, where={"document_id": document_id})
        await loop.run_in_executor(None, del_fn)
    except Exception:
        # Collection doesn't exist — no vectors to clean up. Proceed silently.
        pass