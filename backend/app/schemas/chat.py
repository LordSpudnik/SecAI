"""
Pydantic schemas for chat endpoints — Phase 3.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.models.chat import ChatMode, MessageRole


class ThreadCreate(BaseModel):
    title: str = "New Chat"
    mode: ChatMode = ChatMode.general

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v.strip()


class ThreadUpdate(BaseModel):
    title: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title cannot be empty")
        return v.strip() if v else v


class SourceOut(BaseModel):
    """One cited document chunk returned in a RAG response."""
    document_id: str
    source: str       # original filename — e.g. "report.pdf"
    distance: float   # cosine distance (lower = more relevant)


class MessageOut(BaseModel):
    id: UUID
    thread_id: UUID
    role: MessageRole
    content: str
    sources: Optional[list[SourceOut]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ThreadOut(BaseModel):
    id: UUID
    title: str
    mode: ChatMode
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ThreadWithMessages(ThreadOut):
    messages: list[MessageOut] = []


class SendMessage(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content cannot be empty")
        return v.strip()


class SendMessageResponse(BaseModel):
    """
    Returned by POST /messages.
    Client passes user_message_id to the SSE stream endpoint (Step 2).
    """
    user_message_id: UUID
    thread_id: UUID