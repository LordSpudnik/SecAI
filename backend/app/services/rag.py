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
from functools import partial
from typing import Any

from app.services.chroma import get_or_create_user_collection
from app.services.embedding import generate_embeddings


async def retrieve_context(
    user_id: str,
    query: str,
    n_results: int = 5,
    distance_threshold: float = 0.3,
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
    """
    loop = asyncio.get_event_loop()

    # Embed the query — same model (all-MiniLM-L6-v2) used at ingest time
    query_embeddings = await generate_embeddings([query])
    query_vector = query_embeddings[0]

    # Get the user's collection
    collection = await get_or_create_user_collection(user_id)

    # Query ChromaDB — synchronous HTTP call, wrapped in thread pool
    # Exception guard handles: empty collection, n_results > collection size, network error
    query_fn = partial(
        collection.query,
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
    try:
        results = await loop.run_in_executor(None, query_fn)
    except Exception:
        return []

    if not results or not results.get("ids") or not results["ids"][0]:
        return []

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

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

    return chunks