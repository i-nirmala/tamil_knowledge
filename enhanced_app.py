from __future__ import annotations

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.config import APP_NAME, MAX_UPLOAD_MB
from src.knowledge_base import bootstrap_sample_knowledge_base, get_kb_stats, ingest_pdf
from src.memory import ConversationMemory
from src.pipeline import run_pipeline
from src.llm import _call
from ui.auth import authenticate, create_user
from chat_store import init_db, ensure_conversation, save_message, set_title_if_new, list_conversations, get_messages, delete_conversation, load_memory_rows, CLOUD_ENABLED
from cloud_auth import ENABLED as CLOUD_AUTH_ENABLED, signup as cloud_signup, login as cloud_login, user_from_token

app = FastAPI(title=APP_NAME, version="3.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8000","http://127.0.0.1:8000","http://localhost:5173","http://127.0.0.1:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
FRONTEND = ROOT / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

class ChatRequest(BaseModel):
    session_id: str
    user_email: str
    query: str
    research_mode: bool = False
    output_mode: str = "Tamil"
    access_token: str | None = None

class AuthRequest(BaseModel):
    email: str
    password: str
class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class TokenRequest(BaseModel):
    access_token: str


def citations_for_api(result):
    out=[]
    for c in result.citations:
        title = getattr(c, "book_title", "") or ""
        author = getattr(c, "author", "") or ""
        url = getattr(c, "source_url", "") or ""
        page = getattr(c, "page_number", None)
        snippet = getattr(c, "evidence_snippet", "") or ""
        # Drop placeholders and malformed records; only show understandable sources.
        if not title or title.lower() in {"unknown", "unknown source", "web source"}:
            if not url:
                continue
            title = url.split("/")[2] if "://" in url else "Web source"
        if not snippet and not url:
            continue
        out.append({"title": title, "author": author, "page": page, "snippet": snippet, "url": url})
    # De-duplicate by title/url/page.
    seen=set(); clean=[]
    for x in out:
        k=(x['title'],x['url'],x['page'])
        if k not in seen:
            seen.add(k); clean.append(x)
    return clean[:6]


def memory_for(session_id, user_email):
    memory=ConversationMemory()
    for q,a in load_memory_rows(session_id,user_email,limit=5):
        memory.add_turn(q,"","",a)
    return memory


def translate_answer(answer: str, query: str, output_mode: str) -> str:
    mode=(output_mode or "Tamil").strip()
    if mode not in {"Tamil","English","Tanglish"}:
        return answer
    instruction={
        "Tamil":"Rewrite the answer entirely in natural, clear Tamil script. Preserve factual meaning, names, numbers, citations/source titles, and do not add facts.",
        "English":"Rewrite the answer entirely in clear natural English. Preserve factual meaning, names, numbers, citations/source titles, and do not add facts.",
        "Tanglish":"Rewrite the answer in readable Tanglish (Tamil expressed in Latin script), keeping important proper nouns, book titles, numbers and URLs unchanged. Do not add facts."
    }[mode]
    r=_call([{"role":"system","content":"You are a precise response-language formatter."},{"role":"user","content":f"{instruction}\n\nQuestion:\n{query}\n\nAnswer:\n{answer}"}],0.15,1800)
    return r.text.strip() if r.success and r.text.strip() else answer

@app.on_event("startup")
def startup():
    init_db()
    try: bootstrap_sample_knowledge_base()
    except Exception: pass

@app.get("/")
def index(): return FileResponse(FRONTEND/"index.html")
@app.get("/api/health")
def health():
    stats=get_kb_stats(); return {"status":"ok","indexed_documents":stats.get("documents",0),"cloud_storage":CLOUD_ENABLED,"cloud_auth":CLOUD_AUTH_ENABLED}

@app.post("/api/auth/login")
def login(payload: AuthRequest):
    if CLOUD_AUTH_ENABLED:
        ok,message,user,token=cloud_login(payload.email,payload.password)
        if not ok: raise HTTPException(401,message)
        if not token: return {"success":True,"message":message,"needs_verification":True,"user":{"name":(user or {}).get("user_metadata",{}).get("name","User"),"email":payload.email.strip().lower()}}
        return {"success":True,"message":message,"access_token":token,"user":{"id":(user or {}).get("id"),"name":(user or {}).get("user_metadata",{}).get("name","User"),"email":(user or {}).get("email",payload.email).strip().lower()}}
    ok,message,user=authenticate(payload.email,payload.password)
    if not ok: raise HTTPException(401,message)
    return {"success":True,"message":message,"user":{"name":user.get("name","User"),"email":payload.email.strip().lower()}}

@app.post("/api/auth/signup")
def signup(payload: SignupRequest):
    if CLOUD_AUTH_ENABLED:
        ok,message,user,token=cloud_signup(payload.name,payload.email,payload.password)
        if not ok: raise HTTPException(400,message)
        out={"success":True,"message":message,"user":{"id":(user or {}).get("id"),"name":payload.name,"email":payload.email.strip().lower()}}
        if token: out["access_token"]=token
        else: out["needs_verification"]=True
        return out
    ok,message,user=create_user(payload.name,payload.email,payload.password)
    if not ok: raise HTTPException(400,message)
    return {"success":True,"message":message,"user":{"name":user.get("name",payload.name),"email":payload.email.strip().lower()}}

def current_cloud_user(token: str | None):
    if CLOUD_AUTH_ENABLED and token:
        u=user_from_token(token)
        if not u: raise HTTPException(401,"Your session has expired. Please log in again.")
        return u
    return None

@app.get("/api/conversations")
def conversations(user_email: str, access_token: str | None = None):
    u=current_cloud_user(access_token); email=(u or {}).get("email",user_email).strip().lower(); uid=(u or {}).get("id")
    return {"conversations":list_conversations(email,uid)}

@app.get("/api/conversations/{conversation_id}")
def conversation(conversation_id: str, user_email: str, access_token: str | None = None):
    u=current_cloud_user(access_token); email=(u or {}).get("email",user_email).strip().lower(); uid=(u or {}).get("id")
    return {"messages":get_messages(conversation_id,email,uid)}

# Backward-compatible singular route for older frontend/browser sessions.
@app.get("/api/conversation/{conversation_id}")
def conversation_legacy(conversation_id: str, user_email: str, access_token: str | None = None):
    u=current_cloud_user(access_token); email=(u or {}).get("email",user_email).strip().lower(); uid=(u or {}).get("id")
    return {"messages":get_messages(conversation_id,email,uid)}

@app.delete("/api/conversations/{conversation_id}")
def remove_conversation(conversation_id: str, user_email: str, access_token: str | None = None):
    u=current_cloud_user(access_token); email=(u or {}).get("email",user_email).strip().lower(); uid=(u or {}).get("id")
    delete_conversation(conversation_id,email,uid); return {"success":True}

@app.post("/api/chat")
def chat(payload: ChatRequest):
    u=current_cloud_user(payload.access_token); email=(u or {}).get("email",payload.user_email).strip().lower(); uid=(u or {}).get("id")
    if not email: raise HTTPException(400,"user_email is required")
    if not payload.session_id: raise HTTPException(400,"session_id is required")
    ensure_conversation(payload.session_id,email,payload.query[:80] or "New conversation",uid)
    memory=ConversationMemory()
    for q,a in load_memory_rows(payload.session_id,email,5,uid): memory.add_turn(q,"","",a)
    result=run_pipeline(payload.query,memory,payload.research_mode)
    citations=citations_for_api(result)
    if not result.success:
        return {"success":False,"answer":"","error":result.error,"citations":citations}
    answer=translate_answer(result.answer,payload.query,payload.output_mode)
    save_message(payload.session_id,email,"user",payload.query,payload.output_mode,[],uid)
    save_message(payload.session_id,email,"assistant",answer,payload.output_mode,citations,uid)
    set_title_if_new(payload.session_id,email,payload.query,uid)
    return {"success":True,"answer":answer,"citations":citations,"output_mode":payload.output_mode,"trace":{"mode":result.trace.answer_mode if result.trace else "general","documents_searched":result.trace.documents_searched if result.trace else 0}}

@app.delete("/api/session/{session_id}")
def clear_session(session_id: str, user_email: str, access_token: str | None = None):
    u=current_cloud_user(access_token); email=(u or {}).get("email",user_email).strip().lower(); uid=(u or {}).get("id")
    delete_conversation(session_id,email,uid); return {"success":True}

@app.get("/api/history/{session_id}")
def history(session_id: str,user_email: str, access_token: str | None = None):
    u=current_cloud_user(access_token); email=(u or {}).get("email",user_email).strip().lower(); uid=(u or {}).get("id")
    return {"history":get_messages(session_id,email,uid)}

@app.get("/api/knowledge")
def knowledge():
    stats=get_kb_stats(); records=[]
    for r in stats.get("records",[]): records.append({"title":r.title,"author":r.author,"pages":r.pages,"chunks":r.chunks,"type":r.doc_type,"added_at":r.added_at})
    return {"documents":stats.get("documents",0),"pages":stats.get("pages",0),"chunks":stats.get("chunks",0),"vectors":stats.get("vectors",0),"records":records}

@app.post("/api/knowledge/upload")
async def upload_pdf(file: UploadFile=File(...),title: str=Form(""),author: str=Form("Unknown")):
    if not file.filename.lower().endswith(".pdf"): raise HTTPException(400,"Only PDF files are supported.")
    contents=await file.read()
    if len(contents)>MAX_UPLOAD_MB*1024*1024: raise HTTPException(413,f"File exceeds {MAX_UPLOAD_MB} MB limit.")
    tmp=Path(tempfile.gettempdir())/f"code_bloom_{uuid.uuid4().hex}.pdf"
    try:
        tmp.write_bytes(contents)
        result=ingest_pdf(str(tmp),title.strip() or Path(file.filename).stem,author.strip() or "Unknown",source_filename=file.filename)
        if not result.success: raise HTTPException(400,result.message)
        return {"success":True,"message":result.message,"document":result.document.__dict__ if result.document else None}
    finally: tmp.unlink(missing_ok=True)

@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/") or path.startswith("assets/"): raise HTTPException(404)
    return FileResponse(FRONTEND/"index.html")

if __name__=="__main__":
    import uvicorn
    uvicorn.run("enhanced_app:app",host="127.0.0.1",port=8000,reload=False)
