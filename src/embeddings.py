"""
Code Bloom — Embeddings
------------------------------------------------
Wraps a multilingual sentence-embedding model (default:
paraphrase-multilingual-MiniLM-L12-v2) so that Tamil, English, Tanglish
and mixed-language text can all be embedded into the same vector space
for semantic retrieval.

This model was chosen because it:
  - covers 50+ languages including Tamil
  - is small (~470MB) and runs comfortably on CPU
  - needs no GPU/CUDA — practical for a normal Windows laptop with 16GB RAM

The model is loaded once and cached (Streamlit's cache_resource is used
by the UI layer; this module also keeps a module-level singleton so it
works identically from CLI scripts).
"""

from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from src.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Load (once) and return the multilingual embedding model."""
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model


def embed_texts(texts: List[str]) -> np.ndarray:
    """Embed a list of strings. Returns an (N, D) float32 numpy array,
    L2-normalized so that inner product == cosine similarity."""
    if not texts:
        return np.zeros((0, 384), dtype="float32")
    model = get_embedding_model()
    vectors = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
        batch_size=32,
    )
    return vectors.astype("float32")


def embed_query(query: str) -> np.ndarray:
    """Embed a single query string. Returns a (1, D) float32 array."""
    return embed_texts([query])
