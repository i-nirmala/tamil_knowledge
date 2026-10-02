"""
Code Bloom — PDF Processor
------------------------------------------------
Extracts text from PDF documents page-by-page using PyMuPDF (fitz),
preserving page numbers so every chunk can later be traced back to an
exact page for citation purposes.

Handles corrupted files, encrypted files and scanned (no-text) PDFs
gracefully — the caller always receives a well-formed result dict,
never an unhandled exception.
"""

from dataclasses import dataclass, field
from typing import List, Optional

import fitz  # PyMuPDF

from src.utils import clean_text


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str


@dataclass
class PDFExtractionResult:
    success: bool
    pages: List[PageText] = field(default_factory=list)
    total_pages: int = 0
    error: Optional[str] = None
    is_scanned: bool = False  # true if no extractable text was found


def extract_pdf_text(file_path: str) -> PDFExtractionResult:
    """
    Extract text from every page of a PDF.

    Returns a PDFExtractionResult. On any failure (corrupted file,
    encrypted file, unreadable format) `success` is False and `error`
    contains a human-readable explanation — the caller should surface
    this in the UI, never crash.
    """
    # Validate this is genuinely a PDF before handing it to PyMuPDF.
    # PyMuPDF will happily open plain-text and several image formats as
    # "documents", which would silently ingest an unsupported file
    # instead of telling the user their upload was the wrong type.
    try:
        with open(file_path, "rb") as fh:
            header = fh.read(5)
    except FileNotFoundError:
        return PDFExtractionResult(success=False, error="File not found.")
    except Exception as exc:
        return PDFExtractionResult(success=False, error=f"Could not read file: {exc}")

    if header != b"%PDF-":
        return PDFExtractionResult(
            success=False,
            error="This file is not a valid PDF (missing PDF header). Please upload a .pdf file.",
        )

    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        return PDFExtractionResult(success=False, error=f"Could not open PDF: {exc}")

    if doc.is_encrypted:
        # Try an empty-password unlock (common for "restricted" PDFs);
        # if that fails, report clearly instead of crashing.
        try:
            if not doc.authenticate(""):
                doc.close()
                return PDFExtractionResult(
                    success=False,
                    error="This PDF is password-protected and could not be opened.",
                )
        except Exception as exc:
            doc.close()
            return PDFExtractionResult(success=False, error=f"Encrypted PDF error: {exc}")

    pages: List[PageText] = []
    total_pages = doc.page_count

    try:
        for i in range(total_pages):
            page = doc.load_page(i)
            raw_text = page.get_text("text") or ""
            cleaned = clean_text(raw_text)
            pages.append(PageText(page_number=i + 1, text=cleaned))
    except Exception as exc:
        doc.close()
        return PDFExtractionResult(success=False, error=f"Error reading pages: {exc}")

    doc.close()

    non_empty_pages = [p for p in pages if len(p.text.strip()) > 10]
    is_scanned = total_pages > 0 and len(non_empty_pages) == 0

    if is_scanned:
        return PDFExtractionResult(
            success=False,
            pages=pages,
            total_pages=total_pages,
            is_scanned=True,
            error=(
                "No extractable text was found — this looks like a scanned "
                "(image-only) PDF. OCR is not enabled in this prototype, so "
                "this document cannot be added to the knowledge base."
            ),
        )

    return PDFExtractionResult(success=True, pages=pages, total_pages=total_pages)
