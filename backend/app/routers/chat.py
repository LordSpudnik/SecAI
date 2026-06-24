"""
Chat router — Phase 3.

Two-step streaming:
  Step 1 — POST /api/chat/threads/{id}/messages
    Saves the user message. Returns user_message_id and thread_id.
  Step 2 — GET  /api/chat/threads/{id}/stream?user_message_id=...&token=...
    Opens SSE connection. Streams Ollama tokens. Saves assistant message on done.

Why token in query param on the SSE endpoint:
  The browser's native EventSource API cannot send custom headers.
  Passing JWT as ?token=... is the standard workaround.
  Only safe over HTTPS — enforce that in Phase 4 Nginx config.

SSE event format:
  {"type": "token",   "content": "word"}
  {"type": "sources", "sources": [...]}   <- RAG only, after all tokens
  {"type": "done",    "message_id": "uuid"}
  {"type": "error",   "detail": "message"}

Why _run_stream creates its own DB session:
  StreamingResponse runs the generator after the route handler returns and its
  Depends(get_db) session closes. A dedicated AsyncSessionLocal() is explicit and safe.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import AsyncIterator

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal, get_db
from app.core.deps import get_current_user
from app.core.security import decode_token
from app.models.chat import ChatMessage, ChatMode, ChatThread, MessageRole
from app.models.user import User
from app.schemas.chat import (
    MessageOut,
    SendMessage,
    SendMessageResponse,
    ThreadCreate,
    ThreadOut,
    ThreadUpdate,
    ThreadWithMessages,
)
from app.services.llm import stream_general, stream_rag
from app.services.rag import retrieve_context

router = APIRouter()


# ─── Thread CRUD ──────────────────────────────────────────────────────────────


@router.post("/threads", response_model=ThreadOut, status_code=201)
async def create_thread(
    body: ThreadCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new chat thread. mode='rag' grounds answers in uploaded documents."""
    thread = ChatThread(
        id=uuid.uuid4(),
        owner_id=user.id,
        title=body.title,
        mode=body.mode,
    )
    db.add(thread)
    await db.flush()
    return thread


@router.get("/threads", response_model=list[ThreadOut])
async def list_threads(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all threads for the current user, most recently updated first."""
    result = await db.execute(
        select(ChatThread)
        .where(ChatThread.owner_id == user.id)
        .order_by(ChatThread.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/threads/{thread_id}", response_model=ThreadWithMessages)
async def get_thread(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a thread and its full message history, oldest message first."""
    thread = await _require_thread_owner(thread_id, user.id, db)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    return {
        "id": thread.id,
        "title": thread.title,
        "mode": thread.mode,
        "created_at": thread.created_at,
        "updated_at": thread.updated_at,
        "messages": messages,
    }


@router.patch("/threads/{thread_id}", response_model=ThreadOut)
async def update_thread(
    thread_id: uuid.UUID,
    body: ThreadUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rename a thread. Mode is immutable after creation."""
    thread = await _require_thread_owner(thread_id, user.id, db)
    if body.title is not None:
        thread.title = body.title
    await db.flush()
    return thread


@router.delete("/threads/{thread_id}", status_code=204)
async def delete_thread(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a thread. Messages are CASCADE-deleted by PostgreSQL."""
    thread = await _require_thread_owner(thread_id, user.id, db)
    await db.delete(thread)


@router.get("/threads/{thread_id}/messages", response_model=list[MessageOut])
async def list_messages(
    thread_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all messages in a thread, oldest first."""
    await _require_thread_owner(thread_id, user.id, db)
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.thread_id == thread_id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()


# ─── Step 1: Save user message ────────────────────────────────────────────────


@router.post(
    "/threads/{thread_id}/messages",
    response_model=SendMessageResponse,
    status_code=201,
)
async def send_message(
    thread_id: uuid.UUID,
    body: SendMessage,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save the user's message to PostgreSQL.
    Returns user_message_id — pass it to GET /stream to get the assistant response.
    The LLM is NOT called here.
    """
    thread = await _require_thread_owner(thread_id, user.id, db)
    user_msg = ChatMessage(
        id=uuid.uuid4(),
        thread_id=thread.id,
        role=MessageRole.user,
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()
    return SendMessageResponse(
        user_message_id=user_msg.id,
        thread_id=thread.id,
    )


# ─── Step 2: SSE stream ───────────────────────────────────────────────────────


@router.get("/threads/{thread_id}/stream")
async def stream_response(
    thread_id: uuid.UUID,
    request: Request,
    user_message_id: uuid.UUID = Query(...),
    token: str = Query(..., description="JWT — query param because EventSource cannot send headers"),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE endpoint — streams the Ollama-generated response token by token.

    PHASE 4 NOTE (Nginx): add to the location block for this endpoint:
        proxy_buffering off;
        proxy_cache off;
    The X-Accel-Buffering: no header below handles it at the app layer.
    """
    user = await _auth_from_query_token(token, request, db)
    thread = await _require_thread_owner(thread_id, user.id, db)

    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.id == user_message_id,
            ChatMessage.thread_id == thread_id,
            ChatMessage.role == MessageRole.user,
        )
    )
    user_msg = result.scalar_one_or_none()
    if user_msg is None:
        raise HTTPException(status_code=404, detail="User message not found in this thread")

    # Snapshot primitives — generator creates its own session,
    # passing SQLAlchemy model instances across sessions causes DetachedInstanceError
    return StreamingResponse(
        _run_stream(
            thread_id=thread.id,
            thread_mode=thread.mode,
            owner_id=thread.owner_id,
            user_msg_id=user_msg.id,
            user_content=user_msg.content,
            request=request,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ─── Stream generator ─────────────────────────────────────────────────────────


async def _run_stream(
    thread_id: uuid.UUID,
    thread_mode: ChatMode,
    owner_id: uuid.UUID,
    user_msg_id: uuid.UUID,
    user_content: str,
    request: Request,
) -> AsyncIterator[str]:
    """
    Core SSE generator. Owns its own AsyncSession.

    On client disconnect: stops generation, does NOT save truncated message.
    On any exception: rolls back, yields error event.
    """
    async with AsyncSessionLocal() as db:
        collected_tokens: list[str] = []
        sources = None
        client_disconnected = False

        try:
            if thread_mode == ChatMode.rag:
                chunks = await retrieve_context(
                    user_id=str(owner_id),
                    query=user_content,
                )

                if not chunks:
                    no_info = "I couldn't find relevant information in your documents for this question."
                    yield _sse({"type": "token", "content": no_info})
                    collected_tokens.append(no_info)
                else:
                    async for token in stream_rag(chunks, user_content):
                        if await request.is_disconnected():
                            client_disconnected = True
                            break
                        collected_tokens.append(token)
                        yield _sse({"type": "token", "content": token})

                    if not client_disconnected:
                        # One source entry per document, deduplicated
                        seen: dict[str, dict] = {}
                        for chunk in chunks:
                            doc_id = chunk["document_id"]
                            if doc_id not in seen:
                                seen[doc_id] = {
                                    "document_id": doc_id,
                                    "source": chunk["source"],
                                    "distance": chunk["distance"],
                                }
                        sources = list(seen.values())
                        yield _sse({"type": "sources", "sources": sources})

            else:
                # Load last 20 messages as history (10 turns of context)
                history_result = await db.execute(
                    select(ChatMessage)
                    .where(
                        ChatMessage.thread_id == thread_id,
                        ChatMessage.id != user_msg_id,
                    )
                    .order_by(ChatMessage.created_at.desc())
                    .limit(20)
                )
                history = list(reversed(history_result.scalars().all()))
                history_dicts = [
                    {"role": m.role.value, "content": m.content} for m in history
                ]

                async for token in stream_general(history_dicts, user_content):
                    if await request.is_disconnected():
                        client_disconnected = True
                        break
                    collected_tokens.append(token)
                    yield _sse({"type": "token", "content": token})

            if not client_disconnected and collected_tokens:
                full_content = "".join(collected_tokens)
                assistant_msg = ChatMessage(
                    id=uuid.uuid4(),
                    thread_id=thread_id,
                    role=MessageRole.assistant,
                    content=full_content,
                    sources=sources,
                )
                db.add(assistant_msg)

                # Bump updated_at so the thread sorts to top
                await db.execute(
                    sa.update(ChatThread)
                    .where(ChatThread.id == thread_id)
                    .values(updated_at=datetime.now(timezone.utc))
                )

                await db.commit()
                yield _sse({"type": "done", "message_id": str(assistant_msg.id)})

        except Exception as exc:
            await db.rollback()
            yield _sse({"type": "error", "detail": str(exc)})


# ─── Helpers ──────────────────────────────────────────────────────────────────


async def _require_thread_owner(
    thread_id: uuid.UUID,
    owner_id: uuid.UUID,
    db: AsyncSession,
) -> ChatThread:
    """403 on ownership violation, consistent with the files router."""
    result = await db.execute(select(ChatThread).where(ChatThread.id == thread_id))
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")
    if thread.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return thread


async def _auth_from_query_token(
    token: str,
    request: Request,
    db: AsyncSession,
) -> User:
    """Authenticate from a JWT query param. Mirrors get_current_user exactly."""
    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    jti: str | None = payload.get("jti")
    user_id_str: str | None = payload.get("sub")
    if not jti or not user_id_str:
        raise HTTPException(status_code=401, detail="Malformed token payload")

    blacklisted = await request.app.state.redis.get(f"blacklist:{jti}")
    if blacklisted:
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token subject")

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _sse(data: dict) -> str:
    """Serialize dict to SSE data line. Double newline terminates the event."""
    return f"data: {json.dumps(data)}\n\n"