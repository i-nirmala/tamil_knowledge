"""
Code Bloom — Research Mode & Source Comparison
------------------------------------------------
Implements the two answer modes described in the PPT/spec:

  Normal Mode   -> concise answer + evidence + citation
  Research Mode -> detailed summary, key findings, multiple evidence
                   passages, multiple sources, source comparison

Source comparison is generated ONLY from actual retrieved evidence —
never invented. If there isn't enough distinct-source evidence to
compare, that is stated explicitly.
"""

from dataclasses import dataclass
from typing import List

from src.citation import Citation


@dataclass
class SourceComparison:
    possible: bool
    message: str
    common_points: List[str]
    differences: List[str]


def compare_sources(citations: List[Citation]) -> SourceComparison:
    """
    Build a lightweight, evidence-only comparison across citations that
    come from different books/documents. This is a heuristic textual
    comparison (shared/unique keywords), not an LLM hallucination.
    """
    distinct_books = {}
    for c in citations:
        distinct_books.setdefault(c.book_title, []).append(c)

    if len(distinct_books) < 2:
        return SourceComparison(
            possible=False,
            message="Only one source contributed evidence for this query — not enough "
                    "distinct sources to compare.",
            common_points=[],
            differences=[],
        )

    # Very lightweight keyword-overlap based comparison, evidence-only.
    import re

    def tokens(text):
        return set(re.findall(r"[\w\u0B80-\u0BFF]{4,}", text.lower()))

    book_tokens = {
        book: set().union(*[tokens(c.full_text) for c in chunks])
        for book, chunks in distinct_books.items()
    }

    books = list(book_tokens.keys())
    common = set.intersection(*book_tokens.values()) if len(books) > 1 else set()
    common_points = [f"Both discuss: {', '.join(list(common)[:6])}"] if common else []

    differences = []
    for book in books:
        unique = book_tokens[book] - common
        if unique:
            differences.append(f"{book} uniquely mentions: {', '.join(list(unique)[:5])}")

    return SourceComparison(
        possible=True,
        message=f"Compared evidence across {len(books)} sources: {', '.join(books)}.",
        common_points=common_points,
        differences=differences,
    )
