"""UI pages. The existing src/ RAG/model pipeline is intentionally untouched."""
import base64
import html
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.config import APP_NAME, BOOKS_DIR, MAX_UPLOAD_MB, GROQ_API_KEY, GROQ_MODEL, groq_configured
from src.knowledge_base import get_kb_stats, ingest_pdf
from src.pipeline import run_pipeline
from src.research_mode import compare_sources
from ui.navigation import navigate, go_back
from ui.voice import voice_input
from ui.components import (
    render_answer, render_card_title, render_citations, render_divider,
    render_evidence, render_header, render_knowledge_trace,
    render_query_intelligence, render_source_comparison,
)

LANGUAGES = {"Tamil": "ta", "English": "en", "Tanglish": "tanglish"}


def _translate_answer(text: str, target: str) -> str:
    if target == "English":
        instruction = "Translate the answer into clear, natural English. Preserve names, factual details, citations and structure. Do not add new facts."
    elif target == "Tamil":
        instruction = "Translate the answer into natural, readable Tamil script. Preserve names, factual details, citations and structure. Do not add new facts."
    else:
        instruction = "Rewrite the answer in clear Tanglish: Tamil language written mainly using Latin/English letters. Preserve factual details, names, citations and structure. Do not add new facts."
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=2200,
            messages=[
                {"role": "system", "content": "You are a faithful multilingual answer formatter. Do not change facts."},
                {"role": "user", "content": f"{instruction}\n\nANSWER:\n{text}"},
            ],
        )
        return response.choices[0].message.content or text
    except Exception:
        return text


def _speak(text: str, lang: str) -> None:
    safe = base64.b64encode(text.encode("utf-8")).decode("ascii")
    locale = {"Tamil": "ta-IN", "English": "en-IN", "Tanglish": "ta-IN"}.get(lang, "en-IN")
    components.html(f"""
    <script>
    const text = decodeURIComponent(escape(window.atob('{safe}')));
    const u = new SpeechSynthesisUtterance(text);
    u.lang = '{locale}'; u.rate = 0.92; u.pitch = 1.0;
    window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);
    </script>
    <div style='font:600 12px Arial;color:#1557a6;padding:2px 0'>🔊 Reading answer aloud…</div>
    """, height=30)


def _history_rail() -> None:
    st.markdown('<div class="cb-history-rail"><h3>History · வரலாறு</h3><p>Click a question to reopen it.</p>', unsafe_allow_html=True)
    if not st.session_state.transcript:
        st.caption("No questions yet.")
    else:
        for i, turn in reversed(list(enumerate(st.session_state.transcript))):
            label = turn["query"][:46] + ("…" if len(turn["query"]) > 46 else "")
            if st.button(f"{i+1:02d}  {label}", use_container_width=True, key=f"rail_hist_{i}"):
                st.session_state.chat_input = turn["query"]
                navigate("✦ Ask · கேள்")
    st.markdown('</div>', unsafe_allow_html=True)



def _keyboard_callback(char: str) -> None:
    st.session_state.chat_input = st.session_state.get("chat_input", "") + char


def _render_tamil_keyboard() -> None:
    if not st.session_state.get("show_tamil_keyboard", False):
        return

    # Complete Tamil keyboard: 12 uyir, 18 mei, 216 uyirmei + aytham.
    uyir = ["அ","ஆ","இ","ஈ","உ","ஊ","எ","ஏ","ஐ","ஒ","ஓ","ஔ"]
    mei = ["க்","ங்","ச்","ஞ்","ட்","ண்","த்","ந்","ப்","ம்","ய்","ர்","ல்","வ்","ழ்","ள்","ற்","ன்"]
    aytham = ["ஃ"]
    # Tamil uyirmei formation: consonant base + vowel sign.
    signs = ["", "ா", "ி", "ீ", "ு", "ூ", "ெ", "ே", "ை", "ொ", "ோ", "ௌ"]
    bases = ["க","ங","ச","ஞ","ட","ண","த","ந","ப","ம","ய","ர","ல","வ","ழ","ள","ற","ன"]
    uyirmei=[]
    for b in bases:
        for sign in signs:
            uyirmei.append(b+sign)

    st.markdown(
        '<div class="cb-keyboard"><div class="cb-keyboard-title">தமிழ் Keyboard · முழுமையான தமிழ் எழுத்துக்கள்</div>'
        '<div class="cb-keyboard-sub">குறில் · நெடில் · உயிர் · மெய் · உயிர்மெய் · ஆய்தம்</div>',
        unsafe_allow_html=True,
    )
    tabs = st.tabs(["உயிர் · Kuril/Nedil", "மெய் · Mei", "உயிர்மெய் · Uyirmei"])
    with tabs[0]:
        st.caption("குறில்: அ இ உ எ ஒ  ·  நெடில்: ஆ ஈ ஊ ஏ ஓ  ·  இரட்டுயிர்: ஐ ஔ")
        vowel_groups = [uyir[:5], uyir[5:10], uyir[10:]]
        for row_idx,row in enumerate(vowel_groups):
            cols=st.columns(len(row))
            for idx,key in enumerate(row):
                with cols[idx]:
                    st.button(key,key=f"tam_vowel_{row_idx}_{idx}",use_container_width=True,on_click=_keyboard_callback,args=(key,))
    with tabs[1]:
        for row_idx in range(0,len(mei),9):
            row=mei[row_idx:row_idx+9]
            cols=st.columns(len(row))
            for idx,key in enumerate(row):
                with cols[idx]:
                    st.button(key,key=f"tam_mei_{row_idx}_{idx}",use_container_width=True,on_click=_keyboard_callback,args=(key,))
        st.button("ஃ  ஆய்தம்",key="tam_aytham",use_container_width=True,on_click=_keyboard_callback,args=(aytham[0],))
    with tabs[2]:
        for row_idx in range(0,len(uyirmei),18):
            row=uyirmei[row_idx:row_idx+18]
            cols=st.columns(9)
            for idx,key in enumerate(row):
                with cols[idx%9]:
                    st.button(key,key=f"tam_uyirmei_{row_idx}_{idx}",use_container_width=True,on_click=_keyboard_callback,args=(key,))
    st.button("⌫ Backspace",key="tam_backspace",on_click=lambda: st.session_state.__setitem__("chat_input", st.session_state.get("chat_input","")[:-1]),use_container_width=True)
    st.markdown('</div>',unsafe_allow_html=True)

def page_home() -> None:
    user = st.session_state.get("user_name") or "Explorer"
    try:
        stats = get_kb_stats()
    except Exception:
        stats = {"documents": 0, "pages": 0, "chunks": 0, "vectors": 0, "records": []}
    st.markdown(f'''<section class="cb-dashboard-hero"><div class="cb-dashboard-kicker">CODE BLOOM · TAMIL KNOWLEDGE SPACE</div><h2>Vanakkam, {html.escape(user)} 👋</h2><p>Tamil ilakkiyam, varalaru, mozhi, panpaadu matrum aavanangalai ore idathil thedi — aadharathudan purindhukollungal.</p></section>''', unsafe_allow_html=True)
    st.markdown('<div class="cb-dashboard-grid">'
                f'<div class="cb-stat-card"><span class="cb-stat-icon">▣</span><span class="cb-stat-value">{stats.get("documents",0):,}</span><span class="cb-stat-label">Documents · ஆவணங்கள்</span></div>'
                f'<div class="cb-stat-card"><span class="cb-stat-icon">▤</span><span class="cb-stat-value">{stats.get("pages",0):,}</span><span class="cb-stat-label">Pages · பக்கங்கள்</span></div>'
                f'<div class="cb-stat-card"><span class="cb-stat-icon">◈</span><span class="cb-stat-value">{stats.get("chunks",0):,}</span><span class="cb-stat-label">Evidence chunks · ஆதாரங்கள்</span></div>'
                f'<div class="cb-stat-card"><span class="cb-stat-icon">✦</span><span class="cb-stat-value">{stats.get("vectors",0):,}</span><span class="cb-stat-label">Vectors · குறியீடுகள்</span></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="cb-section-label"><b>தமிழ் உலகம் · Explore Tamil culture</b><span>Animated visual heritage</span></div>', unsafe_allow_html=True)
    culture_dir = Path(__file__).resolve().parents[1] / "assets" / "culture"
    cards = [("temple","சிற்பங்கள்","Temple sculpture & heritage"),("dance","கலை & நடனம்","Classical dance"),("silambam","சிலம்பம்","Martial heritage"),("thiruvalluvar","திருவள்ளுவர்","Tamil literature & wisdom")]
    cols = st.columns(4)
    for col,(slug,title,subtitle) in zip(cols,cards):
        with col:
            asset=culture_dir/f"{slug}.svg"
            uri=""
            if asset.exists(): uri=f"data:image/svg+xml;base64,{base64.b64encode(asset.read_bytes()).decode('ascii')}"
            st.markdown(f'<div class="cb-culture-card"><div class="cb-culture-image"><img src="{uri}" alt="{html.escape(title)}"></div><b>{html.escape(title)}</b><span>{html.escape(subtitle)}</span></div>',unsafe_allow_html=True)
    a,b,c=st.columns([1.4,1,1])
    with a:
        st.markdown('<div class="cb-action-card"><b>✦ Ask with evidence</b><span>Question → retrieval → verification → cited answer.</span></div>',unsafe_allow_html=True)
        if st.button("Ask a question  →",type="primary",use_container_width=True,key="dash_ask"): navigate("✦ Ask · கேள்")
    with b:
        st.markdown('<div class="cb-action-card"><b>◷ History</b><span>Open previous questions and full answers.</span></div>',unsafe_allow_html=True)
        if st.button("Open history",use_container_width=True,key="dash_history"): navigate("◷ History · வரலாறு")
    with c:
        st.markdown('<div class="cb-action-card"><b>↑ Add knowledge</b><span>Upload Tamil books and PDFs.</span></div>',unsafe_allow_html=True)
        if st.button("Upload PDF",use_container_width=True,key="dash_upload"): navigate("↑ Upload · பதிவேற்றம்")


def _render_result(result, query: str, research_mode: bool) -> None:
    st.session_state.last_result = result
    st.session_state.last_query = query
    st.session_state.base_answer = result.answer
    st.session_state.answer_language = st.session_state.get("answer_language", "Tamil")
    st.session_state.display_answer = result.answer
    if not result.success:
        st.error(result.error or "Something went wrong.")
        if result.trace: render_knowledge_trace(result.trace)
        return
    if result.trace: render_query_intelligence(result.trace.query_intelligence); render_divider()
    _render_answer_controls(result, research_mode)
    if not result.insufficient_evidence:
        render_divider(); render_evidence(result.ranked_chunks)
        render_divider(); render_citations(result.citations)
        if research_mode and result.citations:
            render_divider(); render_source_comparison(compare_sources(result.citations))
    render_divider(); render_knowledge_trace(result.trace)
    st.session_state.transcript.append({"query":query,"answer":result.answer,"insufficient":result.insufficient_evidence})


def _render_answer_controls(result, research_mode=False) -> None:
    render_card_title("Answer · பதில்")
    st.markdown('<div class="cb-lang-row">Choose answer language / பதில் மொழியை தேர்வு செய்யவும்</div>',unsafe_allow_html=True)
    l1,l2,l3,l4=st.columns([1,1,1,1.25])
    current=st.session_state.get("answer_language","Tamil")
    if l1.button("தமிழ்" + (" ✓" if current=="Tamil" else ""),key="ans_ta",use_container_width=True):
        st.session_state.answer_language="Tamil"; st.session_state.display_answer=_translate_answer(st.session_state.base_answer,"Tamil"); st.rerun()
    if l2.button("English" + (" ✓" if current=="English" else ""),key="ans_en",use_container_width=True):
        st.session_state.answer_language="English"; st.session_state.display_answer=_translate_answer(st.session_state.base_answer,"English"); st.rerun()
    if l3.button("Tanglish" + (" ✓" if current=="Tanglish" else ""),key="ans_tg",use_container_width=True):
        st.session_state.answer_language="Tanglish"; st.session_state.display_answer=_translate_answer(st.session_state.base_answer,"Tanglish"); st.rerun()
    if l4.button("🔊 Read answer aloud",key="speak_answer",use_container_width=True):
        _speak(st.session_state.get("display_answer",result.answer),current)
    answer=st.session_state.get("display_answer",result.answer)
    render_answer(answer, insufficient=result.insufficient_evidence)


def _run_and_render(query: str, research_mode: bool) -> None:
    with st.spinner("Discovering knowledge, verifying evidence… · அறிவைத் தேடி சரிபார்க்கிறது…"):
        result = run_pipeline(query=query, memory=st.session_state.memory, research_mode=research_mode)
    st.session_state.last_result = result
    st.session_state.last_query = query
    if result.success:
        st.session_state.base_answer = result.answer
        st.session_state.display_answer = result.answer
        st.session_state.answer_language = "Tamil"
        st.session_state.transcript.append({"query": query, "answer": result.answer, "insufficient": result.insufficient_evidence})


def _query_form(key_prefix: str, research_mode: bool=False) -> None:
    if key_prefix == "chat":
        st.session_state.setdefault("answer_language","Tamil")
        st.session_state.setdefault("show_tamil_keyboard",False)
    pending=st.session_state.pop(f"{key_prefix}_pending","")
    if pending: st.session_state[f"{key_prefix}_input"]=pending
    query=st.text_area("Ask · கேளுங்கள்",height=120,key=f"{key_prefix}_input",placeholder="Tamil, English, Tanglish or mixed-language question…")
    if key_prefix in ("chat", "research"):
        vlang = "ta-IN" if st.session_state.get("answer_language","Tamil") == "Tamil" else "en-IN"
        voice_text = voice_input(key=f"{key_prefix}_voice", language=vlang)
        if voice_text and voice_text != st.session_state.get("last_voice_text",""):
            st.session_state.last_voice_text = voice_text
            st.session_state[f"{key_prefix}_input"] = voice_text
            st.rerun()
    if key_prefix=="chat":
        if st.button("⌨️ Tamil Keyboard · தமிழ் Keyboard",key="toggle_tamil_keyboard",use_container_width=True):
            st.session_state.show_tamil_keyboard=not st.session_state.get("show_tamil_keyboard",False); st.rerun()
        _render_tamil_keyboard()
    c1,c2=st.columns([1.4,1])
    submitted=c1.button("🔍 Search & Verify" if not research_mode else "🔬 Research",type="primary",key=f"{key_prefix}_submit",use_container_width=True)
    if c2.button("Clear · அழி",key=f"{key_prefix}_clear",use_container_width=True):
        st.session_state.memory.clear(); st.session_state.transcript=[]; st.session_state.pop("last_result",None); st.rerun()
    if submitted:
        if not query.strip(): st.warning("Please enter a question first. · கேள்வியை உள்ளிடுங்கள்.")
        else: _run_and_render(query.strip(),research_mode)


def page_chat() -> None:
    render_header()
    left,right=st.columns([3.2,1],gap="large")
    with left:
        if not groq_configured(): st.warning("Groq API key missing. Add GROQ_API_KEY to .env.")
        _query_form("chat",False)
        result = st.session_state.get("last_result")
        if result is not None and st.session_state.get("last_query"):
            render_divider()
            _render_answer_controls(result, False)
            if result.trace:
                render_divider(); render_query_intelligence(result.trace.query_intelligence)
            if not result.success:
                st.error(result.error or "Something went wrong.")
            elif not result.insufficient_evidence:
                render_divider(); render_evidence(result.ranked_chunks)
                render_divider(); render_citations(result.citations)
            if result.trace:
                render_divider(); render_knowledge_trace(result.trace)
    with right:
        _history_rail()


def page_history() -> None:
    render_header(); render_card_title("History · கேள்வி வரலாறு")
    if not st.session_state.transcript:
        st.info("Your questions will appear here after you use Ask.")
        return
    for i,turn in reversed(list(enumerate(st.session_state.transcript))):
        title=turn["query"][:110]+("…" if len(turn["query"])>110 else "")
        with st.expander(f"{i+1:02d} · {title}",expanded=False):
            st.markdown(f'<div class="cb-history-item"><div class="cb-history-q">{html.escape(turn["query"])}</div><div class="cb-history-meta">Stored in this session</div></div>',unsafe_allow_html=True)
            render_answer(turn["answer"],turn["insufficient"])


def page_research() -> None:
    render_header(); st.info("Research Mode returns detailed evidence and source comparison."); _query_form("research",True)


def page_knowledge_base() -> None:
    render_header(); stats=get_kb_stats(); render_card_title("Knowledge Base · அறிவுக் களஞ்சியம்")
    c1,c2,c3,c4=st.columns(4); c1.metric("Documents",f"{stats['documents']:,}"); c2.metric("Pages",f"{stats['pages']:,}"); c3.metric("Chunks",f"{stats['chunks']:,}"); c4.metric("Vectors",f"{stats['vectors']:,}")
    render_divider(); render_card_title("Documents · ஆவணங்கள்")
    if not stats["records"]: st.info("No documents yet. Open Upload Documents to add a PDF."); return
    df=pd.DataFrame([{"Title":r.title,"Author":r.author,"Type":r.doc_type,"Pages":r.pages,"Chunks":r.chunks,"Indexed":"✓" if r.indexed else "—","Added":r.added_at.replace("T"," ")} for r in stats["records"]])
    st.dataframe(df,use_container_width=True,hide_index=True)


def page_upload() -> None:
    render_header(); render_card_title("Upload Documents · ஆவணங்களை பதிவேற்றுக")
    st.caption(f"PDF files only, up to {MAX_UPLOAD_MB} MB. Text-based PDFs work best.")
    uploaded=st.file_uploader("Choose a PDF",type=["pdf"],key="uploader")
    c1,c2=st.columns(2); title=c1.text_input("Book / document title",key="up_title"); author=c2.text_input("Author",value="Unknown",key="up_author")
    c3,c4=st.columns(2); chapter=c3.text_input("Chapter (optional)",key="up_chapter"); doc_type=c4.selectbox("Source type",["book","pdf"],key="up_type")
    if st.button("📥 Process & Index · செயலாக்கி சேர்க்கவும்",type="primary",key="up_submit"):
        if uploaded is None: st.warning("Please choose a PDF file first."); return
        if not title.strip(): st.warning("Please give the document a title."); return
        size_mb=uploaded.size/(1024*1024)
        if size_mb>MAX_UPLOAD_MB: st.error(f"File is {size_mb:.1f} MB, exceeding {MAX_UPLOAD_MB} MB."); return
        dest=Path(BOOKS_DIR)/uploaded.name
        try: dest.write_bytes(uploaded.getbuffer())
        except Exception as exc: st.error(f"Could not save file: {exc}"); return
        with st.spinner("Extracting text, chunking, embedding and indexing…"):
            result=ingest_pdf(file_path=str(dest),title=title.strip(),author=author.strip() or "Unknown",chapter=chapter.strip(),doc_type=doc_type,source_filename=uploaded.name)
        if not result.success: st.error(result.message); return
        doc=result.document; st.success(f"{doc.title} is now searchable.")
        for text in [f"Pages processed — {doc.pages}",f"Chunks created — {doc.chunks}","Embeddings generated","FAISS index updated","Document added to Knowledge Base"]: st.write("✓ "+text)
        st.cache_resource.clear()


def page_about() -> None:
    render_header(); render_card_title("About · திட்டம் பற்றி")
    st.markdown('<div class="cb-card"><h3>தமிழ் அறிவுக் களஞ்சியம்</h3><p style="color:#6f8091;line-height:1.8">A Tamil-first multilingual Universal Knowledge Assistant. The UI supports Tamil, English, Tanglish, Tamil keyboard input, answer translation and optional answer playback while the existing retrieval, reranking, evidence verification and citation pipeline remains unchanged.</p><p><b>Query → Language Detection → Knowledge Routing → Retrieval → Reranking → Evidence Verification → Grounded Answer → Citations</b></p></div>',unsafe_allow_html=True)
