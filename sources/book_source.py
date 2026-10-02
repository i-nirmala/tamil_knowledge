"""
Code Bloom — Tamil Book Source Adapter
------------------------------------------------
Searches curated Tamil book content (doc_type == "book") that has been
ingested into the shared FAISS vector store — this is the primary,
fully-working source for the hackathon MVP, per the PPT's prioritization
of Tamil Books / PDFs.
"""

from typing import List

from src.vector_store import VectorStore
from sources.base_source import BaseSource, SourceSearchResult


class TamilBookAdapter(BaseSource):
    name = "Tamil Books"
    key = "tamil_books"

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
        return any(m.get("doc_type") == "book" for m in store.metadata)

    def search(self, query: str, query_vector, top_k: int) -> List[SourceSearchResult]:
        store = self._get_store()
        if store is None:
            return []
        raw_results = store.search(query_vector, top_k=top_k * 3)
        filtered = [
            SourceSearchResult(metadata=meta, score=score)
            for meta, score in raw_results
            if meta.get("doc_type") == "book"
        ]
        return filtered[:top_k]
