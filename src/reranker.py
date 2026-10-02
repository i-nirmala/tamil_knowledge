"""
Code Bloom — Reranker
------------------------------------------------
Deliberately kept as a *separate* module from retrieval (per spec) so
the two responsibilities never get mixed together.

Why not a cross-encoder? Practical cross-encoder models (e.g. MS MARCO
MiniLM cross-encoders) are English-only and would silently degrade
quality on Tamil/Tanglish queries, which is the opposite of what this
project stands for. Instead, this reranker uses a transparent,
multilingual-safe combination of:

  1. semantic similarity (cosine, from the embedding model — already
     multilingual)
  2. lexical/entity overlap between the query and the candidate chunk
     (rewards chunks that literally mention the entity/topic the user
     asked about, which the embedding alone can under-weight for short
     Tamil queries)

The result is a "relevance/evidence score", clearly NOT described as a
probability, in the [0, 1] range.
"""

import re
from dataclasses import dataclass
from typing import List

from src.config import TOP_K_RERANK
from src.retriever import RetrievedChunk

#: How strongly literal term overlap boosts the semantic score.
#: 0.5 means a chunk containing every query term scores 50% higher than
#: its raw semantic similarity alone (capped at 1.0).
LEXICAL_BOOST_WEIGHT = 0.5


@dataclass
class RankedChunk:
    metadata: dict
    relevance_score: float
    semantic_score: float
    lexical_overlap: float
    source_key: str


#: Minimum shared prefix length for two tokens to count as the same word.
#: Tamil is agglutinative — case and possessive endings attach directly to
#: the stem (கல்வி "education" -> கல்வியின் "of education"), so exact string
#: matching badly under-counts real overlap. Prefix matching recovers it
#: without needing a full Tamil morphological analyser.
_STEM_PREFIX_LEN = 4


def _tokenize(text: str) -> set:
    return set(re.findall(r"[\w\u0B80-\u0BFF]+", (text or "").lower()))


def _stems(tokens: set) -> set:
    """Reduce tokens to their leading characters so inflected forms of the
    same word collapse together."""
    return {t[:_STEM_PREFIX_LEN] for t in tokens if len(t) >= _STEM_PREFIX_LEN}


def _lexical_overlap(query: str, chunk_text: str) -> float:
    """
    Fraction of query terms that appear in the chunk, counting inflected
    variants as matches. Exact matches are counted first; remaining query
    terms get a second chance via stem-prefix matching.
    """
    q_tokens = _tokenize(query)
    c_tokens = _tokenize(chunk_text)
    if not q_tokens or not c_tokens:
        return 0.0

    exact = q_tokens & c_tokens
    remaining = q_tokens - exact

    c_stems = _stems(c_tokens)
    stem_matches = {t for t in remaining if len(t) >= _STEM_PREFIX_LEN and t[:_STEM_PREFIX_LEN] in c_stems}

    return (len(exact) + len(stem_matches)) / len(q_tokens)


def rerank(query: str, candidates: List[RetrievedChunk], top_k: int = TOP_K_RERANK) -> List[RankedChunk]:
    """Rerank retrieved candidates into a smaller, higher-precision set."""
    if not candidates:
        return []

    ranked: List[RankedChunk] = []
    for c in candidates:
        lexical = _lexical_overlap(query, c.metadata.get("text", ""))
        # Lexical overlap is applied as a multiplicative BOOST rather than
        # a weighted average. A weighted average would systematically
        # deflate every score (a perfect semantic match with zero literal
        # word overlap would be capped at 0.75), which unfairly penalises
        # cross-script matches — exactly the Tamil-query-against-Tamil-text
        # case this project exists to serve. A boost preserves the semantic
        # score's magnitude and rewards literal term overlap on top of it.
        relevance = c.combined_score * (1.0 + (LEXICAL_BOOST_WEIGHT * lexical))
        relevance = max(0.0, min(1.0, relevance))
        ranked.append(
            RankedChunk(
                metadata=c.metadata,
                relevance_score=relevance,
                semantic_score=c.semantic_score,
                lexical_overlap=lexical,
                source_key=c.source_key,
            )
        )

    ranked.sort(key=lambda r: r.relevance_score, reverse=True)
    return ranked[:top_k]
