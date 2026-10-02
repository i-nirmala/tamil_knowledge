"""
Code Bloom — Evidence Verification Layer
------------------------------------------------
Major differentiating feature: before the LLM is ever asked to
generate an answer, this module checks whether the retrieved (and
reranked) evidence is actually strong enough to support a grounded
answer.

Two paths:
  Path A (sufficient) -> evidence goes to the LLM -> grounded answer
  Path B (insufficient) -> the LLM is never called with a "make
           something up" prompt; the user is told the knowledge base
           cannot verify the answer.

We deliberately avoid ever claiming "100% hallucination-free" — the
honest framing used throughout the UI is:
  "Evidence-grounded generation with insufficient-evidence handling."
"""

from dataclasses import dataclass, field
from typing import List

from src.config import EVIDENCE_SCORE_THRESHOLD, MIN_EVIDENCE_CHUNKS
from src.reranker import RankedChunk


@dataclass
class EvidenceVerdict:
    sufficient: bool
    qualifying_chunks: List[RankedChunk] = field(default_factory=list)
    reason: str = ""
    best_score: float = 0.0
    llm_checked: bool = False  # whether stage-2 LLM verification ran


def verify_evidence(
    ranked_chunks: List[RankedChunk],
    score_threshold: float = EVIDENCE_SCORE_THRESHOLD,
    min_chunks: int = MIN_EVIDENCE_CHUNKS,
    query: str = "",
    use_llm_check: bool = True,
) -> EvidenceVerdict:
    """
    Decide whether the retrieved evidence is sufficient to ground an
    answer. Checks:
      - relevance score of the top chunk(s) against a threshold
      - the number of chunks that clear that threshold
      - that source metadata is actually present (not synthetic)
    """
    if not ranked_chunks:
        return EvidenceVerdict(
            sufficient=False,
            reason="No relevant passages were retrieved from any available knowledge source.",
        )

    qualifying = [c for c in ranked_chunks if c.relevance_score >= score_threshold]
    best_score = ranked_chunks[0].relevance_score if ranked_chunks else 0.0

    # Sanity-check that qualifying chunks actually carry source metadata
    # (defensive — should always be true given our pipeline, but a
    # missing book_title/page would mean we cannot honestly cite it).
    qualifying = [c for c in qualifying if c.metadata.get("book_title") and c.metadata.get("text")]

    if len(qualifying) >= min_chunks:
        stage1_reason = (
            f"{len(qualifying)} passage(s) met the relevance threshold "
            f"({score_threshold:.2f}) with verifiable source metadata."
        )

        # ---- Stage 2: LLM relevance check -------------------------------
        # Retrieval scores measure similarity, not answerability. A passage
        # can score highly just by sharing a subject with the question
        # (e.g. "what will Thirukkural say about 2050?" matching general
        # Thirukkural text). This second pass asks the model whether the
        # evidence actually ANSWERS the question. It is advisory: if it
        # cannot run (no API key / API error) we keep the stage-1 verdict.
        llm_checked = False
        if use_llm_check and query:
            from src.llm import verify_evidence_with_llm

            llm_verdict = verify_evidence_with_llm(
                query, [{"metadata": c.metadata} for c in qualifying]
            )
            if llm_verdict is not None:
                llm_checked = True
                if llm_verdict is False:
                    return EvidenceVerdict(
                        sufficient=False,
                        qualifying_chunks=qualifying,
                        reason=(
                            f"{stage1_reason} However, a second verification pass found that "
                            "these passages do not actually address what was asked — they only "
                            "share a subject with the question."
                        ),
                        best_score=best_score,
                        llm_checked=True,
                    )
                stage1_reason += " Confirmed by a second verification pass."

        return EvidenceVerdict(
            sufficient=True,
            qualifying_chunks=qualifying,
            reason=stage1_reason,
            best_score=best_score,
            llm_checked=llm_checked,
        )

    return EvidenceVerdict(
        sufficient=False,
        qualifying_chunks=qualifying,
        reason=(
            f"Best relevance score was {best_score:.2f}, below the required threshold "
            f"({score_threshold:.2f}), or too few passages qualified. "
            "The available knowledge sources cannot verify a confident answer."
        ),
        best_score=best_score,
    )
