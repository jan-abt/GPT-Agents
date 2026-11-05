"""
DIY GPTs - stage 1: instructions + chat.

A do-it-yourself version of chapter 3's custom GPTs, without ChatGPT Plus:
pick one of the book's instruction files, and it becomes the system message
for a chat with whatever LLM .env points at (LM Studio, Gemini or OpenAI).

Run it from the repo root with:
    .venv/bin/streamlit run chapter_03/diy_gpts/app.py
"""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).parent
INSTRUCTIONS_DIR = HERE.parent                  # chapter_03: the book's GPT instruction files

load_dotenv(HERE / ".env")                       # diy_gpts/.env, same format as chapter_2/.env
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def load_instructions(path: Path) -> str:
    """Return the text of a GPT instruction file."""
    return path.read_text(encoding="utf-8")


def build_messages(system_prompt: str, history: list[dict]) -> list[dict]:
    """The messages sent to the LLM: the GPT's instructions as the system
    message, then the whole conversation so far. Returns a new list, so the
    stored history never contains the system message."""
    return [{"role": "system", "content": system_prompt}] + history

# ---------------------------------------------------------------------------
# Sidebar: choose a GPT
# ---------------------------------------------------------------------------
gpt_files = sorted(INSTRUCTIONS_DIR.glob("*_v1.txt"))
names = {f.stem.removesuffix("_v1").replace("_", " ").title(): f for f in gpt_files}

with st.sidebar:
    st.header("DIY GPTs")
    choice = st.selectbox("Assistant", list(names))
    st.caption(f"Model: `{MODEL}`")
    if st.button("New chat"):
        st.session_state.history = []

# Start a fresh conversation when you switch to a different GPT.
if st.session_state.get("gpt") != choice:
    st.session_state.gpt = choice
    st.session_state.history = []

system_prompt = load_instructions(names[choice])

st.title(choice)
with st.expander("Instructions (system message)"):
    st.text(system_prompt)

# Show the conversation so far.
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# One chat turn
# ---------------------------------------------------------------------------
if user_text := st.chat_input("Ask your assistant..."):
    st.session_state.history.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=MODEL,
            messages=build_messages(system_prompt, st.session_state.history),
            stream=True,
        )
        reply = st.write_stream(stream)   # shows the reply as it arrives, returns the full text

    # Remember the reply, so the next turn includes it. The API is stateless:
    # without this the assistant would forget everything it said.
    st.session_state.history.append({"role": "assistant", "content": reply})
