"""
Code Bloom — Command-Line Document Ingestion
------------------------------------------------
Optional CLI alternative to the Upload Documents page. Useful for
bulk-adding a folder of PDFs before a demo.

Examples (Windows PowerShell):

    # Ingest a single PDF
    python scripts/ingest_documents.py --file "data/books/my_book.pdf" --title "My Book" --author "Author Name"

    # Ingest every PDF in a folder
    python scripts/ingest_documents.py --folder "data/books" --author "Unknown"
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.knowledge_base import get_kb_stats, ingest_pdf


def ingest_one(path: Path, title: str, author: str, chapter: str, doc_type: str) -> None:
    print(f"\n→ {path.name}")
    result = ingest_pdf(
        file_path=str(path),
        title=title,
        author=author,
        chapter=chapter,
        doc_type=doc_type,
        source_filename=path.name,
    )
    if result.success:
        d = result.document
        print(f"   ✓ Indexed — {d.pages} pages, {d.chunks} chunks")
    else:
        print(f"   ✗ Skipped — {result.message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest PDFs into the Code Bloom knowledge base.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to a single PDF file.")
    group.add_argument("--folder", help="Path to a folder containing PDF files.")
    parser.add_argument("--title", help="Document title (defaults to the filename stem).")
    parser.add_argument("--author", default="Unknown", help="Author name.")
    parser.add_argument("--chapter", default="", help="Chapter label (optional).")
    parser.add_argument("--type", dest="doc_type", default="book", choices=["book", "pdf"],
                        help="Which source adapter this document belongs to.")
    args = parser.parse_args()

    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"✗ File not found: {path}")
            sys.exit(1)
        ingest_one(path, args.title or path.stem, args.author, args.chapter, args.doc_type)

    else:
        folder = Path(args.folder)
        if not folder.is_dir():
            print(f"✗ Folder not found: {folder}")
            sys.exit(1)
        pdfs = sorted(folder.glob("*.pdf"))
        if not pdfs:
            print(f"✗ No PDF files found in {folder}")
            sys.exit(1)
        print(f"Found {len(pdfs)} PDF(s) in {folder}")
        for pdf in pdfs:
            ingest_one(pdf, args.title or pdf.stem, args.author, args.chapter, args.doc_type)

    stats = get_kb_stats()
    print(
        f"\nKnowledge Base — Documents: {stats['documents']} · "
        f"Pages: {stats['pages']} · Chunks: {stats['chunks']} · Vectors: {stats['vectors']}"
    )


if __name__ == "__main__":
    main()
