"""
Code Bloom — Chunker
------------------------------------------------
Splits page-level text into overlapping chunks suitable for embedding,
while preserving full metadata (document id, title, author, chapter,
page number, source filename, chunk id) on every single chunk. This
metadata is what powers Code Bloom's page-level citations.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from src.config import CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS
from src.pdf_processor import PageText
from src.utils import new_id


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    text: str
    page_number: int
    book_title: str
    author: str
    chapter: str
    section: str
    source_filename: str
    doc_type: str = "book"  # "book" | "pdf" — used by source adapters to filter


def _split_page_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """Split a single page's text into overlapping chunks on sentence /
    whitespace boundaries where possible, falling back to a hard cut."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + chunk_size, length)
        # try to break on a sentence-ish boundary near the end
        if end < length:
            boundary = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
                text.rfind("\n", start, end),
            )
            if boundary != -1 and boundary > start + int(chunk_size * 0.4):
                end = boundary + 1
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_document(
    pages: List[PageText],
    doc_id: str,
    book_title: str,
    author: str = "Unknown",
    chapter: str = "",
    section: str = "",
    source_filename: str = "",
    doc_type: str = "book",
    chunk_size: int = CHUNK_SIZE_CHARS,
    overlap: int = CHUNK_OVERLAP_CHARS,
) -> List[Chunk]:
    """
    Convert a list of page-level texts into metadata-rich chunks.
    Every chunk knows exactly which page (and document) it came from.
    """
    all_chunks: List[Chunk] = []

    for page in pages:
        pieces = _split_page_text(page.text, chunk_size, overlap)
        for piece in pieces:
            all_chunks.append(
                Chunk(
                    chunk_id=new_id("chunk_"),
                    doc_id=doc_id,
                    text=piece,
                    page_number=page.page_number,
                    book_title=book_title,
                    author=author,
                    chapter=chapter,
                    section=section,
                    source_filename=source_filename,
                    doc_type=doc_type,
                )
            )

    return all_chunks
