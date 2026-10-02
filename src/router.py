from dataclasses import dataclass, field
from typing import List
from sources.archive_source import ArchiveAdapter
from sources.book_source import TamilBookAdapter
from sources.database_source import DatabaseAdapter
from sources.pdf_source import PDFAdapter
from sources.web_source import WebAdapter

ALL_ADAPTERS=[TamilBookAdapter(), PDFAdapter(), WebAdapter(), DatabaseAdapter(), ArchiveAdapter()]

@dataclass
class RoutingDecision:
    selected_sources: List[str]=field(default_factory=list)
    available_sources: List[str]=field(default_factory=list)
    reasoning: str=""

def get_all_adapters(): return ALL_ADAPTERS

def get_source_status():
    return {a.key:{"name":a.name,"status":a.status_message(),"available":a.is_available()} for a in ALL_ADAPTERS}

def route_query(query_intelligence):
    available=[a for a in ALL_ADAPTERS if a.is_available()]
    keys=[a.key for a in available]
    selected=[]
    if "tamil_books" in keys: selected.append("tamil_books")
    if "pdfs" in keys: selected.append("pdfs")
    # Web is always included: the assistant is no longer limited to the bundled KB.
    if "web" in keys: selected.append("web")
    reasons=["Local documents are searched when indexed.",
             "Live web discovery is enabled so questions are not restricted to the bundled knowledge base."]
    if query_intelligence.language in ("Tamil","Tanglish","Mixed"):
        reasons.append("Tamil-aware multilingual retrieval is used for Tamil/Tanglish queries.")
    return RoutingDecision(selected_sources=selected, available_sources=keys, reasoning=" ".join(reasons))
