"""Browser-native voice input Streamlit component."""
from __future__ import annotations
from pathlib import Path
import streamlit.components.v1 as components

_COMPONENT = components.declare_component(
    "code_bloom_voice_input",
    path=str(Path(__file__).resolve().parent / "voice_component"),
)

def voice_input(key: str = "voice", language: str = "ta-IN") -> str:
    value = _COMPONENT(key=key, language=language, default="")
    return value or ""
