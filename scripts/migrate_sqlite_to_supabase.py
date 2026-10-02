"""One-time migration of local chat history into Supabase.

Requires SUPABASE_URL, SUPABASE_SECRET_KEY and the target user's Supabase user id.
The script intentionally does not migrate passwords; authentication is managed by Supabase Auth.
"""
from __future__ import annotations
import os, sqlite3, sys, requests
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/'data'/'code_bloom_chat.db'
URL=os.getenv('SUPABASE_URL','').rstrip('/')
KEY=os.getenv('SUPABASE_SECRET_KEY','')
if not URL or not KEY:
    raise SystemExit('Set SUPABASE_URL and SUPABASE_SECRET_KEY first.')
if len(sys.argv)<3:
    raise SystemExit('Usage: python scripts/migrate_sqlite_to_supabase.py EMAIL SUPABASE_USER_ID')
email=sys.argv[1].strip().lower(); uid=sys.argv[2].strip()
h={'apikey':KEY,'Authorization':f'Bearer {KEY}','Content-Type':'application/json','Prefer':'return=representation'}

def post(table,payload):
    r=requests.post(f'{URL}/rest/v1/{table}',headers=h,json=payload,timeout=30)
    if not r.ok: raise SystemExit(f'{table}: {r.status_code} {r.text[:500]}')
    return r.json()

c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
convs=c.execute('select * from conversations where user_email=? order by created_at',(email,)).fetchall()
count=0
for conv in convs:
    existing=requests.get(f'{URL}/rest/v1/conversations',headers=h,params={'id':f"eq.{conv['id']}",'select':'id'},timeout=30).json()
    if not existing:
        post('conversations',{'id':conv['id'],'user_id':uid,'user_email':email,'title':conv['title'],'created_at':conv['created_at'],'updated_at':conv['updated_at']})
    msgs=c.execute('select * from messages where conversation_id=? order by id',(conv['id'],)).fetchall()
    for m in msgs:
        payload={'conversation_id':conv['id'],'user_id':uid,'user_email':email,'role':m['role'],'content':m['content'],'output_mode':m['output_mode'] or 'Tamil','citations':__import__('json').loads(m['citations_json'] or '[]'),'created_at':m['created_at']}
        post('messages',payload); count+=1
print(f'Migrated {len(convs)} conversations and {count} messages for {email}.')
