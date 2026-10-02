# Code Bloom — Dynamic Tamil Knowledge Navigator

## What changed
- No longer restricted to the bundled PDF.
- Every question is answered through Groq; local documents and live web results are evidence when relevant.
- Tamil/Tanglish/mixed-language retrieval is supported by multilingual embeddings.
- Live web source: Tavily if `TAVILY_API_KEY` is configured; otherwise Wikipedia + DuckDuckGo HTML fallback.
- Local PDF/book upload remains searchable and can ground answers.
- A Tamil corpus manifest and `scripts/build_tamil_corpus.py` are included for building an expandable retrieval corpus from public/official sources.

## Important
This project does not fine-tune/train the Groq model locally. It uses retrieval-augmented generation (RAG) plus live search. A genuinely trained Tamil model would require a large licensed dataset and a separate training/fine-tuning pipeline.

## Run
1. Put `GROQ_API_KEY=...` in `.env` (recommended) or `.env.example` for local-only testing.
2. `python -m venv venv`
3. `venv\\Scripts\\python.exe -m pip install -r requirements.txt`
4. `venv\\Scripts\\python.exe -m streamlit run app.py`

## Optional web quality
Add `TAVILY_API_KEY` to `.env` for stronger search/retrieval. No API key is required for the fallback sources, subject to their availability and terms.
