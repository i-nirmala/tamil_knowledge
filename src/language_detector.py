"""
Code Bloom — Language Detector
------------------------------------------------
Detects the language style of a user query:

    Tamil    -> written in Tamil Unicode script
    English  -> plain English
    Tanglish -> Tamil spoken/written using Roman letters (romanized Tamil)
    Mixed    -> a combination of Tamil script and English/Tanglish in the
                same query

This module never fails hard — if `langdetect` misbehaves on a short
string it falls back to heuristic rules so the app never crashes.
"""

import re
from dataclasses import dataclass

try:
    from langdetect import detect, DetectorFactory, LangDetectException

    DetectorFactory.seed = 0
    _LANGDETECT_AVAILABLE = True
except Exception:  # pragma: no cover - defensive import
    _LANGDETECT_AVAILABLE = False

TAMIL_RANGE = re.compile(r"[\u0B80-\u0BFF]")

# Common Tanglish (romanized Tamil) tokens/particles. These are strong
# signals that the Latin-script text is Tamil written in English letters
# rather than genuine English.
TANGLISH_MARKERS = {
    "pathi", "sollirukku", "sollu", "enna", "eppadi", "epdi", "irukku",
    "irukka", "vendum", "venum", "illa", "illai", "nala", "nalla",
    "seri", "sari", "romba", "konjam", "kudukka", "kudu", "mudiyuma",
    "mudiyum", "solunga", "solla", "oru", "ippo", "appo", "adhu", "athu",
    "idhu", "ithu", "naan", "nan", "neenga", "ninga", "avanga", "avaru",
    "vaanga", "poga", "pannunga", "panna", "theriyuma",
    "theriyum", "arthama", "artham", "sonna", "solra", "la",
}

# Note: proper nouns like "thirukkural" / "kural" are intentionally NOT
# treated as Tanglish markers — they appear in genuine English queries
# too (see src/query_engine.py KNOWN_ENTITIES for entity detection).


@dataclass
class LanguageResult:
    language: str          # "Tamil" | "English" | "Tanglish" | "Mixed"
    tamil_ratio: float      # fraction of Tamil-script characters
    has_tanglish_markers: bool
    confidence: str         # "high" | "medium" | "low"


def _tamil_char_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    tamil_letters = [c for c in letters if TAMIL_RANGE.match(c)]
    return len(tamil_letters) / len(letters)


def _has_tanglish_markers(text: str) -> bool:
    tokens = re.findall(r"[a-zA-Z]+", text.lower())
    return any(tok in TANGLISH_MARKERS for tok in tokens)


def detect_language(text: str) -> LanguageResult:
    """
    Classify a query as Tamil / English / Tanglish / Mixed.

    Logic:
      1. Compute the ratio of Tamil-script letters to all letters.
      2. Look for romanized-Tamil marker words in the Latin-script part.
      3. Combine both signals into a final label.
    """
    text = (text or "").strip()
    if not text:
        return LanguageResult("English", 0.0, False, "low")

    tamil_ratio = _tamil_char_ratio(text)
    has_markers = _has_tanglish_markers(text)
    has_latin = bool(re.search(r"[a-zA-Z]", text))

    # Pure / near-pure Tamil script
    if tamil_ratio >= 0.85:
        return LanguageResult("Tamil", tamil_ratio, has_markers, "high")

    # Tamil script mixed with meaningful Latin content
    if tamil_ratio > 0.15 and has_latin:
        return LanguageResult("Mixed", tamil_ratio, has_markers, "high")

    # No/near-no Tamil script, but Latin text reads like romanized Tamil
    if tamil_ratio <= 0.15 and has_markers:
        return LanguageResult("Tanglish", tamil_ratio, True, "medium")

    # Fall back to langdetect for genuinely ambiguous short strings
    if _LANGDETECT_AVAILABLE and len(text) >= 4:
        try:
            code = detect(text)
            if code == "ta":
                return LanguageResult("Tamil", tamil_ratio, has_markers, "medium")
        except LangDetectException:
            pass

    return LanguageResult("English", tamil_ratio, has_markers, "high")
