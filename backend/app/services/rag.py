"""
RAG retrieval service — Phase 3.

Embeds a user query and searches their ChromaDB collection for the most
semantically relevant document chunks stored during Phase 2 processing.

Distance threshold: cosine distance < 0.3  (= cosine similarity > 0.7)
Chunks above 0.3 are too far off-topic to be useful context.

Metadata dependency on Phase 2:
  document_processor.py must store these fields in ChromaDB metadata per chunk:
    - document_id:  UUID string
    - source:       original filename, e.g. "quarterly_report.pdf"
    - owner_id:     user UUID string
    - chunk_index:  integer position within the document

ChromaDB HTTP client is synchronous. All collection calls are wrapped in
run_in_executor so they don't block the async event loop.
"""
import asyncio
import logging
from functools import partial
from typing import Any

from app.services.chroma import get_or_create_user_collection
from app.services.embedding import generate_embeddings

logger = logging.getLogger(__name__)


async def retrieve_context(
    user_id: str,
    query: str,
    n_results: int = 5,
    distance_threshold: float = 0.7,
) -> list[dict[str, Any]]:
    """
    Find the top semantically relevant chunks for a query from the user's documents.

    Args:
        user_id:            string UUID — selects the user's ChromaDB collection.
        query:              the user's natural language question.
        n_results:          number of candidates to fetch before threshold filtering.
        distance_threshold: cosine distance cutoff. Chunks above this are discarded.

    Returns:
        List of dicts: content, source, document_id, distance, chunk_index.
        Returns [] when collection is empty, query fails, or no chunk passes threshold.

    Why we check count() before query():
        ChromaDB raises an exception when n_results > number of documents in the
        collection. For small documents (few chunks) this is very common. The old
        code caught this exception silently and returned [], making every RAG query
        appear to find nothing — no error in logs, no visible failure, just the
        "not found" fallback message every time.
    """
    loop = asyncio.get_event_loop()

    # Embed the query — same model (all-MiniLM-L6-v2) used at ingest time
    query_embeddings = await generate_embeddings([query])
    query_vector = query_embeddings[0]

    # Get the user's collection
    collection = await get_or_create_user_collection(user_id)

    # Check how many chunks are actually stored before querying.
    # ChromaDB raises if n_results > collection size — we cap it here.
    try:
        count = await loop.run_in_executor(None, collection.count)
    except Exception as exc:
        logger.error("ChromaDB count() failed for user %s: %s", user_id, exc)
        return []

    if count == 0:
        logger.debug("ChromaDB collection is empty for user %s", user_id)
        return []

    # Cap n_results to what actually exists — avoids the n_results > count crash
    actual_n = min(n_results, count)

    # Query ChromaDB — synchronous HTTP call, wrapped in thread pool
    query_fn = partial(
        collection.query,
        query_embeddings=[query_vector],
        n_results=actual_n,
        include=["documents", "metadatas", "distances"],
    )
    try:
        results = await loop.run_in_executor(None, query_fn)
    except Exception as exc:
        logger.error("ChromaDB query() failed for user %s: %s", user_id, exc)
        return []

    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    # Log distances so threshold tuning is visible if retrieval still looks wrong
    logger.debug(
        "ChromaDB returned %d results for user %s. Distances: %s. Threshold: %s",
        len(distances),
        user_id,
        [round(d, 4) for d in distances],
        distance_threshold,
    )

    chunks = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        if distance <= distance_threshold:
            chunks.append(
                {
                    "content": text,
                    "source": metadata.get("source", "Unknown"),
                    "document_id": metadata.get("document_id", ""),
                    "distance": round(distance, 4),
                    "chunk_index": int(metadata.get("chunk_index", 0)),
                }
            )

    logger.debug(
        "%d of %d chunks passed distance threshold %.2f for user %s",
        len(chunks),
        len(distances),
        distance_threshold,
        user_id,
    )

    return chunks