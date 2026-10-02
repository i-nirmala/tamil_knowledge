"""
Code Bloom — Query Intelligence Layer
------------------------------------------------
For every user query this module determines:
  - language (Tamil / English / Tanglish / Mixed)
  - a normalized query suitable for embedding
  - intent (Knowledge Discovery / Definition / Comparison / Follow-up / ...)
  - topic (rough subject keyword)
  - entity (book/author/named concept the query is about)
  - whether evidence is required
  - whether this is a follow-up question referencing earlier conversation

This is intentionally rule-based/lightweight (no extra LLM call) so the
system stays fast, deterministic, and demonstrable without depending on
network latency for every keystroke — a deliberate reliability choice
for a hackathon demo.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional

from src.language_detector import detect_language
from src.transliteration import normalize_query

# Known entities the demo knowledge base focuses on. In a production
# system this would be built dynamically from the knowledge base's
# indexed document titles.
KNOWN_ENTITIES = [
    "thirukkural", "திருக்குறள்", "kural", "குறள்",
    "tholkappiyam", "தொல்காப்பியம்",
    "silappathikaram", "சிலப்பதிகாரம்",
]

# Follow-up reference words (pronouns / demonstratives) in Tamil,
# Tanglish and English that typically point back at prior conversation.
FOLLOWUP_MARKERS = [
    "அதில்", "அது", "இதில்", "இது", "அதன்", "இதன்",
    "adhil", "athil", "adhu", "athu", "idhil", "ithil",
    "it", "that", "this", "those", "these", "again",
    "next", "more about", "continue",
]

TOPIC_KEYWORDS = {
    "education": ["education", "கல்வி", "learning", "படிப்பு", "teacher", "ஆசிரியர்"],
    "ethics": ["ethics", "morality", "அறம்", "virtue", "நீதி"],
    "governance": ["king", "governance", "அரசு", "ஆட்சி", "ruler"],
    "friendship": ["friendship", "நட்பு", "friend", "நண்பன்"],
    "wealth": ["wealth", "பொருள்", "money", "செல்வம்"],
    "love": ["love", "காதல்", "இன்பம்"],
    "future": ["2050", "future", "எதிர்காலம்", "prediction"],
}


@dataclass
class QueryIntelligence:
    original_query: str
    language: str
    normalized_query: str
    intent: str
    topic: str
    entity: str
    evidence_required: bool
    is_followup: bool
    tamil_ratio: float = 0.0


def _detect_entity(text_lower: str) -> str:
    for ent in KNOWN_ENTITIES:
        if ent.lower() in text_lower:
            # Normalize display name
            if ent in ("thirukkural", "திருக்குறள்", "kural", "குறள்"):
                return "Thirukkural"
            if ent in ("tholkappiyam", "தொல்காப்பியம்"):
                return "Tholkappiyam"
            if ent in ("silappathikaram", "சிலப்பதிகாரம்"):
                return "Silappathikaram"
    return ""


def _detect_topic(text_lower: str) -> str:
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return topic.capitalize()
    return "General Knowledge"


def _detect_intent(text_lower: str, is_followup: bool) -> str:
    if is_followup:
        return "Follow-up Question"
    if any(w in text_lower for w in ["compare", "difference", "vs", "versus", "ஒப்பிடு"]):
        return "Comparison"
    if any(w in text_lower for w in ["what is", "define", "meaning", "என்றால் என்ன", "பொருள்"]):
        return "Definition"
    if any(w in text_lower for w in ["how", "எப்படி", "eppadi"]):
        return "Explanation"
    return "Knowledge Discovery"


def _detect_followup(text_lower: str, has_history: bool) -> bool:
    if not has_history:
        return False
    return any(marker in text_lower for marker in FOLLOWUP_MARKERS)


def analyze_query(query: str, conversation_history: Optional[List[dict]] = None) -> QueryIntelligence:
    """Run the full Query Intelligence pipeline on a raw user query."""
    conversation_history = conversation_history or []
    query = (query or "").strip()

    lang_result = detect_language(query)
    text_lower = query.lower()

    is_followup = _detect_followup(text_lower, bool(conversation_history))
    entity = _detect_entity(text_lower)
    topic = _detect_topic(text_lower)
    intent = _detect_intent(text_lower, is_followup)

    normalized = normalize_query(query, lang_result.language)

    # If this is a follow-up and no entity was found directly, inherit
    # the entity/topic from the most recent turn for better retrieval.
    if is_followup and not entity and conversation_history:
        last = conversation_history[-1]
        entity = last.get("entity", "")
        topic = last.get("topic", topic)
        normalized = f"{normalized} {entity}".strip()

    return QueryIntelligence(
        original_query=query,
        language=lang_result.language,
        normalized_query=normalized,
        intent=intent,
        topic=topic,
        entity=entity,
        evidence_required=True,
        is_followup=is_followup,
        tamil_ratio=lang_result.tamil_ratio,
    )
