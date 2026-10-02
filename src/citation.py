from dataclasses import dataclass
from typing import List
from src.reranker import RankedChunk
from src.utils import format_score, truncate

@dataclass
class Citation:
    book_title:str
    author:str
    chapter:str
    page_number:int
    relevance:str
    evidence_snippet:str
    full_text:str
    source_key:str
    source_url:str=""

def build_citations(chunks:List[RankedChunk])->List[Citation]:
    out=[]
    for c in chunks:
        m=c.metadata
        out.append(Citation(m.get("book_title","Unknown"),m.get("author","Unknown"),m.get("chapter","") or "—",
            m.get("page_number",1),format_score(c.relevance_score),truncate(m.get("text",""),260),m.get("text",""),c.source_key,m.get("source_url","") ))
    return out

def citations_to_markdown(citations):
    return "\n".join(f"- **{c.book_title}** — {c.source_url or ('Page '+str(c.page_number))}" for c in citations)
