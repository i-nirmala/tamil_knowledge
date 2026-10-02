"""
Code Bloom — Tamil / Tanglish Normalization
------------------------------------------------
The multilingual embedding model understands Tamil script and English
reasonably well, but romanized Tamil ("Tanglish") is not well covered
by most embedding models. To bridge this gap we attempt a best-effort
ITRANS-style transliteration of the Latin-script parts of a query into
Tamil script using `indic_transliteration`. This is a heuristic — it
will not be linguistically perfect, but it meaningfully improves
retrieval quality for common Tanglish phrasing compared to leaving the
text as raw Roman letters.

If transliteration fails or the library is unavailable, the original
text is used unchanged — the app must never crash because of this.
"""

import re

try:
    from indic_transliteration import sanscript
    from indic_transliteration.sanscript import transliterate

    _TRANSLIT_AVAILABLE = True
except Exception:  # pragma: no cover - defensive import
    _TRANSLIT_AVAILABLE = False

from src.language_detector import TAMIL_RANGE


def _romanize_normalize(token: str) -> str:
    """Light spelling normalization for common Tanglish variants
    before attempting transliteration (helps ITRANS map more cleanly)."""
    replacements = {
        "zh": "L",     # Tamil ழ sound approximation
        "ph": "f",
        "aa": "A",
        "ee": "I",
        "oo": "U",
    }
    out = token
    for src, dst in replacements.items():
        out = out.replace(src, dst)
    return out


def transliterate_tanglish_to_tamil(text: str) -> str:
    """Best-effort conversion of romanized Tamil text into Tamil script."""
    if not text:
        return text
    if not _TRANSLIT_AVAILABLE:
        return text

    words = text.split()
    converted = []
    for w in words:
        # Leave already-Tamil, numeric, or punctuation-only tokens untouched
        if TAMIL_RANGE.search(w) or not re.search(r"[a-zA-Z]", w):
            converted.append(w)
            continue
        try:
            norm = _romanize_normalize(w)
            tam = transliterate(norm, sanscript.ITRANS, sanscript.TAMIL)
            converted.append(tam)
        except Exception:
            converted.append(w)
    return " ".join(converted)


def normalize_query(text: str, language: str) -> str:
    """
    Produce a normalized version of the query suitable for embedding /
    retrieval, based on the detected language style.

    - Tamil / English: light whitespace cleanup only.
    - Tanglish / Mixed: also append a transliterated-to-Tamil variant so
      the embedding captures both the literal text and its Tamil-script
      meaning, improving recall against a Tamil-script knowledge base.
    """
    text = (text or "").strip()
    text = re.sub(r"\s+", " ", text)

    if language in ("Tanglish", "Mixed"):
        translit = transliterate_tanglish_to_tamil(text)
        if translit and translit != text:
            return f"{text} {translit}"

    return text
