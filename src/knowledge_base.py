"""
Code Bloom — Knowledge Base Manager
------------------------------------------------
Owns the document registry (which books/PDFs have been ingested) and
coordinates PDF extraction -> chunking -> embedding -> FAISS indexing.
This is the module the Upload page and the ingestion CLI script both
call into, so there is exactly one ingestion code path.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional

from src.chunker import chunk_document
from src.config import KB_REGISTRY_PATH
from src.embeddings import embed_texts
from src.pdf_processor import extract_pdf_text
from src.utils import file_hash, new_id, now_iso
from src.vector_store import VectorStore


@dataclass
class DocumentRecord:
    doc_id: str
    title: str
    author: str
    source_filename: str
    doc_type: str
    pages: int
    chunks: int
    file_hash: str
    added_at: str
    indexed: bool = True


@dataclass
class IngestResult:
    success: bool
    message: str
    document: Optional[DocumentRecord] = None


# ----------------------------------------------------------------------
# Registry (list of ingested documents) persistence
# ----------------------------------------------------------------------
def load_registry() -> List[DocumentRecord]:
    if not KB_REGISTRY_PATH.exists():
        return []
    try:
        with open(KB_REGISTRY_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        return [DocumentRecord(**r) for r in raw]
    except Exception:
        return []


def save_registry(records: List[DocumentRecord]) -> None:
    with open(KB_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, ensure_ascii=False, indent=2)


def registry_has_hash(records: List[DocumentRecord], h: str) -> bool:
    return any(r.file_hash == h for r in records)


# ----------------------------------------------------------------------
# Ingestion
# ----------------------------------------------------------------------
def ingest_pdf(
    file_path: str,
    title: str,
    author: str = "Unknown",
    chapter: str = "",
    section: str = "",
    doc_type: str = "book",
    source_filename: Optional[str] = None,
    store: Optional[VectorStore] = None,
) -> IngestResult:
    """
    Full ingestion pipeline for a single PDF:
      extract -> clean -> chunk -> embed -> add to FAISS -> register
    Returns an IngestResult with either the new DocumentRecord or a
    human-readable error message. Never raises.
    """
    source_filename = source_filename or Path(file_path).name

    with open(file_path, "rb") as f:
        content = f.read()
    h = file_hash(content)

    registry = load_registry()
    if registry_has_hash(registry, h):
        return IngestResult(success=False, message="This document is already in the knowledge base.")

    extraction = extract_pdf_text(file_path)
    if not extraction.success:
        return IngestResult(success=False, message=extraction.error or "Failed to read PDF.")

    doc_id = new_id("doc_")
    chunks = chunk_document(
        pages=extraction.pages,
        doc_id=doc_id,
        book_title=title,
        author=author,
        chapter=chapter,
        section=section,
        source_filename=source_filename,
        doc_type=doc_type,
    )

    if not chunks:
        return IngestResult(success=False, message="No usable text could be extracted from this PDF.")

    texts = [c.text for c in chunks]
    vectors = embed_texts(texts)

    if store is None:
        store = VectorStore.load() or VectorStore()
    store.add(vectors, chunks)
    store.save()

    record = DocumentRecord(
        doc_id=doc_id,
        title=title,
        author=author,
        source_filename=source_filename,
        doc_type=doc_type,
        pages=extraction.total_pages,
        chunks=len(chunks),
        file_hash=h,
        added_at=now_iso(),
    )
    registry.append(record)
    save_registry(registry)

    return IngestResult(success=True, message="Document indexed successfully.", document=record)


# ----------------------------------------------------------------------
# First-run bootstrap of the sample knowledge base
# ----------------------------------------------------------------------
SAMPLE_PDF_NAME = "thirukkural_sample.pdf"
SAMPLE_TITLE = "Thirukkural — Curated Sample Selection"
SAMPLE_AUTHOR = "Thiruvalluvar (trans. G.U. Pope, 1886)"


def bootstrap_sample_knowledge_base() -> IngestResult:
    """
    Make the app usable the moment it is installed: if the knowledge
    base is empty, generate the sample PDF (if missing) and ingest it.

    Safe to call on every app start — it returns immediately once the
    sample document is already registered.
    """
    from src.config import SAMPLE_DIR

    registry = load_registry()
    if registry:
        return IngestResult(success=True, message="Knowledge base already initialised.")

    sample_pdf = SAMPLE_DIR / SAMPLE_PDF_NAME

    if not sample_pdf.exists():
        try:
            # Generate the demo PDF from the bundled public-domain content.
            from scripts.generate_sample_pdfs import build_pdf

            build_pdf()
        except Exception as exc:
            return IngestResult(success=False, message=f"Could not generate sample PDF: {exc}")

    if not sample_pdf.exists():
        return IngestResult(success=False, message="Sample PDF could not be created.")

    return ingest_pdf(
        file_path=str(sample_pdf),
        title=SAMPLE_TITLE,
        author=SAMPLE_AUTHOR,
        chapter="Selected chapters",
        doc_type="book",
        source_filename=SAMPLE_PDF_NAME,
    )


# ----------------------------------------------------------------------
# Dashboard stats
# ----------------------------------------------------------------------
def get_kb_stats() -> dict:
    registry = load_registry()
    store = VectorStore.load()
    total_pages = sum(r.pages for r in registry)
    total_chunks = sum(r.chunks for r in registry)
    return {
        "documents": len(registry),
        "pages": total_pages,
        "chunks": total_chunks,
        "vectors": store.total_vectors if store else 0,
        "records": registry,
    }
