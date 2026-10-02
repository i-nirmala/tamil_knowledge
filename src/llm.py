from dataclasses import dataclass
from typing import List, Optional
from src.config import GROQ_API_KEY,GROQ_MAX_TOKENS,GROQ_MODEL,GROQ_TEMPERATURE,groq_configured
try:
    from groq import Groq
    _GROQ_SDK_AVAILABLE=True
except Exception:
    _GROQ_SDK_AVAILABLE=False

@dataclass
class LLMResponse:
    success: bool
    text: str=""
    error: Optional[str]=None
    model: str=GROQ_MODEL

SYSTEM_PROMPT="""You are Code Bloom, a Tamil-first universal knowledge assistant.
Answer questions in Tamil, English, Tanglish, or mixed language. You can use retrieved local documents and live web sources as evidence, but you are not limited to them.
Rules:
- Give a useful answer for general knowledge, not only questions present in the local knowledge base.
- When sources are supplied, prefer them for factual claims and do not invent citations or quotations.
- If a source is uncertain or incomplete, say that briefly and then provide the best general explanation you can.
- Never claim that a fact came from a source unless it is in the supplied source text.
- For current or time-sensitive facts, rely on recent web evidence when available and say when information may change.
- For Tamil literature, language, history, culture and classical works, prefer authoritative Tamil sources when available.
- Preserve Tamil script when the user asks in Tamil. For Tanglish, clear Tamil or bilingual wording is acceptable.
- Be clear, structured and natural. Do not refuse merely because the local PDFs do not contain the answer.
"""

VERIFIER="""Decide whether the supplied evidence directly helps answer the question. Reply only SUFFICIENT or INSUFFICIENT."""

def _format_evidence(chunks):
    blocks=[]
    for i,chunk in enumerate(chunks,1):
        m=chunk.get("metadata",chunk)
        blocks.append(f"[Source {i}]\nTitle: {m.get('book_title','Unknown')}\nAuthor: {m.get('author','Unknown')}\nURL: {m.get('source_url','')}\nPage: {m.get('page_number','—')}\nText: {m.get('text','')}")
    return "\n\n".join(blocks)

def _call(messages, temperature=None, max_tokens=None):
    if not groq_configured(): return LLMResponse(False,error="Groq API key is missing. Add GROQ_API_KEY to .env.")
    if not _GROQ_SDK_AVAILABLE: return LLMResponse(False,error="The groq package is not installed.")
    try:
        client=Groq(api_key=GROQ_API_KEY)
        c=client.chat.completions.create(model=GROQ_MODEL,messages=messages,
            temperature=GROQ_TEMPERATURE if temperature is None else temperature,
            max_tokens=GROQ_MAX_TOKENS if max_tokens is None else max_tokens)
        return LLMResponse(True,text=c.choices[0].message.content or "",model=GROQ_MODEL)
    except Exception as exc:
        return LLMResponse(False,error=f"Groq API error: {exc}")

def verify_evidence_with_llm(query,evidence_chunks):
    if not groq_configured() or not _GROQ_SDK_AVAILABLE or not evidence_chunks: return None
    r=_call([{"role":"system","content":VERIFIER},{"role":"user","content":f"QUESTION:\n{query}\n\nEVIDENCE:\n{_format_evidence(evidence_chunks)}"}],0.0,8)
    if not r.success: return None
    v=r.text.strip().upper()
    if "INSUFFICIENT" in v: return False
    if "SUFFICIENT" in v: return True
    return None

def generate_answer(query,evidence_chunks,conversation_context="",research_mode=False):
    mode="detailed research answer with sections and source notes" if research_mode else "direct useful answer with concise structure"
    prompt=f"""User question:\n{query}\n\nPrevious conversation:\n{conversation_context or 'None'}\n\nRetrieved sources (may be incomplete):\n{_format_evidence(evidence_chunks) if evidence_chunks else 'No local/web evidence was retrieved.'}\n\nTask: Give a {mode}. Use retrieved sources when relevant, but if they do not answer the question, answer from your general knowledge rather than stopping. Do not fabricate citations. If web evidence is supplied, include a short Sources section with the actual URLs."""
    return _call([{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}])

def generate_grounded_answer(query,evidence_chunks,conversation_context="",research_mode=False):
    return generate_answer(query,evidence_chunks,conversation_context,research_mode)
