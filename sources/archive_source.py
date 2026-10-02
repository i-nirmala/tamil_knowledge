"""
Code Bloom — Digital Archive Source Adapter (Future Scope)
------------------------------------------------
Architectural placeholder for connecting to digital archives / cultural
institution repositories (e.g. Tamil Virtual Academy, museum archives).
Wired into the Knowledge Routing Engine so future integration doesn't
require rewriting the router, but not implemented in this prototype.
"""

from typing import List

from sources.base_source import BaseSource, SourceSearchResult


class ArchiveAdapter(BaseSource):
    name = "Digital Archives"
    key = "archives"

    def is_available(self) -> bool:
        return False

    def search(self, query: str, query_vector, top_k: int) -> List[SourceSearchResult]:
        return []

    def status_message(self) -> str:
        return "⚠ Not implemented (future scope)"
