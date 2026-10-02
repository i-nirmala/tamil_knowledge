from __future__ import annotations

import sys, tempfile, uuid, shutil
from pathlib import Path
from typing import Optional

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
from ui.auth import authenticate, create_user

app = FastAPI(title=APP_NAME, version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: dict[str, ConversationMemory] = {}
FRONTEND = ROOT / "frontend"
app.mount("/assets", StaticFiles(directory=FRONTEND / "assets"), name="assets")

class ChatRequest(BaseModel):
    session_id: str
    query: str
    research_mode: bool = False

class AuthRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


def get_memory(session_id: str) -> ConversationMemory:
    if not session_id:
        raise HTTPException(400, "session_id is required")
    if session_id not in sessions:
        sessions[session_id] = ConversationMemory()
    return sessions[session_id]


def serialize_result(result):
    citations = []
    for c in result.citations:
        citations.append({
            "title": getattr(c, "title", "Unknown source"),
            "author": getattr(c, "author", ""),
            "page": getattr(c, "page", None),
            "source": getattr(c, "source", ""),
            "snippet": getattr(c, "snippet", ""),
            "url": getattr(c, "url", "") or "",
        })
    trace = result.trace
    return {
        "success": result.success,
        "answer": result.answer,
        "error": result.error,
        "insufficient_evidence": result.insufficient_evidence,
        "citations": citations,
        "trace": {
            "mode": trace.answer_mode if trace else "general",
            "documents_searched": trace.documents_searched if trace else 0,
            "chunks_retrieved": trace.chunks_retrieved if trace else 0,
            "chunks_after_rerank": trace.chunks_after_rerank if trace else 0,
            "evidence_sufficient": trace.evidence_verdict.sufficient if trace else False,
        } if trace else None,
    }

@app.on_event("startup")
def startup():
    # Keep existing knowledge-base bootstrap behavior.
    try:
        bootstrap_sample_knowledge_base()
    except Exception:
        pass

@app.get("/")
def index():
    return FileResponse(FRONTEND / "index.html")

@app.get("/api/health")
def health():
    stats = get_kb_stats()
    return {"status": "ok", "demo_mode": False, "indexed_documents": stats.get("documents", 0)}

@app.post("/api/auth/login")
def login(payload: AuthRequest):
    ok, message, user = authenticate(payload.email, payload.password)
    if not ok:
        raise HTTPException(401, message)
    return {"success": True, "message": message, "user": {"name": user.get("name", "User"), "email": payload.email.strip().lower()}}

@app.post("/api/auth/signup")
def signup(payload: SignupRequest):
    ok, message, user = create_user(payload.name, payload.email, payload.password)
    if not ok:
        raise HTTPException(400, message)
    return {"success": True, "message": message, "user": {"name": user.get("name", payload.name), "email": payload.email.strip().lower()}}

@app.get("/api/history/{session_id}")
def history(session_id: str):
    memory = get_memory(session_id)
    return {"history": memory.as_history_dicts()}

@app.post("/api/chat")
def chat(payload: ChatRequest):
    memory = get_memory(payload.session_id)
    result = run_pipeline(payload.query, memory, payload.research_mode)
    return serialize_result(result)

@app.delete("/api/session/{session_id}")
def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"success": True}

@app.get("/api/knowledge")
def knowledge():
    stats = get_kb_stats()
    records = []
    for r in stats.get("records", []):
        records.append({"title": r.title, "author": r.author, "pages": r.pages, "chunks": r.chunks, "type": r.doc_type, "added_at": r.added_at})
    return {"documents": stats.get("documents", 0), "pages": stats.get("pages", 0), "chunks": stats.get("chunks", 0), "vectors": stats.get("vectors", 0), "records": records}

@app.post("/api/knowledge/upload")
async def upload_pdf(file: UploadFile = File(...), title: str = Form(""), author: str = Form("Unknown")):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {MAX_UPLOAD_MB} MB limit.")
    tmp = Path(tempfile.gettempdir()) / f"code_bloom_{uuid.uuid4().hex}.pdf"
    try:
        tmp.write_bytes(contents)
        result = ingest_pdf(str(tmp), title.strip() or Path(file.filename).stem, author.strip() or "Unknown", source_filename=file.filename)
        if not result.success:
            raise HTTPException(400, result.message)
        return {"success": True, "message": result.message, "document": result.document.__dict__ if result.document else None}
    finally:
        tmp.unlink(missing_ok=True)

# SPA fallback: browser routes such as /chat and /history are handled client-side.
@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/") or path.startswith("assets/"):
        raise HTTPException(404)
    return FileResponse(FRONTEND / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
