from __future__ import annotations
import os, requests

SUPABASE_URL=os.getenv('SUPABASE_URL','').rstrip('/')
SUPABASE_PUBLISHABLE_KEY=os.getenv('SUPABASE_PUBLISHABLE_KEY','') or os.getenv('SUPABASE_ANON_KEY','')
ENABLED=bool(SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY)

def _headers(token=None):
    h={'apikey':SUPABASE_PUBLISHABLE_KEY,'Content-Type':'application/json'}
    if token: h['Authorization']=f'Bearer {token}'
    return h

def signup(name,email,password):
    r=requests.post(f'{SUPABASE_URL}/auth/v1/signup',headers=_headers(),json={'email':email.strip().lower(),'password':password,'data':{'name':name.strip()}},timeout=20)
    d=r.json() if r.content else {}
    if not r.ok: return False,d.get('msg') or d.get('error_description') or d.get('message') or 'Signup failed.',None,None
    session=d.get('session'); user=d.get('user')
    if not session: return True,'Account created. Please verify your email before signing in.',user,None
    return True,'Account created successfully.',user,session.get('access_token')

def login(email,password):
    r=requests.post(f'{SUPABASE_URL}/auth/v1/token?grant_type=password',headers=_headers(),json={'email':email.strip().lower(),'password':password},timeout=20)
    d=r.json() if r.content else {}
    if not r.ok: return False,d.get('error_description') or d.get('msg') or d.get('message') or 'Invalid email or password.',None,None
    return True,'Login successful.',d.get('user'),d.get('access_token')

def user_from_token(token):
    if not ENABLED or not token: return None
    r=requests.get(f'{SUPABASE_URL}/auth/v1/user',headers=_headers(token),timeout=20)
    if not r.ok:return None
    return r.json()
