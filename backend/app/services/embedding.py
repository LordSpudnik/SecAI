"""
Embedding model singleton.

An embedding is a list of numbers (384 of them, for this model) that represents
the *meaning* of a piece of text. Two sentences with similar meaning will produce
similar number patterns — this is what makes semantic search work.

Why a singleton: the model is 80MB and takes ~2 seconds to load. Loading it
per request would be unusable. We load it once at startup and share it.

Why all-MiniLM-L6-v2:
  - 384 dimensions: small enough to store efficiently, large enough to capture meaning
  - Fast on CPU: ~1000 short sentences per second
  - Strong performance on semantic similarity benchmarks for its size
  - Fully local, no cloud, Apache 2.0 license
"""
import asyncio
from functools import partial

from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None


def load_embedding_model() -> SentenceTransformer:
    """
    Load the model into memory. Call this once in the lifespan startup.
    On first run, downloads the model from HuggingFace (~80MB).
    Subsequent runs use the Docker volume cache at /root/.cache/huggingface.
    """
    global _model
    _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_embedding_model() -> SentenceTransformer:
    """Return the loaded singleton. Raises if called before load_embedding_model()."""
    if _model is None:
        raise RuntimeError("Embedding model not initialized. Call load_embedding_model() at startup.")
    return _model


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of text strings into 384-dimensional vectors.

    model.encode() is synchronous and CPU-bound — it runs a transformer neural
    network forward pass for each input. Calling it directly inside an async
    function would block the event loop: no other requests could be handled
    until encoding completes.

    run_in_executor hands this work to Python's thread pool and yields control
    back to the event loop until the result is ready.

    partial() pre-fills the keyword arguments so run_in_executor (which expects
    a zero-argument callable) can call it correctly.

    Returns: list of 384-float lists, one per input text, ready for ChromaDB.
    """
    model = get_embedding_model()
    loop = asyncio.get_event_loop()
    encode_fn = partial(model.encode, texts, batch_size=32, show_progress_bar=False)
    # .tolist() converts numpy array → Python list (ChromaDB requires native Python types)
    embeddings = await loop.run_in_executor(None, encode_fn)
    return embeddings.tolist()