# Code Bloom — HTML/CSS/JS Enhanced Version

This version removes Streamlit from the runtime UI. The existing `src/` RAG pipeline is preserved and served through FastAPI.

## Features
- HTML/CSS/JavaScript SPA dashboard
- Browser history navigation with Back/Forward support
- Local conversation history
- Backend contextual memory via session IDs
- Tamil on-screen keyboard
- Browser voice input (Chrome/Edge)
- Tamil / Tanglish / English input modes
- Knowledge-base listing and PDF ingestion
- Research mode
- Existing authentication helpers retained

## Run
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:8000

Set `GROQ_API_KEY` in `.env` before asking AI questions.
