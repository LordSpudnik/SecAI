"""
Document processing pipeline: extract → chunk → embed → store in ChromaDB.

This is the core of Phase 2. It runs as a FastAPI BackgroundTask — the HTTP
response (status: queued) is returned to the client immediately, and this
function runs after. The client polls GET /files/{id}/status to track progress.

Pipeline stages:
  1. Update status to "processing"
  2. Extract raw text from the file (file-type-specific)
  3. Split text into overlapping chunks
  4. Generate embedding vectors for each chunk
  5. Store embeddings in ChromaDB
  6. Update status to "ready" with chunk count

On any exception: update status to "failed" with the error message.
"""
import asyncio
import csv
import uuid
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

import pdfplumber
from docx import Document as DocxDocument
from openpyxl import load_workbook
from sqlalchemy import update

from app.core.database import AsyncSessionLocal
from app.models.documents import Document, ProcessingStatus
from app.services.chroma import get_or_create_user_collection
from app.services.embedding import generate_embeddings


# ─── Stage 2: Text Extraction ─────────────────────────────────────────────────

def _extract_pdf(file_path: str) -> str:
    """
    Extract text from PDF using pdfplumber, page by page.
    Skips pages with no extractable text — common for scanned image PDFs.
    If ALL pages are images, we raise a clear error in process_document.
    """
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
    return "\n\n".join(pages)


def _extract_docx(file_path: str) -> str:
    """
    Extract text from DOCX using python-docx.
    Covers paragraph text AND table cells — content inside tables is
    not accessible via doc.paragraphs and would be silently skipped otherwise.
    """
    doc = DocxDocument(file_path)
    parts = []

    for para in doc.paragraphs:
        if para.text.strip():
            parts.append(para.text.strip())

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    parts.append(cell.text.strip())

    return "\n\n".join(parts)


def _extract_xlsx(file_path: str) -> str:
    """
    Extract text from XLSX using openpyxl.
    read_only=True avoids loading the full workbook into memory for large files.
    data_only=True returns computed cell values, not formulas.
    """
    wb = load_workbook(file_path, read_only=True, data_only=True)
    parts = []

    for sheet in wb.worksheets:
        parts.append(f"[Sheet: {sheet.title}]")
        for row in sheet.iter_rows(values_only=True):
            row_text = "\t".join(str(v) for v in row if v is not None)
            if row_text.strip():
                parts.append(row_text)

    wb.close()
    return "\n".join(parts)


def _extract_txt(file_path: str) -> str:
    """Read a plain text file. Falls back to latin-1 if the file is not valid UTF-8."""
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(file_path).read_text(encoding="latin-1")


def _extract_csv(file_path: str) -> str:
    """
    Extract text from CSV using Python's built-in csv module.
    utf-8-sig handles files with a BOM (common from Excel exports).
    """
    rows = []
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            row_text = "\t".join(cell.strip() for cell in row if cell.strip())
            if row_text:
                rows.append(row_text)
    return "\n".join(rows)


def _extract_text(file_path: str, file_type: str) -> str:
    """Dispatch to the correct extractor based on file type."""
    extractors = {
        "pdf": _extract_pdf,
        "docx": _extract_docx,
        "xlsx": _extract_xlsx,
        "txt": _extract_txt,
        "csv": _extract_csv,
    }
    return extractors[file_type](file_path)


# ─── Stage 3: Chunking ────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks — no external dependencies.

    Algorithm:
      1. Walk through the text in chunk_size steps
      2. At each boundary, look backwards for a natural break point:
         paragraph break → newline → sentence end → word boundary
      3. Start the next chunk (chunk_overlap) characters before the end
         of the current one — this is the overlap that preserves context
         at boundaries

    chunk_size=800 characters is ~120 words — large enough for a complete
    idea, small enough for precise retrieval.
    chunk_overlap=100 ensures a sentence split across a boundary still
    appears in full in one of the two adjacent chunks.
    """
    chunk_size = 800
    chunk_overlap = 100

    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # If not at the end of the text, walk back to a natural boundary
        # so we don't cut in the middle of a sentence or word
        if end < len(text):
            for separator in ["\n\n", "\n", ". ", " "]:
                pos = text.rfind(separator, start + chunk_overlap, end)
                if pos != -1:
                    end = pos + len(separator)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Advance by (chunk_size - overlap) to create the overlap window
        next_start = end - chunk_overlap
        start = next_start if next_start > start else start + 1

    return chunks


# ─── Database Helper ──────────────────────────────────────────────────────────

async def _update_status(
    document_id: uuid.UUID,
    status: ProcessingStatus,
    vector_count: int = 0,
    error_message: str | None = None,
    processed_at: datetime | None = None,
) -> None:
    """
    Update a document's processing status in PostgreSQL.

    Opens its own session because this runs in a background task — after the
    HTTP response was already sent, outside the request/response lifecycle.
    The get_db() dependency is only available inside route handlers.
    """
    values: dict = {"processing_status": status}
    if vector_count:
        values["vector_count"] = vector_count
    if error_message is not None:
        values["processing_error"] = error_message
    if processed_at is not None:
        values["processed_at"] = processed_at

    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Document).where(Document.id == document_id).values(**values)
        )
        await session.commit()


# ─── Main Pipeline ────────────────────────────────────────────────────────────

async def process_document(
    document_id: uuid.UUID,
    file_path: str,
    file_type: str,
    filename: str,
    user_id: uuid.UUID,
) -> None:
    """
    Run the full document processing pipeline as a background task.

    Each blocking stage runs in a thread pool via run_in_executor so the
    async event loop stays responsive for other incoming requests.

    On any failure: status is set to "failed" with the exception message.
    The client can see this by polling GET /files/{id}/status.
    """
    try:
        await _update_status(document_id, ProcessingStatus.processing)

        # Stage 2: extract text — synchronous file I/O and library calls
        loop = asyncio.get_event_loop()
        raw_text = await loop.run_in_executor(
            None, partial(_extract_text, file_path, file_type)
        )

        if not raw_text.strip():
            raise ValueError(
                "No text could be extracted. The file may be a scanned image PDF or empty."
            )

        # Stage 3: chunk text — fast enough to run inline, no executor needed
        chunks = _chunk_text(raw_text)

        if not chunks:
            raise ValueError("Text extraction succeeded but chunking produced no output.")

        # Stage 4: generate embeddings — CPU-bound, must use executor
        # generate_embeddings handles run_in_executor internally
        embeddings = await generate_embeddings(chunks)

        # Stage 5: store in ChromaDB
        collection = await get_or_create_user_collection(user_id)

        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": str(document_id),
                "filename": filename,
                "chunk_index": i,
                "owner_id": str(user_id),
            }
            for i in range(len(chunks))
        ]

        add_fn = partial(
            collection.add,
            ids=ids,
            embeddings=embeddings,
            documents=chunks,   # storing raw text lets you inspect chunks later
            metadatas=metadatas,
        )
        await loop.run_in_executor(None, add_fn)

        # Stage 6: mark ready
        await _update_status(
            document_id,
            ProcessingStatus.ready,
            vector_count=len(chunks),
            processed_at=datetime.now(timezone.utc),
        )

    except Exception as e:
        await _update_status(
            document_id,
            ProcessingStatus.failed,
            error_message=str(e),
        )
        raise  # Re-raise so FastAPI logs the full traceback in the container