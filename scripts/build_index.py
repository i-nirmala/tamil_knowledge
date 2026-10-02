"""
Code Bloom — Rebuild Index
------------------------------------------------
Rebuilds the FAISS index and the knowledge-base registry from scratch:
clears the existing index, regenerates the bundled sample document, and
re-ingests every PDF found in data/books/.

Use this if the index is ever corrupted, or after changing the embedding
model (vectors from different models are not comparable).

    python scripts/build_index.py
    python scripts/build_index.py --sample-only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import BOOKS_DIR, FAISS_INDEX_PATH, KB_REGISTRY_PATH, METADATA_PATH
from src.knowledge_base import bootstrap_sample_knowledge_base, get_kb_stats, ingest_pdf


def clear_index() -> None:
    for path in (FAISS_INDEX_PATH, METADATA_PATH, KB_REGISTRY_PATH):
        if path.exists():
            path.unlink()
            print(f"   removed {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the Code Bloom FAISS index.")
    parser.add_argument("--sample-only", action="store_true",
                        help="Only re-index the bundled sample document.")
    args = parser.parse_args()

    print("Clearing existing index…")
    clear_index()

    print("\nIngesting sample knowledge base…")
    boot = bootstrap_sample_knowledge_base()
    print(f"   {'✓' if boot.success else '✗'} {boot.message}")

    if not args.sample_only:
        pdfs = sorted(Path(BOOKS_DIR).glob("*.pdf"))
        if pdfs:
            print(f"\nRe-ingesting {len(pdfs)} user document(s) from {BOOKS_DIR}…")
            for pdf in pdfs:
                result = ingest_pdf(
                    file_path=str(pdf),
                    title=pdf.stem,
                    author="Unknown",
                    doc_type="book",
                    source_filename=pdf.name,
                )
                status = "✓" if result.success else "✗"
                print(f"   {status} {pdf.name} — {result.message}")
        else:
            print(f"\nNo user documents found in {BOOKS_DIR}.")

    stats = get_kb_stats()
    print(
        f"\nRebuild complete — Documents: {stats['documents']} · "
        f"Pages: {stats['pages']} · Chunks: {stats['chunks']} · Vectors: {stats['vectors']}"
    )


if __name__ == "__main__":
    main()
