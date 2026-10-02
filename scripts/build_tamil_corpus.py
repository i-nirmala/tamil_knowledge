"""Build an expandable Tamil web corpus by downloading selected public pages and indexing them as PDFs is not required.
This creates plain-text training/retrieval material. It does NOT fine-tune the Groq model.
"""
from pathlib import Path
import json, requests
from bs4 import BeautifulSoup
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'data'/'tamil_corpus'/'seed_corpus.jsonl'
SOURCES=json.loads((BASE/'data'/'tamil_corpus'/'sources.json').read_text(encoding='utf8'))
with OUT.open('w',encoding='utf8') as f:
    for src in SOURCES:
        try:
            r=requests.get(src['url'],headers={'User-Agent':'CodeBloom/1.0'},timeout=15)
            soup=BeautifulSoup(r.text,'html.parser')
            for tag in soup(['script','style','nav','footer']): tag.decompose()
            text=' '.join(soup.stripped_strings)
            f.write(json.dumps({'title':src['name'],'url':src['url'],'text':text[:20000]},ensure_ascii=False)+'\n')
            print('OK',src['name'])
        except Exception as e: print('SKIP',src['name'],e)
print('Wrote',OUT)
