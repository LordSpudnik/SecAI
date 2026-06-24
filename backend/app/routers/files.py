"""
File management endpoints: upload, list, status, delete.

Ownership rule from PRD: return 403 (not 404) on ownership failure.
404 would imply the resource doesn't exist — it does, the user just can't see it.
403 is honest about what happened.
"""
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.documents import Document, FileType, ProcessingStatus
from app.models.user import User
from app.schemas.file import DeleteResponse, DocumentListItem, DocumentStatusResponse, UploadResponse
from app.services.chroma import delete_document_chunks
from app.services.document_processor import process_document

router = APIRouter()

ALLOWED_EXTENSIONS: dict[str, FileType] = {
    ".pdf": FileType.pdf,
    ".docx": FileType.docx,
    ".xlsx": FileType.xlsx,
    ".txt": FileType.txt,
    ".csv": FileType.csv,
}


def _sanitize_filename(name: str) -> str:
    """
    Produce a safe display name from the original filename.
    Strips special characters and collapses whitespace.
    Example: "Q3 Report (Final)!.pdf" → "Q3-Report-Final.pdf"
    The UUID-named file on disk is separate — this is for display only.
    """
    stem = Path(name).stem
    suffix = Path(name).suffix.lower()
    safe = re.sub(r"[^\w\s-]", "", stem).strip()
    safe = re.sub(r"[\s_]+", "-", safe)
    return f"{safe}{suffix}" if safe else name


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    """
    Upload a document and queue it for RAG indexing.

    Returns immediately with status=queued. Processing happens in the background.
    Poll GET /files/{id}/status every few seconds to track progress.
    """
    original_name = file.filename or "unknown"
    suffix = Path(original_name).suffix.lower()
    file_type = ALLOWED_EXTENSIONS.get(suffix)

    if file_type is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"'{suffix}' is not supported. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is {size_mb:.1f}MB — exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit",
        )

    # Store on disk as {uuid}.{ext} — prevents filename conflicts and path traversal attacks
    document_id = uuid.uuid4()
    disk_name = f"{document_id}{suffix}"
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / disk_name

    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        id=document_id,
        owner_id=current_user.id,
        filename=_sanitize_filename(original_name),
        original_filename=original_name,
        file_type=file_type,
        file_size_mb=round(size_mb, 3),
        file_path=str(file_path),
        chroma_collection=f"user_{current_user.id}",
        processing_status=ProcessingStatus.queued,
    )
    db.add(doc)
    await db.flush()

    # Schedule processing AFTER the DB record is committed
    # (background task starts after this function returns, by which time get_db commits)
    background_tasks.add_task(
        process_document,
        document_id=document_id,
        file_path=str(file_path),
        file_type=file_type.value,
        filename=doc.original_filename,
        user_id=current_user.id,
    )

    return UploadResponse(
        document_id=document_id,
        filename=doc.filename,
        status=ProcessingStatus.queued.value,
    )


@router.get("/", response_model=list[DocumentListItem])
async def list_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentListItem]:
    """List all documents owned by the current user, newest first."""
    result = await db.execute(
        select(Document)
        .where(Document.owner_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    )
    return [DocumentListItem.model_validate(doc) for doc in result.scalars().all()]


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def file_status(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentStatusResponse:
    """Polling endpoint — frontend calls this every 3 seconds after upload."""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return DocumentStatusResponse(
        status=doc.processing_status,
        vector_count=doc.vector_count,
        error_message=doc.processing_error,
    )


@router.delete("/{document_id}", response_model=DeleteResponse)
async def delete_file(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DeleteResponse:
    """
    Delete a document from ChromaDB, disk, and PostgreSQL.

    Order is deliberate:
      ChromaDB first — if DB delete succeeds but Chroma fails, you have
      orphaned vectors with no way to identify or clean them.
      Disk second — file is referenced by the DB record until now.
      Database last — record is the source of truth; delete it last.
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()

    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Only call ChromaDB if processing completed — otherwise collection may not exist
    if doc.processing_status == ProcessingStatus.ready:
        await delete_document_chunks(
            user_id=current_user.id,
            document_id=str(document_id),
        )

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink()

    await db.execute(delete(Document).where(Document.id == document_id))

    return DeleteResponse(message="Document deleted successfully")