"""Reusable UI components. UI-only changes; all AI/RAG logic remains in src/."""

import html
from typing import List
import streamlit as st

from src.citation import Citation
from src.config import APP_NAME, APP_TAGLINE, APP_ICON, groq_configured, GROQ_MODEL
from src.pipeline import KnowledgeTrace
from src.reranker import RankedChunk
from src.research_mode import SourceComparison
from src.utils import format_score


def render_topbar(user_name: str = "") -> None:
    st.markdown(
        f'''<div class="cb-topbar">
          <div class="cb-topbrand"><div class="mark">✦</div><div><b>{APP_NAME}</b><small>தமிழ் அறிவுக் களஞ்சியம் · Tamil Knowledge Navigator</small></div></div>
          <div style="text-align:right"><b>{html.escape(user_name or "Explorer")}</b><small style="display:block;color:#9aa7b4">Tamil-first knowledge space</small></div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render a polished page header with reliable in-session back navigation."""
    page = st.session_state.get("current_page", "")
    if page != "⌂ Home · முகப்பு":
        left, right = st.columns([0.12, 0.88], vertical_alignment="center")
        with left:
            if st.button("←", key=f"page_back_{page}", help="Go to previous page"):
                from ui.navigation import go_back
                go_back()
        with right:
            st.markdown(
                "<div class='cb-header cb-header-compact'>"
                "<div class='cb-header-orb'>✦</div><div>"
                f"<h1>தமிழ் அறிவுக் களஞ்சியம்</h1><p>{APP_NAME} · {APP_TAGLINE}</p>"
                "<div class='cb-motto'>கேள்வி → தேடல் → சான்று → சரிபார்ப்பு → தெளிவான பதில்</div>"
                "</div></div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            "<div class='cb-header'>"
            "<div class='cb-header-orb'>✦</div><div>"
            f"<h1>தமிழ் அறிவுக் களஞ்சியம்</h1><p>{APP_NAME} · {APP_TAGLINE}</p>"
            "<div class='cb-motto'>கேள்வி → தேடல் → சான்று → சரிபார்ப்பு → தெளிவான பதில்</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )


def render_card_title(title: str) -> None:
    st.markdown(f'<div class="cb-card-title">{html.escape(title)}</div>', unsafe_allow_html=True)


def render_divider() -> None:
    st.markdown('<hr class="cb-divider"/>', unsafe_allow_html=True)


def render_system_status(kb_stats: dict, source_status: dict, embeddings_loaded: bool) -> None:
    render_card_title("System Status · அமைப்பு நிலை")
    groq_ok = groq_configured()
    kb_ok = kb_stats.get("documents", 0) > 0
    index_ok = kb_stats.get("vectors", 0) > 0

    def line(label, ok, ok_text, bad_text):
        icon = "●" if ok else "○"
        color = "#83d0aa" if ok else "#d8a74a"
        value = ok_text if ok else bad_text
        st.markdown(f'<div class="cb-status-line"><span>{html.escape(label)}</span><span style="color:{color};font-weight:700">{icon} {html.escape(value)}</span></div>', unsafe_allow_html=True)

    line("Groq API", groq_ok, "Ready", "Key missing")
    line("Knowledge Base", kb_ok, "Ready", "Empty")
    line("FAISS Index", index_ok, "Ready", "Not built")
    line("Embeddings", embeddings_loaded, "Loaded", "Not loaded")
    st.markdown(f'<div class="cb-status-line"><span>Documents</span><span style="font-weight:700">{kb_stats.get("documents",0)}</span></div>', unsafe_allow_html=True)

    if not groq_ok:
        st.warning("GROQ_API_KEY is missing. Add it to .env to enable answer generation.")

    with st.expander("Knowledge Sources · அறிவு மூலங்கள்"):
        for _, info in source_status.items():
            st.markdown(f'<div class="cb-status-line"><span>{html.escape(info["name"])}</span><span class="cb-small">{html.escape(info["status"])}</span></div>', unsafe_allow_html=True)
    st.caption(f"Model: `{GROQ_MODEL}`")


def render_query_intelligence(qi) -> None:
    render_card_title("Query Intelligence · கேள்வி புரிதல்")
    cols = st.columns(4)
    cols[0].metric("மொழி", qi.language)
    cols[1].metric("Intent", qi.intent)
    cols[2].metric("Topic", qi.topic)
    cols[3].metric("Entity", qi.entity or "—")
    pills = [
        ("Evidence required: Yes" if qi.evidence_required else "Evidence required: No", "cb-pill"),
        ("Follow-up question" if qi.is_followup else "New question", "cb-pill cb-pill-amber" if qi.is_followup else "cb-pill cb-pill-grey"),
    ]
    st.markdown("".join(f'<span class="{c}">{html.escape(t)}</span>' for t,c in pills), unsafe_allow_html=True)
    if qi.normalized_query != qi.original_query:
        with st.expander("Normalized query · தேடலுக்கான மாற்றிய கேள்வி"):
            st.code(qi.normalized_query, language=None)


def render_answer(answer: str, insufficient: bool = False) -> None:
    render_card_title("Answer · பதில்")
    if insufficient:
        st.markdown(f'<div class="cb-answer-warning">{answer}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="cb-answer">', unsafe_allow_html=True)
        st.markdown(answer)
        st.markdown('</div>', unsafe_allow_html=True)


def render_evidence(ranked_chunks: List[RankedChunk]) -> None:
    if not ranked_chunks:
        return
    render_card_title(f"Evidence · ஆதாரம் ({len(ranked_chunks)})")
    st.caption("The passages below are retrieved evidence, not generated text.")
    for i, chunk in enumerate(ranked_chunks, start=1):
        m = chunk.metadata
        label = f"#{i} · {m.get('book_title','Unknown')} · Page {m.get('page_number','—')} · Relevance {format_score(chunk.relevance_score)}"
        with st.expander(label, expanded=(i == 1)):
            c1,c2,c3 = st.columns(3)
            c1.markdown(f'<div class="cb-meta-row"><b>Book:</b> {html.escape(str(m.get("book_title","—")))}</div><div class="cb-meta-row"><b>Author:</b> {html.escape(str(m.get("author","—")))}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="cb-meta-row"><b>Chapter:</b> {html.escape(str(m.get("chapter") or "—"))}</div><div class="cb-meta-row"><b>Page:</b> {html.escape(str(m.get("page_number","—")))}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="cb-meta-row"><b>Source:</b> {html.escape(str(m.get("source_filename","—")))}</div><div class="cb-meta-row"><b>Route:</b> {html.escape(chunk.source_key)}</div>', unsafe_allow_html=True)
            st.progress(min(1.0, max(0.0, chunk.relevance_score)))
            st.caption(f"Similarity relevance {format_score(chunk.relevance_score)} · semantic {chunk.semantic_score:.2f} · lexical {chunk.lexical_overlap:.2f}")
            st.markdown(f'<div class="cb-evidence-text">{html.escape(m.get("text", ""))}</div>', unsafe_allow_html=True)


def render_citations(citations: List[Citation]) -> None:
    if not citations:
        return
    render_card_title("Citations · மேற்கோள்கள்")
    for c in citations:
        st.markdown(f'''<div class="cb-card"><div class="cb-meta-row"><b>Book:</b> {html.escape(c.book_title)}</div><div class="cb-meta-row"><b>Author:</b> {html.escape(c.author)}</div><div class="cb-meta-row"><b>Chapter:</b> {html.escape(c.chapter)}</div><div class="cb-meta-row"><b>Page:</b> {html.escape(str(c.page_number))}</div><div class="cb-meta-row"><b>Relevance:</b> {html.escape(c.relevance)}</div></div>''', unsafe_allow_html=True)


def render_knowledge_trace(trace: KnowledgeTrace) -> None:
    if trace is None:
        return
    qi = trace.query_intelligence
    verdict = trace.evidence_verdict
    with st.expander("🔎 Knowledge Trace · அறிவு தேடல் தடம்", expanded=False):
        steps = [
            ("User Query", qi.original_query, True),
            ("Language Detection", qi.language, True),
            ("Query Understanding", f"Intent: {qi.intent} · Topic: {qi.topic}", True),
            ("Entity Recognition", qi.entity or "No known entity matched", True),
            ("Knowledge Routing", ", ".join(trace.routing.selected_sources) or "No source available", bool(trace.routing.selected_sources)),
            ("Source Discovery", f"{trace.documents_searched} document(s) searched", trace.documents_searched > 0),
            ("Semantic Retrieval", f"{trace.chunks_retrieved} chunk(s) retrieved", trace.chunks_retrieved > 0),
            ("Reranking", f"{trace.chunks_after_rerank} chunk(s) after reranking", trace.chunks_after_rerank > 0),
            ("Evidence Verification", "✓ Sufficient" if verdict.sufficient else "⚠ Insufficient", verdict.sufficient),
            ("Grounded Answer", "✓ Generated" if trace.answer_generated else "Not generated", trace.answer_generated),
            ("Citation", "✓ Page-level citations attached" if trace.answer_generated else "—", trace.answer_generated),
        ]
        for idx,(label,value,ok) in enumerate(steps,1):
            cls="cb-trace-dot" if ok else "cb-trace-dot cb-trace-dot-off"
            st.markdown(f'<div class="cb-trace-step"><div class="{cls}">{idx}</div><div><div class="cb-trace-label">{html.escape(label)}</div><div class="cb-trace-value">{html.escape(str(value))}</div></div></div>', unsafe_allow_html=True)
        render_divider()
        st.markdown("**Routing reasoning**")
        st.caption(trace.routing.reasoning)
        st.markdown("**Evidence verdict**")
        st.caption(verdict.reason)


def render_source_comparison(comparison: SourceComparison) -> None:
    render_card_title("Compare Sources · மூல ஒப்பீடு")
    if not comparison.possible:
        st.info(comparison.message)
        return
    st.caption(comparison.message)
    col1,col2=st.columns(2)
    with col1:
        st.markdown("**Common points**")
        for p in comparison.common_points or ["No strong overlap found."]:
            st.markdown(f"- {p}")
    with col2:
        st.markdown("**Differences**")
        for d in comparison.differences or ["No distinguishing content found."]:
            st.markdown(f"- {d}")
