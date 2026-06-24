"""
Ollama LLM service — Phase 3.

Uses langchain-ollama (ChatOllama) for the Ollama HTTP integration.
astream() yields AIMessageChunk objects token-by-token.

Why a new ChatOllama per call:
  ChatOllama is a stateless config object — creating it per call is zero-cost.
  A module-level singleton would risk sharing state between concurrent streams.

Two stream functions:
  - stream_general: conversation mode, sends full message history for context
  - stream_rag:     RAG mode, injects numbered document context into the prompt

Both yield raw token strings. The caller (chat router) handles SSE formatting.
"""
from typing import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama

from app.core.config import settings

# ── System prompts ────────────────────────────────────────────────────────────

GENERAL_SYSTEM = (
    "You are SecAI, a helpful and precise AI assistant. "
    "Answer the user's question clearly and concisely. "
    "If you do not know something, say so — do not fabricate information."
)

RAG_SYSTEM = (
    "You are SecAI, an AI assistant that answers questions strictly from the "
    "provided document excerpts below.\n\n"
    "Rules:\n"
    "1. Answer ONLY using the context provided. Do not use outside knowledge.\n"
    "2. If the context does not contain enough information, respond with exactly: "
    "'I couldn't find relevant information in your documents.'\n"
    "3. Cite the source number your answer comes from (e.g. 'According to [1]...').\n"
    "4. Do not invent facts not present in the context."
)


def _get_llm() -> ChatOllama:
    """
    Build a ChatOllama instance pointing at the host Ollama server.
    temperature=0.7 — balanced between factual accuracy and readable prose.
    """
    return ChatOllama(
        base_url=settings.OLLAMA_HOST,
        model=settings.OLLAMA_MODEL,
        temperature=0.7,
    )


async def stream_general(
    history: list[dict],
    user_query: str,
) -> AsyncIterator[str]:
    """
    Stream a general LLM response with prior conversation history.

    Args:
        history: list of {"role": "user"|"assistant", "content": str}.
                 Must NOT include the current user message.
        user_query: the new user message.

    Yields:
        Raw token strings as Ollama generates them.
    """
    llm = _get_llm()

    messages = [SystemMessage(content=GENERAL_SYSTEM)]
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_query))

    async for chunk in llm.astream(messages):
        if isinstance(chunk.content, str) and chunk.content:
            yield chunk.content


async def stream_rag(
    context_chunks: list[dict],
    user_query: str,
) -> AsyncIterator[str]:
    """
    Stream a RAG response with numbered document context injected into the prompt.

    Args:
        context_chunks: list of dicts with keys: content, source, document_id, distance.
                        Comes from rag.retrieve_context(). Already filtered by threshold.
        user_query: the user's question.

    History is intentionally excluded from RAG mode — each question is answered
    from documents, not from prior conversation turns.

    Yields:
        Raw token strings as Ollama generates them.
    """
    llm = _get_llm()

    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        context_parts.append(f"[{i}] Source: {chunk['source']}\n\n{chunk['content']}")
    context_block = "\n\n---\n\n".join(context_parts)

    prompt = (
        f"{RAG_SYSTEM}\n\n"
        f"DOCUMENT CONTEXT:\n{context_block}\n\n"
        f"QUESTION: {user_query}\n\n"
        f"ANSWER:"
    )

    async for chunk in llm.astream([HumanMessage(content=prompt)]):
        if isinstance(chunk.content, str) and chunk.content:
            yield chunk.content