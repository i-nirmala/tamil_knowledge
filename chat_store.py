from __future__ import annotations
import json, os, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import requests

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / 'data' / 'code_bloom_chat.db'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SUPABASE_URL = os.getenv('SUPABASE_URL','').rstrip('/')
SUPABASE_SECRET_KEY = os.getenv('SUPABASE_SECRET_KEY','') or os.getenv('SUPABASE_SERVICE_ROLE_KEY','')
CLOUD_ENABLED = bool(SUPABASE_URL and SUPABASE_SECRET_KEY)


def now(): return datetime.now(timezone.utc).isoformat()

def _conn():
    c=sqlite3.connect(DB_PATH); c.row_factory=sqlite3.Row; c.execute('PRAGMA journal_mode=WAL'); return c

def init_db():
    with _conn() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS conversations (id TEXT PRIMARY KEY,user_email TEXT NOT NULL,title TEXT NOT NULL,created_at TEXT NOT NULL,updated_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT,conversation_id TEXT NOT NULL,role TEXT NOT NULL,content TEXT NOT NULL,output_mode TEXT DEFAULT 'Tamil',citations_json TEXT DEFAULT '[]',created_at TEXT NOT NULL,FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE); CREATE INDEX IF NOT EXISTS idx_conv_user_updated ON conversations(user_email,updated_at DESC); CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id,id);''')

def _headers():
    return {'apikey':SUPABASE_SECRET_KEY,'Authorization':f'Bearer {SUPABASE_SECRET_KEY}','Content-Type':'application/json','Prefer':'return=representation'}

def _rest(table, method='GET', params=None, body=None):
    r=requests.request(method, f'{SUPABASE_URL}/rest/v1/{table}', headers=_headers(), params=params, json=body, timeout=20)
    if not r.ok: raise RuntimeError(f'Supabase {method} {table}: {r.status_code} {r.text[:500]}')
    return r.json() if r.text else []

def _cloud_conversation(cid,email):
    rows=_rest('conversations',params={'id':f'eq.{cid}','user_email':f'eq.{email}','select':'*','limit':'1'})
    return rows[0] if rows else None

def ensure_conversation(conversation_id,user_email,title='New conversation',user_id=None):
    if CLOUD_ENABLED and user_id:
        existing=_rest('conversations',params={'id':f'eq.{conversation_id}','user_id':f'eq.{user_id}','select':'id','limit':'1'})
        if not existing:
            _rest('conversations','POST',body={'id':conversation_id,'user_id':user_id,'user_email':user_email,'title':title[:120] or 'New conversation'})
        return
    init_db();
    with _conn() as c:
        row=c.execute('SELECT id FROM conversations WHERE id=? AND user_email=?',(conversation_id,user_email)).fetchone()
        if not row: c.execute('INSERT INTO conversations VALUES(?,?,?,?,?)',(conversation_id,user_email,title[:120] or 'New conversation',now(),now()))

def save_message(conversation_id,user_email,role,content,output_mode='Tamil',citations=None,user_id=None):
    if CLOUD_ENABLED and user_id:
        ensure_conversation(conversation_id,user_email,user_id=user_id)
        _rest('messages','POST',body={'conversation_id':conversation_id,'user_id':user_id,'user_email':user_email,'role':role,'content':content,'output_mode':output_mode,'citations':citations or []})
        _rest('conversations','PATCH',params={'id':f'eq.{conversation_id}','user_id':f'eq.{user_id}'},body={'updated_at':now()})
        return
    ensure_conversation(conversation_id,user_email)
    with _conn() as c:
        c.execute('INSERT INTO messages(conversation_id,role,content,output_mode,citations_json,created_at) VALUES(?,?,?,?,?,?)',(conversation_id,role,content,output_mode,json.dumps(citations or [],ensure_ascii=False),now()))
        c.execute('UPDATE conversations SET updated_at=? WHERE id=? AND user_email=?',(now(),conversation_id,user_email))

def set_title_if_new(conversation_id,user_email,title,user_id=None):
    if CLOUD_ENABLED and user_id:
        _rest('conversations','PATCH',params={'id':f'eq.{conversation_id}','user_id':f'eq.{user_id}','title':'eq.New conversation'},body={'title':title[:120]})
        return
    with _conn() as c: c.execute("UPDATE conversations SET title=? WHERE id=? AND user_email=? AND title='New conversation'",(title[:120],conversation_id,user_email))

def list_conversations(user_email,user_id=None):
    if CLOUD_ENABLED and user_id:
        rows=_rest('conversations',params={'user_id':f'eq.{user_id}','select':'id,title,created_at,updated_at','order':'updated_at.desc'})
        return rows
    init_db();
    with _conn() as c: return [dict(r) for r in c.execute('SELECT id,title,created_at,updated_at FROM conversations WHERE user_email=? ORDER BY updated_at DESC',(user_email,)).fetchall()]

def get_messages(conversation_id,user_email,user_id=None):
    if CLOUD_ENABLED and user_id:
        ok=_rest('conversations',params={'id':f'eq.{conversation_id}','user_id':f'eq.{user_id}','select':'id','limit':'1'})
        if not ok:return []
        return _rest('messages',params={'conversation_id':f'eq.{conversation_id}','user_id':f'eq.{user_id}','select':'role,content,output_mode,citations,created_at','order':'id.asc'})
    init_db();
    with _conn() as c:
        ok=c.execute('SELECT id FROM conversations WHERE id=? AND user_email=?',(conversation_id,user_email)).fetchone()
        if not ok:return []
        rows=c.execute('SELECT role,content,output_mode,citations_json,created_at FROM messages WHERE conversation_id=? ORDER BY id',(conversation_id,)).fetchall(); out=[]
        for r in rows:
            x=dict(r)
            try:x['citations']=json.loads(x.pop('citations_json') or '[]')
            except Exception:x['citations']=[]
            out.append(x)
        return out

def delete_conversation(conversation_id,user_email,user_id=None):
    if CLOUD_ENABLED and user_id:
        _rest('conversations','DELETE',params={'id':f'eq.{conversation_id}','user_id':f'eq.{user_id}'})
        return
    with _conn() as c:
        c.execute('DELETE FROM messages WHERE conversation_id=?',(conversation_id,)); c.execute('DELETE FROM conversations WHERE id=? AND user_email=?',(conversation_id,user_email))

def load_memory_rows(conversation_id,user_email,limit=5,user_id=None):
    rows=get_messages(conversation_id,user_email,user_id); turns=[]
    for i in range(len(rows)-1):
        if rows[i]['role']=='user' and rows[i+1]['role']=='assistant': turns.append((rows[i]['content'],rows[i+1]['content']))
    return turns[-limit:]
