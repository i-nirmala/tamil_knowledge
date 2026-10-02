"""
Code Bloom — Shared Utilities
------------------------------------------------
Small, dependency-light helper functions used across multiple modules.
Keeping them here avoids duplicated code.
"""

import hashlib
import re
import uuid
from datetime import datetime
from typing import Optional


def new_id(prefix: str = "") -> str:
    """Generate a short unique identifier."""
    raw = uuid.uuid4().hex[:12]
    return f"{prefix}{raw}" if prefix else raw


def file_hash(file_bytes: bytes) -> str:
    """Stable hash for a file's bytes — used to detect duplicate uploads."""
    return hashlib.sha256(file_bytes).hexdigest()[:16]


def clean_text(text: str) -> str:
    """
    Clean extracted PDF text:
    - collapse repeated whitespace
    - remove control characters
    - keep Tamil, English and common punctuation intact
    """
    if not text:
        return ""
    # Remove non-printable / control characters (keep newlines as spaces)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text)
    # Collapse multiple spaces/tabs
    text = re.sub(r"[ \t]+", " ", text)
    # Collapse 3+ newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip stray hyphenation artifacts from PDF line-wrapping (word-\nword)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)
    return text.strip()


def truncate(text: str, max_chars: int = 220) -> str:
    """Shorten text for display, preserving whole words where possible."""
    if not text or len(text) <= max_chars:
        return text
    snippet = text[:max_chars].rsplit(" ", 1)[0]
    return snippet.strip() + "…"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def contains_tamil(text: str) -> bool:
    """True if the text contains at least one Tamil Unicode character."""
    return bool(re.search(r"[\u0B80-\u0BFF]", text or ""))


def format_score(score: Optional[float]) -> str:
    """Format a similarity score as a percentage-like relevance string."""
    if score is None:
        return "—"
    return f"{max(0.0, min(1.0, score)) * 100:.1f}%"
