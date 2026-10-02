from dataclasses import dataclass, field
from typing import List, Optional
from src.citation import Citation, build_citations
from src.evidence_verifier import EvidenceVerdict, verify_evidence
from src.llm import LLMResponse, generate_answer
from src.memory import ConversationMemory
from src.query_engine import QueryIntelligence, analyze_query
from src.reranker import RankedChunk, rerank
from src.retriever import RetrievedChunk, retrieve
from src.router import RoutingDecision, route_query

@dataclass
class KnowledgeTrace:
    query_intelligence: QueryIntelligence
    routing: RoutingDecision
    documents_searched: int
    chunks_retrieved: int
    chunks_after_rerank: int
    evidence_verdict: EvidenceVerdict
    answer_generated: bool
    answer_mode: str="general"

@dataclass
class PipelineResult:
    success: bool
    answer: str=""
    citations: List[Citation]=field(default_factory=list)
    ranked_chunks: List[RankedChunk]=field(default_factory=list)
    trace: Optional[KnowledgeTrace]=None
    insufficient_evidence: bool=False
    error: Optional[str]=None

def run_pipeline(query:str,memory:ConversationMemory,research_mode:bool=False)->PipelineResult:
    query=(query or "").strip()
    if not query: return PipelineResult(False,error="Please enter a question.")
    qi=analyze_query(query,conversation_history=memory.as_history_dicts())
    routing=route_query(qi)
    try:
        retrieved:List[RetrievedChunk]=retrieve(qi.normalized_query,routing)
    except Exception as exc:
        retrieved=[]
        retrieval_error=str(exc)
    else: retrieval_error=""
    documents_searched=len({r.metadata.get("doc_id") for r in retrieved}) if retrieved else 0
    ranked=rerank(qi.normalized_query,retrieved)
    verdict=verify_evidence(ranked,query=query)
    citations=build_citations(ranked[:6])
    mode="grounded" if verdict.sufficient else "general"
    trace=KnowledgeTrace(qi,routing,documents_searched,len(retrieved),len(ranked),verdict,False,mode)
    if not groq_available_message():
        return PipelineResult(False,error="Groq API key is missing. Add it to .env and restart the app.",citations=citations,ranked_chunks=ranked,trace=trace)
    response:LLMResponse=generate_answer(query,[{"metadata":c.metadata} for c in ranked[:6]],memory.as_context_string(),research_mode)
    if not response.success:
        return PipelineResult(False,error=response.error,citations=citations,ranked_chunks=ranked,trace=trace)
    trace.answer_generated=True
    memory.add_turn(query=query,entity=qi.entity,topic=qi.topic,answer_summary=response.text)
    return PipelineResult(True,response.text,citations,ranked,trace,False,None)

def groq_available_message():
    from src.config import groq_configured
    return groq_configured()
