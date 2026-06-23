"""
Pydantic schemas for the file management endpoints.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.models.documents import FileType, ProcessingStatus


class UploadResponse(BaseModel):
    """Returned immediately after upload — document is queued, not yet processed."""
    document_id: UUID
    filename: str
    status: str


class DocumentStatusResponse(BaseModel):
    """Polling response for processing progress."""
    status: ProcessingStatus
    vector_count: int
    error_message: str | None


class DocumentListItem(BaseModel):
    """One row in the file list."""
    id: UUID
    filename: str
    original_filename: str
    file_type: FileType
    file_size_mb: float
    processing_status: ProcessingStatus
    vector_count: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}


class DeleteResponse(BaseModel):
    message: str