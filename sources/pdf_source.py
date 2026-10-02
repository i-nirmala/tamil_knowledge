"""
Code Bloom — PDF Source Adapter
------------------------------------------------
Searches PDF documents (doc_type == "pdf") that have been ingested into
the shared FAISS vector store. This is one of the two fully working
sources in the MVP (the other is TamilBookAdapter).
"""

from typing import List

from src.vector_store import VectorStore
from sources.base_source import BaseSource, SourceSearchResult


class PDFAdapter(BaseSource):
    name = "PDFs"
    key = "pdfs"

    def __init__(self):
        self._store = None

    def _get_store(self):
        if self._store is None:
            self._store = VectorStore.load()
        return self._store

    def is_available(self) -> bool:
        store = self._get_store()
        if store is None or store.total_vectors == 0:
            return False
        return any(m.get("doc_type") == "pdf" for m in store.metadata)

    def search(self, query: str, query_vector, top_k: int) -> List[SourceSearchResult]:
        store = self._get_store()
        if store is None:
            return []
        raw_results = store.search(query_vector, top_k=top_k * 3)  # over-fetch, then filter
        filtered = [
            SourceSearchResult(metadata=meta, score=score)
            for meta, score in raw_results
            if meta.get("doc_type") == "pdf"
        ]
        return filtered[:top_k]
