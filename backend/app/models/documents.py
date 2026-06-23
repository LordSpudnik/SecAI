"""
Document table definition.

One record per uploaded file. The actual vector data lives in ChromaDB —
this table tracks metadata and processing state.

processing_status is the state machine:
  queued → processing → ready
                      ↘ failed
"""
import enum
import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FileType(str, enum.Enum):
    pdf = "pdf"
    docx = "docx"
    xlsx = "xlsx"
    txt = "txt"
    csv = "csv"


class ProcessingStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        sa.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # filename: sanitized for display ("my-report.pdf")
    filename: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    # original_filename: exactly what the user uploaded ("My Report (Final)!.pdf")
    original_filename: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    file_type: Mapped[FileType] = mapped_column(sa.Enum(FileType, name="filetype"), nullable=False)
    file_size_mb: Mapped[float] = mapped_column(sa.Float, nullable=False)
    # file_path: absolute path on disk, stored as {uuid4}.{ext} to prevent conflicts and path traversal
    file_path: Mapped[str] = mapped_column(sa.String(512), nullable=False)
    # chroma_collection: the ChromaDB collection this document's vectors live in
    chroma_collection: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    processing_status: Mapped[ProcessingStatus] = mapped_column(
        sa.Enum(ProcessingStatus, name="processingstatus"),
        nullable=False,
        default=ProcessingStatus.queued,
        server_default="queued",
    )
    processing_error: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    # vector_count: number of chunks stored in ChromaDB — 0 until status is ready
    vector_count: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0, server_default="0")
    uploaded_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
    )
    processed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)