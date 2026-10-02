"""
Code Bloom — Source Adapter Base Class
------------------------------------------------
Defines the common interface every knowledge source adapter must
implement. The AI Knowledge Routing Engine (src/router.py) talks to
every source through this interface, so new sources (web, database,
digital archives, ...) can be added later without changing the router
or the retrieval pipeline.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class SourceSearchResult:
    metadata: dict
    score: float


class BaseSource(ABC):
    """Abstract interface for a pluggable knowledge source."""

    #: Human-readable name shown in the UI / Knowledge Trace
    name: str = "Base Source"

    #: Short machine-readable key used by the router ("tamil_books", "web", ...)
    key: str = "base"

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this source is actually usable right now
        (e.g. has data indexed, has network access, has credentials)."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str, query_vector, top_k: int) -> List[SourceSearchResult]:
        """Run a search against this source and return ranked results.
        `query_vector` is a pre-computed embedding of the query, passed
        in so vector-backed sources don't recompute it."""
        raise NotImplementedError

    def status_message(self) -> str:
        """Human-readable availability status for the System Status panel."""
        return "✓ Available" if self.is_available() else "⚠ Not available"
