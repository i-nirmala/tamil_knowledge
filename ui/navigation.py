"""UI navigation helpers. Keeps page navigation inside the same Streamlit session."""
from __future__ import annotations
import streamlit as st

HOME = "⌂ Home · முகப்பு"

def init_navigation() -> None:
    st.session_state.setdefault("page_stack", [])

def navigate(page: str) -> None:
    init_navigation()
    current = st.session_state.get("current_page", HOME)
    if current != page:
        stack = st.session_state.get("page_stack", [])
        stack.append(current)
        st.session_state.page_stack = stack[-20:]
    st.session_state.current_page = page
    st.rerun()

def go_back(default: str = HOME) -> None:
    init_navigation()
    stack = st.session_state.get("page_stack", [])
    if stack:
        st.session_state.current_page = stack.pop()
        st.session_state.page_stack = stack
    else:
        st.session_state.current_page = default
    st.rerun()
