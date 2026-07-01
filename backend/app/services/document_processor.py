"""
Document processing pipeline: extract → chunk → embed → store in ChromaDB.

Runs as a FastAPI BackgroundTask after the HTTP response is sent.
Client polls GET /files/{id}/status to track progress.

Pipeline stages:
  1. Update status to "processing"
  2. Extract raw text from the file
  3. Split text into overlapping chunks
  4. Generate embedding vectors
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
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
    return "\n\n".join(pages)


def _extract_docx(file_path: str) -> str:
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
    try:
        return Path(file_path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return Path(file_path).read_text(encoding="latin-1")


def _extract_csv(file_path: str) -> str:
    rows = []
    with open(file_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        for row in reader:
            row_text = "\t".join(cell.strip() for cell in row if cell.strip())
            if row_text:
                rows.append(row_text)
    return "\n".join(rows)


def _extract_text(file_path: str, file_type: str) -> str:
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
    chunk_size = 500
    chunk_overlap = 50
    min_chunk_size = 100  # Discard fragments shorter than this

    if len(text) <= chunk_size:
        stripped = text.strip()
        return [stripped] if len(stripped) >= min_chunk_size else []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            # Critical: only search for a separator after accumulating at least
            # half the chunk size (split_floor). The original code searched from
            # start+chunk_overlap (~50 chars in), which caused rfind to find the
            # first \n\n in the document immediately — producing 50-char fragments
            # and advancing start by only ~2 chars per iteration. A 3KB document
            # ended up as 65 micro-chunks instead of ~6 meaningful ones.
            split_floor = start + (chunk_size // 2)
            for separator in ["\n\n", "\n", ". ", " "]:
                pos = text.rfind(separator, split_floor, end)
                if pos != -1:
                    end = pos + len(separator)
                    break
        chunk = text[start:end].strip()
        if len(chunk) >= min_chunk_size:
            chunks.append(chunk)
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
    'filename' must be the original filename (e.g. "report.pdf"), NOT the UUID
    disk name. The files router is responsible for passing the right value.
    This is what surfaces in RAG citations shown to the user.
    """
    try:
        await _update_status(document_id, ProcessingStatus.processing)

        loop = asyncio.get_event_loop()
        raw_text = await loop.run_in_executor(
            None, partial(_extract_text, file_path, file_type)
        )

        if not raw_text.strip():
            raise ValueError(
                "No text could be extracted. The file may be a scanned image PDF or empty."
            )

        chunks = _chunk_text(raw_text)

        if not chunks:
            raise ValueError("Text extraction succeeded but chunking produced no output.")

        embeddings = await generate_embeddings(chunks)

        collection = await get_or_create_user_collection(user_id)

        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": str(document_id),
                "owner_id": str(user_id),
                "source": filename,       # ← used by rag.py for citations
                "filename": filename,     # ← kept for backward compatibility
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]

        add_fn = partial(
            collection.add,
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )
        await loop.run_in_executor(None, add_fn)

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
        raise