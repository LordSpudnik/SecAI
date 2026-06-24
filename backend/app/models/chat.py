"""
ChatThread and ChatMessage SQLAlchemy models — Phase 3.

ChatThread: one conversation session. mode is set at creation and never changes.
  - general: direct LLM conversation with history context
  - rag: every answer grounded in the user's uploaded documents

ChatMessage: one message in a thread.
  - role: 'user' or 'assistant'
  - sources: JSONB, only populated on assistant messages in RAG mode
             contains [{document_id, source, distance}, ...]

No SQLAlchemy relationship attributes — async SQLAlchemy requires explicit
selectinload() for eager loading. We load messages in a separate query where needed.
"""
import enum
import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ChatMode(str, enum.Enum):
    general = "general"
    rag = "rag"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatThread(Base):
    __tablename__ = "chat_threads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        sa.String(255),
        nullable=False,
        default="New Chat",
    )
    # create_type=False — migration creates the ENUM type, not SQLAlchemy
    mode: Mapped[ChatMode] = mapped_column(
        sa.Enum(ChatMode, name="chatmode", create_type=False),
        nullable=False,
        default=ChatMode.general,
    )
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    thread_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        sa.Enum(MessageRole, name="messagerole", create_type=False),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    sources: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.now(),
        nullable=False,
    )