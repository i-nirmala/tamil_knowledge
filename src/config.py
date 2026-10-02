import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Prefer a real .env; fall back to .env.example for easy local demos.
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.example")

DATA_DIR = BASE_DIR / "data"
BOOKS_DIR = DATA_DIR / "books"
SAMPLE_DIR = DATA_DIR / "sample"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "indexes"
for _dir in (DATA_DIR, BOOKS_DIR, SAMPLE_DIR, PROCESSED_DIR, INDEX_DIR):
    _dir.mkdir(parents=True, exist_ok=True)

FAISS_INDEX_PATH = INDEX_DIR / "code_bloom.faiss"
METADATA_PATH = INDEX_DIR / "code_bloom_metadata.json"
KB_REGISTRY_PATH = PROCESSED_DIR / "knowledge_base_registry.json"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_TEMPERATURE = float(os.getenv("GROQ_TEMPERATURE", "0.2"))
GROQ_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "1800"))

# Optional web-search provider. The app also has a no-key Wikipedia/HTML fallback.
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "").strip()
WEB_MAX_RESULTS = int(os.getenv("WEB_MAX_RESULTS", "6"))
WEB_TIMEOUT = int(os.getenv("WEB_TIMEOUT", "10"))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2").strip()
EMBEDDING_DIM = 384
TOP_K_RETRIEVE = int(os.getenv("TOP_K_RETRIEVE", "10"))
TOP_K_RERANK = int(os.getenv("TOP_K_RERANK", "6"))
EVIDENCE_SCORE_THRESHOLD = float(os.getenv("EVIDENCE_SCORE_THRESHOLD", "0.25"))
MIN_EVIDENCE_CHUNKS = int(os.getenv("MIN_EVIDENCE_CHUNKS", "1"))
CHUNK_SIZE_CHARS = int(os.getenv("CHUNK_SIZE_CHARS", "800"))
CHUNK_OVERLAP_CHARS = int(os.getenv("CHUNK_OVERLAP_CHARS", "150"))
MEMORY_TURNS = int(os.getenv("MEMORY_TURNS", "5"))
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))

APP_NAME = "Code Bloom"
APP_TAGLINE = "Tamil-first Universal Knowledge Discovery"
APP_ICON = "🌸"

def groq_configured() -> bool:
    return bool(GROQ_API_KEY)

def web_configured() -> bool:
    return True
