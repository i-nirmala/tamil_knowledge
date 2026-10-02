"""
Code Bloom — Semantic Retriever
------------------------------------------------
Given a routing decision (which sources to search) and a query, this
module embeds the query once and fans it out to every selected source
adapter, collecting and merging their results into a single ranked
candidate list ready for reranking.

Optionally blends in a lightweight BM25 keyword score (hybrid
retrieval) when the indexed corpus is small enough for it to be fast —
per the PPT, reliability takes priority over always running hybrid
search, so this degrades gracefully if BM25 setup fails.
"""

from dataclasses import dataclass
from typing import List

from src.config import TOP_K_RETRIEVE
from src.embeddings import embed_query
from src.router import ALL_ADAPTERS, RoutingDecision

try:
    from rank_bm25 import BM25Okapi

    _BM25_AVAILABLE = True
except Exception:  # pragma: no cover
    _BM25_AVAILABLE = False


@dataclass
class RetrievedChunk:
    metadata: dict
    semantic_score: float
    bm25_score: float = 0.0
    combined_score: float = 0.0
    source_key: str = ""


def _bm25_scores(query: str, candidates: List[dict]) -> List[float]:
    if not _BM25_AVAILABLE or not candidates:
        return [0.0] * len(candidates)
    try:
        corpus = [c["text"].split() for c in candidates]
        bm25 = BM25Okapi(corpus)
        raw_scores = bm25.get_scores(query.split())
        max_score = max(raw_scores) if len(raw_scores) else 0.0
        if max_score <= 0:
            return [0.0] * len(candidates)
        return [float(s) / float(max_score) for s in raw_scores]
    except Exception:
        return [0.0] * len(candidates)


def retrieve(query_normalized: str, routing: RoutingDecision, top_k: int = TOP_K_RETRIEVE) -> List[RetrievedChunk]:
    """Run semantic (+ optional keyword) retrieval across the sources
    selected by the router. Returns a de-duplicated, score-sorted list."""
    if not routing.selected_sources:
        return []

    query_vector = embed_query(query_normalized)

    all_results: List[RetrievedChunk] = []
    adapters_by_key = {a.key: a for a in ALL_ADAPTERS}

    for key in routing.selected_sources:
        adapter = adapters_by_key.get(key)
        if not adapter:
            continue
        source_results = adapter.search(query_normalized, query_vector, top_k=top_k)
        for r in source_results:
            all_results.append(
                RetrievedChunk(metadata=r.metadata, semantic_score=r.score, source_key=key)
            )

    if not all_results:
        return []

    # De-duplicate by chunk_id (a chunk could theoretically be reachable
    # via more than one source route), keeping the highest score.
    best_by_chunk = {}
    for r in all_results:
        cid = r.metadata.get("chunk_id")
        if cid not in best_by_chunk or r.semantic_score > best_by_chunk[cid].semantic_score:
            best_by_chunk[cid] = r
    deduped = list(best_by_chunk.values())

    # Hybrid keyword scoring blended in at a modest weight.
    bm25 = _bm25_scores(query_normalized, [r.metadata for r in deduped])
    for r, b in zip(deduped, bm25):
        r.bm25_score = b
        r.combined_score = (0.85 * r.semantic_score) + (0.15 * b)

    deduped.sort(key=lambda r: r.combined_score, reverse=True)
    return deduped[:top_k]
