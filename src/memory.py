"""
Code Bloom — Conversational Memory
------------------------------------------------
Lightweight, bounded conversation memory so follow-up questions like
"அதில் ஆசிரியரின் பங்கு என்ன?" (What is the teacher's role in that?)
can be understood in context — WITHOUT sending unlimited chat history
to the LLM (which would be slow, expensive, and unnecessary).

Only the last `MEMORY_TURNS` turns are kept, and only a compact summary
(query, entity, topic, short answer) is passed to the LLM as context —
not full evidence blocks from earlier turns.
"""

from dataclasses import dataclass, field
from typing import List

from src.config import MEMORY_TURNS


@dataclass
class ConversationTurn:
    query: str
    entity: str
    topic: str
    answer_summary: str


class ConversationMemory:
    def __init__(self, max_turns: int = MEMORY_TURNS):
        self.max_turns = max_turns
        self.turns: List[ConversationTurn] = []

    def add_turn(self, query: str, entity: str, topic: str, answer_summary: str) -> None:
        self.turns.append(
            ConversationTurn(
                query=query,
                entity=entity,
                topic=topic,
                answer_summary=answer_summary[:300],
            )
        )
        self.turns = self.turns[-self.max_turns:]

    def as_history_dicts(self) -> List[dict]:
        """Format used by query_engine.analyze_query for follow-up resolution."""
        return [
            {"query": t.query, "entity": t.entity, "topic": t.topic}
            for t in self.turns
        ]

    def as_context_string(self) -> str:
        """Compact text block passed to the LLM as prior-turn context."""
        if not self.turns:
            return ""
        lines = []
        for i, t in enumerate(self.turns, start=1):
            lines.append(f"Turn {i} — Q: {t.query}\nA (summary): {t.answer_summary}")
        return "\n".join(lines)

    def clear(self) -> None:
        self.turns = []
