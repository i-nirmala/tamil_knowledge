# 🌸 Code Bloom

**Universal Knowledge Assistant & AI-Powered Knowledge Discovery**

> An AI that discovers, verifies and cites Tamil & multilingual knowledge — not just chats.

Code Bloom doesn't just answer questions. It **discovers** the relevant knowledge,
**verifies** the evidence, and **shows you where the answer came from** — down to the page.

---

## The Problem

Tamil and other multilingual knowledge is locked inside books, PDFs, institutional
databases and digital archives. Three things make it hard to actually *use*:

1. **Language barriers.** Real users don't type clean queries. They write in Tamil script,
   in English, in Tanglish (romanized Tamil), or in a mix of all three in one sentence.
   Most retrieval systems handle exactly one of those.
2. **Discovery, not just search.** Knowing which *source* holds the answer is itself the
   hard part. A generic keyword search over one folder isn't knowledge discovery.
3. **Trust.** General-purpose chatbots produce fluent answers with invented sources,
   invented page numbers and invented quotations. For students, researchers and cultural
   institutions, an unsourced answer is worthless — or worse, misleading.

## The Solution

Code Bloom is a **Tamil-first multilingual knowledge discovery platform**. Every query
runs through a real, inspectable pipeline: it is understood, routed to a knowledge source,
retrieved semantically, reranked, **verified for evidence sufficiency**, and only then
answered — with page-level citations and a full trace of how the answer was reached.

If the evidence isn't strong enough, Code Bloom **declines to answer** instead of guessing.

---

## Key Features

Every feature listed here is actually implemented in this repository.

| # | Feature | What it does |
|---|---|---|
| 1 | **Tamil-first multilingual understanding** | Detects and handles Tamil, English, Tanglish and mixed Tamil+English queries |
| 2 | **Query Intelligence layer** | Extracts language, normalized query, intent, topic, entity, evidence requirement and follow-up status |
| 3 | **AI Knowledge Routing Engine** | Decides *which* knowledge source should answer, via a modular source-adapter architecture |
| 4 | **Semantic retrieval** | Multilingual embeddings + FAISS vector search, configurable top-K |
| 5 | **Hybrid retrieval** | Blends BM25 keyword scoring into semantic search, degrading gracefully if unavailable |
| 6 | **Dedicated reranking stage** | A separate module (not mixed into retrieval) with morphology-aware lexical boosting for Tamil |
| 7 | **Two-stage evidence verification** | A score/metadata check, plus an optional LLM pass that asks whether the evidence *actually answers* the question |
| 8 | **Insufficient-evidence handling** | An explicit "I couldn't verify this" path — no hallucinated fallback |
| 9 | **Source-grounded answers** | Strict RAG prompt; the model only sees retrieved evidence with real metadata |
| 10 | **Page-level citations** | Book, author, chapter, page and relevance score for every passage used |
| 11 | **Evidence highlighting** | The exact passages behind the answer, shown in expandable cards |
| 12 | **🔎 Knowledge Trace** | Eleven pipeline stages with real runtime values — the headline differentiator |
| 13 | **Conversational memory** | Bounded context so follow-ups like *"அதில் ஆசிரியரின் பங்கு என்ன?"* resolve correctly |
| 14 | **Research Mode** | Detailed summaries, key findings, multiple passages and source comparison |
| 15 | **Source comparison** | Built only from retrieved evidence; says so honestly when comparison isn't possible |
| 16 | **Knowledge Base dashboard** | Documents, pages, chunks and indexed vectors, plus per-document detail |
| 17 | **Document upload** | In-app PDF upload with step-by-step processing feedback, plus a CLI script |
| 18 | **Sample knowledge base** | Ships ready to demo — no hunting for PDFs before the first query |

### An honest note on accuracy

Code Bloom performs **evidence-grounded generation with insufficient-evidence handling.**

It does **not** claim to be "100% hallucination-free." It claims something more defensible:
every answer is tied to retrieved passages you can inspect yourself, and the system refuses
to answer when the evidence is weak.

---

## Architecture

```
                              USER QUERY
                                  │
                    ┌─────────────▼─────────────┐
                    │    QUERY UNDERSTANDING    │
                    │  ┌─────────────────────┐  │
                    │  │ Language Detection  │  │  Tamil / English /
                    │  │ (Tamil/Eng/Tanglish)│  │  Tanglish / Mixed
                    │  ├─────────────────────┤  │
                    │  │ Normalization +     │  │  Tanglish → Tamil
                    │  │ Transliteration     │  │  transliteration
                    │  ├─────────────────────┤  │
                    │  │ Intent + Entity     │  │  Knowledge Discovery,
                    │  │ + Follow-up detect  │  │  Thirukkural, Education
                    │  └─────────────────────┘  │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ AI KNOWLEDGE ROUTING      │
                    │ ENGINE                    │
                    └─────────────┬─────────────┘
                                  │
          ┌───────────┬───────────┼───────────┬───────────┐
          │           │           │           │           │
    ┌─────▼────┐ ┌───▼────┐ ┌────▼───┐ ┌────▼─────┐ ┌───▼──────┐
    │  Tamil   │ │  PDFs  │ │  Web   │ │ Database │ │ Archives │
    │  Books   │ │        │ │        │ │          │ │          │
    │ ✅ live  │ │ ✅ live│ │ ⚠ future│ │ ⚠ future │ │ ⚠ future │
    └─────┬────┘ └───┬────┘ └────────┘ └──────────┘ └──────────┘
          └──────────┘
                    │  SOURCE DISCOVERY
                    │
          ┌─────────▼──────────┐
          │ SEMANTIC RETRIEVAL │   query embedding → FAISS top-K
          │   + BM25 hybrid    │   (+ keyword blend)
          └─────────┬──────────┘
                    │  Top 10 candidates
          ┌─────────▼──────────┐
          │     RERANKING      │   semantic score × lexical boost
          │  (separate module) │   (Tamil morphology aware)
          └─────────┬──────────┘
                    │  Top 5 evidence candidates
          ┌─────────▼──────────────────────┐
          │    EVIDENCE VERIFICATION       │
          │  Stage 1: score + metadata     │
          │  Stage 2: LLM answerability    │
          └───────┬────────────────┬───────┘
                  │                │
         SUFFICIENT                INSUFFICIENT
                  │                │
        ┌─────────▼──────┐  ┌──────▼──────────────────┐
        │  Groq LLM      │  │ ⚠ Insufficient Evidence │
        │  strict RAG    │  │ "I couldn't verify this │
        │  prompt        │  │  from available sources"│
        └─────────┬──────┘  │  (no hallucination)     │
                  │         └─────────────────────────┘
        ┌─────────▼──────────┐
        │  GROUNDED ANSWER   │
        ├────────────────────┤
        │ CITATIONS + SOURCE │   Book · Author · Chapter · Page
        │ + PAGE             │
        ├────────────────────┤
        │ 🔎 KNOWLEDGE TRACE │   11 stages, real runtime values
        ├────────────────────┤
        │ CONVERSATIONAL     │   bounded memory → follow-ups
        │ FOLLOW-UP          │
        └────────────────────┘
```

### Project structure

```
Code_Bloom/
├── app.py                      # Entry point — thin; wires config, state, navigation
├── requirements.txt
├── README.md
├── .env.example
├── .gitignore
│
├── data/
│   ├── books/                  # Your uploaded PDFs land here
│   ├── sample/                 # Bundled public-domain demo content + generated PDF
│   ├── processed/              # Knowledge-base registry (JSON)
│   └── indexes/                # FAISS index + chunk metadata
│
├── src/
│   ├── config.py               # Single source of truth for all configuration
│   ├── utils.py                # Shared helpers (cleaning, hashing, formatting)
│   ├── language_detector.py    # Tamil / English / Tanglish / Mixed detection
│   ├── transliteration.py      # Tanglish → Tamil script normalization
│   ├── pdf_processor.py        # PyMuPDF page-by-page extraction + validation
│   ├── chunker.py              # Page-preserving chunking with full metadata
│   ├── embeddings.py           # Cached multilingual sentence embeddings
│   ├── vector_store.py         # FAISS index + metadata persistence
│   ├── knowledge_base.py       # Ingestion pipeline, registry, stats, bootstrap
│   ├── router.py               # AI Knowledge Routing Engine
│   ├── query_engine.py         # Query Intelligence layer
│   ├── retriever.py            # Semantic + BM25 hybrid retrieval
│   ├── reranker.py             # Dedicated reranking (separate from retrieval)
│   ├── evidence_verifier.py    # Two-stage evidence verification
│   ├── llm.py                  # Groq client, strict RAG prompt, LLM verifier
│   ├── citation.py             # Citation construction from real metadata only
│   ├── memory.py               # Bounded conversational memory
│   ├── research_mode.py        # Research mode + evidence-only source comparison
│   └── pipeline.py             # Orchestrates every stage; builds the Knowledge Trace
│
├── sources/                    # Modular source-adapter architecture
│   ├── base_source.py          # Abstract interface every adapter implements
│   ├── book_source.py          # ✅ Tamil Books (working)
│   ├── pdf_source.py           # ✅ PDFs (working)
│   ├── web_source.py           # ⚠ Future scope — reports unavailable, never fakes
│   ├── database_source.py      # ⚠ Future scope
│   └── archive_source.py       # ⚠ Future scope
│
├── ui/
│   ├── styles.py               # All custom CSS in one place
│   ├── components.py           # Reusable renderers (trace, evidence, citations…)
│   └── pages.py                # One function per page
│
└── scripts/
    ├── generate_sample_pdfs.py # Builds the demo PDF from public-domain content
    ├── ingest_documents.py     # CLI ingestion (single file or whole folder)
    └── build_index.py          # Rebuild the FAISS index from scratch
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **UI** | Streamlit | Fast to build, pure Python, no separate frontend build step |
| **Language** | Python 3.10–3.13 | Broad compatibility; no downgrade required |
| **LLM** | **Groq API** (`openai/gpt-oss-120b`) | Very fast inference; model is configurable via `.env` |
| **Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` | 50+ languages incl. Tamil, ~470 MB, **CPU-only**, no GPU needed |
| **Vector search** | FAISS (`faiss-cpu`) | Fast exact inner-product search; normalized vectors ⇒ cosine similarity |
| **Keyword search** | `rank-bm25` | Hybrid retrieval; optional and degrades gracefully |
| **PDF processing** | **PyMuPDF (fitz)** | Reliable page-by-page text extraction with page numbers preserved |
| **Language detection** | `langdetect` + custom heuristics | Handles Tanglish, which off-the-shelf detectors cannot |
| **Transliteration** | `indic-transliteration` | Best-effort Tanglish → Tamil script for better recall |
| **RAG** | Custom pipeline | Routing → retrieval → reranking → verification → grounded generation |

### Why this embedding model

`paraphrase-multilingual-MiniLM-L12-v2` was chosen over larger alternatives because it:

- covers **50+ languages including Tamil** in a shared vector space, so a Tamil query can
  retrieve English text and vice versa;
- is small (**~470 MB**, 384 dimensions) and runs comfortably on **CPU** — a normal
  Windows laptop with 16 GB RAM, no CUDA, no GPU;
- loads in seconds and is cached for the whole session.

### Why not a cross-encoder reranker?

The obvious reranking upgrade would be a cross-encoder like `ms-marco-MiniLM`. We
deliberately didn't use one: those models are **English-only**, and would silently
*degrade* quality on Tamil and Tanglish queries — the exact opposite of this project's
purpose. Instead the reranker uses a transparent, multilingual-safe combination of
semantic similarity and **morphology-aware lexical overlap** (Tamil is agglutinative, so
`கல்வியின்` is matched to `கல்வி` via stem-prefix matching).

---

## Installation

> **Requirements:** Python 3.10 or newer (3.13 supported), ~2 GB free disk for the
> embedding model, and an internet connection on first run.

```powershell
cd Code_Bloom

# (Recommended) create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

> If PowerShell blocks the activation script, run:
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

## Environment Setup

1. Get a **free** Groq API key at <https://console.groq.com/keys>
2. Copy the example file and edit it:

```powershell
Copy-Item .env.example .env
notepad .env
```

3. Put your key in `.env` (this file is git-ignored and must never be committed):

```env
GROQ_API_KEY=gsk_your_actual_key_here
GROQ_MODEL=openai/gpt-oss-120b
```

> **Note on models:** `llama-3.3-70b-versatile` has been deprecated and decommissioned by
> Groq. This project defaults to `openai/gpt-oss-120b`. Any currently supported Groq model
> can be used — just change `GROQ_MODEL`.

Without a key the app still runs: language detection, routing, retrieval, reranking,
evidence verification and the Knowledge Trace all work. Only answer *generation* is
disabled, and the UI says so clearly rather than crashing.

## Run

```powershell
streamlit run app.py
```

The app opens at <http://localhost:8501>.

On first launch it downloads the embedding model (~470 MB, once), then automatically
builds and indexes the sample knowledge base. **No manual setup step is required.**

---

## Adding Documents

### Option A — In the app (recommended)

Go to **📤 Upload Documents**, choose a PDF, fill in the title and author (these are used
in citations), and click **Process & Index**. You'll see each stage complete:

```
✓ File uploaded      ✓ Chunks created
✓ Text extracted     ✓ Embeddings generated
✓ Pages processed    ✓ FAISS index updated
                     ✓ Document added to Knowledge Base
```

### Option B — Command line

```powershell
# One file
python scripts/ingest_documents.py --file "data/books/my_book.pdf" --title "My Book" --author "Author Name"

# A whole folder
python scripts/ingest_documents.py --folder "data/books"

# Rebuild the index from scratch
python scripts/build_index.py
```

---

## Demo Queries

All six are available as one-click buttons in the app under **Try a demo query**.

| Type | Query |
|---|---|
| **Tamil** | `திருக்குறளில் கல்வியின் முக்கியத்துவம் என்ன?` |
| **English** | `What does Thirukkural say about education?` |
| **Tanglish** | `Thirukkural la education pathi enna sollirukku?` |
| **Mixed** | `Thirukkural la கல்வி பற்றி என்ன சொல்லிருக்கு?` |
| **Follow-up** | `அதில் ஆசிரியரின் பங்கு என்ன?` |
| **Insufficient evidence** | `Thirukkural la 2050-la enna nadakkum?` |

The follow-up query only makes sense after one of the education queries — that's the point.
`அதில்` ("in that") is resolved from conversational memory.

---

## Sample Knowledge Base

The bundled demo content is **legally safe**:

- **Thirukkural** by Thiruvalluvar — roughly 2,000 years old, firmly public domain
- **G.U. Pope's 1886 English translation** — also public domain
- **Original explanatory notes** written specifically for this project

A small curated selection covering education, virtue, friendship and governance is
rendered into a real PDF and ingested through the exact same pipeline your own uploads
use — no shortcuts, no pre-baked index. **No copyrighted books are bundled.**

---

## Limitations

These are genuine, and worth stating plainly to judges:

1. **Only PDF/book sources are live.** Web, database and digital-archive adapters exist as
   architecture and correctly report themselves unavailable. They return no results — the
   app never fabricates live source data.
2. **No OCR.** Scanned, image-only PDFs are detected and reported clearly, but cannot be
   indexed. Adding Tesseract is straightforward future work.
3. **Tanglish transliteration is heuristic.** `indic-transliteration` maps romanized Tamil
   to Tamil script on a best-effort basis; it is not a trained transliteration model, so
   unusual spellings may transliterate imperfectly.
4. **Entity recognition is rule-based.** `KNOWN_ENTITIES` is a curated list, not a trained
   NER model. This keeps the demo fast and deterministic, but won't recognize arbitrary
   named entities.
5. **Reranking is not a cross-encoder.** A deliberate trade-off (see above) — quality is
   good and multilingual-safe, but a proper *multilingual* cross-encoder would likely beat it.
6. **Stage-2 LLM verification costs an extra API call** per query and is skipped if no
   API key is present, falling back to score-based verification alone.
7. **Small sample knowledge base.** Six pages of curated content is enough to demonstrate
   every pipeline stage, but it is a demo corpus, not a library.
8. **Answer quality depends on the Groq model** configured in `.env`.

## Future Scope

- **Web sources** — plug a search API into `WebAdapter` (the interface already exists)
- **Databases** — connect library catalogs and institutional repositories via `DatabaseAdapter`
- **Digital archives** — integrate Tamil Virtual Academy and similar collections
- **OCR** — Tesseract with Tamil language data, to unlock scanned manuscripts
- **Voice interaction** — Tamil/English speech-to-text input and browser spoken answers (implemented in the UI)
- **Multimodal knowledge** — images, tables, inscriptions and manuscript scans
- **Larger multilingual knowledge bases** — scale FAISS to an IVF/HNSW index
- **Trained Tanglish transliteration** — replace the heuristic with a learned model
- **User accounts and saved research** — persistent collections and citation export

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `⚠ Groq API Key Missing` | Add `GROQ_API_KEY` to `.env`, then restart the app |
| Model download fails on first run | Check your internet connection — it's a one-time ~470 MB download |
| Tamil text shows as boxes | Install a Tamil font (e.g. Noto Sans Tamil); this affects display only, not retrieval |
| Index seems stale or corrupted | `python scripts/build_index.py` |
| "This file is not a valid PDF" | The upload isn't a real PDF — check the file |
| "No extractable text was found" | The PDF is scanned/image-only; OCR is not supported |
| Changed the embedding model | Rebuild: `python scripts/build_index.py` (vectors from different models aren't comparable) |

---

## License & Attribution

Project code: created for the **Aurex'26** hackathon.

Sample content: Thirukkural by Thiruvalluvar (public domain); English translation by
G.U. Pope, 1886 (public domain); explanatory notes original to this project.

---

<div align="center">

**🌸 Code Bloom** — *discovers the knowledge, verifies the evidence, shows you the source.*

</div>


## UI Upgrade — Code Bloom 2.0

This version keeps the existing `src/` RAG, retrieval, reranking, evidence verification,
LLM and knowledge-base backend unchanged. The presentation layer has been upgraded with:

- Interactive HTML/CSS visual cards with lavender + warm-brown glass styling.
- Hover lift, shimmer, sparkle, pulse and button-ripple animations.
- Reliable in-session page history and a working `←` back button on application pages.
- Browser-native voice question input using the Web Speech API (Chrome/Edge recommended).
- Voice transcripts are inserted into the existing query box, so the same backend pipeline is used.
- Responsive layout improvements for smaller screens.
- No additional Python package is required for voice input.

### Voice input

Open **Ask** or **Research**, click **🎙 Voice question**, allow microphone access, and speak.
The transcript appears in the normal question field. Tamil uses `ta-IN`; English/Tanglish can
use `en-IN` depending on the selected answer language. If browser speech recognition is not
available, typed input continues to work normally.

### Navigation

The application now stores a small page stack in Streamlit session state. Sidebar/card
navigation pushes the current page, and the page header `←` pops the previous page without
using browser URLs or full-page navigation.
