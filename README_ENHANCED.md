# Code Bloom — Enhanced HTML/FastAPI Edition

This edition keeps the existing `src/` Corrective RAG modules and existing `app.py` unchanged. The enhanced UI is served by `enhanced_app.py`.

## Run

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe enhanced_app.py
```

Open `http://127.0.0.1:8000`.

## Features

- HTML/CSS/JavaScript SPA; no Streamlit runtime.
- Browser back/forward navigation.
- Tamil / English / Tanglish response selector.
- Voice response mode using browser speech synthesis.
- Voice input using Chrome/Edge SpeechRecognition.
- Tamil on-screen keyboard.
- Persistent conversation storage in `data/code_bloom_chat.db`.
- Reopen conversations and preserve contextual follow-ups.
- Clean source cards; placeholder/unknown citations are filtered out.
- Existing `src/` RAG pipeline is imported, not rewritten.
- Existing `.env` / Groq key setup remains supported by `src/config.py`.

## Groq key

Keep the key in the project-root `.env`:

```env
GROQ_API_KEY=gsk_...
```

Do not put the key in frontend JavaScript.
