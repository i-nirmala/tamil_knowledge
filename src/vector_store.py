"""
Code Bloom — Vector Store (FAISS)
------------------------------------------------
Thin wrapper around a FAISS flat inner-product index. Because embeddings
are L2-normalized, inner product == cosine similarity, giving scores in
a clean [-1, 1] (practically [0, 1]) range.

Chunk metadata is kept in a parallel Python list and persisted as JSON
next to the FAISS index file, so the whole knowledge base can be saved
and reloaded between app runs without recomputing embeddings.
"""

import json
import threading
from dataclasses import asdict
from typing import List, Optional, Tuple

import faiss
import numpy as np

from src.chunker import Chunk
from src.config import EMBEDDING_DIM, FAISS_INDEX_PATH, METADATA_PATH

_lock = threading.Lock()


class VectorStore:
    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.metadata: List[dict] = []  # parallel list, one dict per vector

    # ------------------------------------------------------------------
    def add(self, vectors: np.ndarray, chunks: List[Chunk]) -> None:
        if vectors.shape[0] == 0:
            return
        with _lock:
            self.index.add(vectors)
            self.metadata.extend([asdict(c) for c in chunks])

    # ------------------------------------------------------------------
    def search(self, query_vector: np.ndarray, top_k: int) -> List[Tuple[dict, float]]:
        """Return up to top_k (metadata, score) pairs, best first."""
        if self.index.ntotal == 0:
            return []
        top_k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_vector, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self.metadata[idx], float(score)))
        return results

    # ------------------------------------------------------------------
    @property
    def total_vectors(self) -> int:
        return self.index.ntotal

    # ------------------------------------------------------------------
    def save(self, index_path=FAISS_INDEX_PATH, metadata_path=METADATA_PATH) -> None:
        with _lock:
            faiss.write_index(self.index, str(index_path))
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(self.metadata, f, ensure_ascii=False)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, index_path=FAISS_INDEX_PATH, metadata_path=METADATA_PATH) -> Optional["VectorStore"]:
        if not index_path.exists() or not metadata_path.exists():
            return None
        try:
            index = faiss.read_index(str(index_path))
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception:
            return None

        store = cls(dim=index.d)
        store.index = index
        store.metadata = metadata
        return store
