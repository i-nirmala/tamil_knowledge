"""
Code Bloom — Database Source Adapter (Future Scope)
------------------------------------------------
Architectural placeholder for querying structured institutional
databases (e.g. library catalog systems, university repositories).
Wired into the Knowledge Routing Engine so future integration doesn't
require rewriting the router, but not implemented in this prototype.
"""

from typing import List

from sources.base_source import BaseSource, SourceSearchResult


class DatabaseAdapter(BaseSource):
    name = "Databases"
    key = "database"

    def is_available(self) -> bool:
        return False

    def search(self, query: str, query_vector, top_k: int) -> List[SourceSearchResult]:
        return []

    def status_message(self) -> str:
        return "⚠ Not implemented (future scope)"
