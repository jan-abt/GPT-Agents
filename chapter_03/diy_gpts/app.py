"""
DIY GPTs - a do-it-yourself version of chapter 3's custom GPTs, without
ChatGPT Plus.

Stage 1, instructions + chat: pick one of the book's instruction files, and it
becomes the system message for a chat with whatever LLM .env points at
(LM Studio, Gemini or OpenAI).
Stage 2, knowledge: a GPT with a PDF of the same name answers from the most
relevant excerpts of that PDF (see knowledge.py).
Stage 3, actions: the Task Organizer can call a web API through function
calling (see actions.py).
Stage 4, memory: facts about you are extracted from each exchange, stored,
and recalled in later chats, by every GPT (see memory.py).

Run it from the repo root with:
    .venv/bin/streamlit run chapter_03/diy_gpts/app.py
"""
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

import actions
import knowledge
import memory

HERE = Path(__file__).resolve().parent
INSTRUCTIONS_DIR = HERE.parent                  # chapter_03: the book's GPT instruction files

load_dotenv(HERE / ".env")                       # diy_gpts/.env, same format as chapter_2/.env
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# TODO 1: return the text of the instruction file at `path`.
# Hint: Path has a method that reads a whole file as a string.
# ---------------------------------------------------------------------------
def load_instructions(path: Path) -> str:
    return path.read_text(encoding="utf-8")

# ---------------------------------------------------------------------------
# TODO 2: build the list of messages to send to the LLM.
#   - system_prompt: the GPT's instructions (a string)
#   - history: the conversation so far, a list like
#       [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
# Return a NEW list: the system message first, then the whole history.
# (Same shape as the `messages` lists in chapter 2.)
# ---------------------------------------------------------------------------
def build_messages(system_prompt: str, history: list[dict]) -> list[dict]:
    return [{"role": "system", "content": system_prompt}] + history

# ---------------------------------------------------------------------------
# Sidebar: choose a GPT
# ---------------------------------------------------------------------------
gpt_files = sorted(INSTRUCTIONS_DIR.glob("*_v1.txt"))
names = {f.stem.removesuffix("_v1").replace("_", " ").title(): f for f in gpt_files}

with st.sidebar:
    st.header("DIY GPTs")
    choice = st.selectbox("Assistant", list(names))
    knowledge_pdf = knowledge.knowledge_file_for(names[choice])
    use_knowledge = st.toggle(
        "Use knowledge",
        value=knowledge_pdf is not None,
        disabled=knowledge_pdf is None,
        help=f"Answer from excerpts of {knowledge_pdf.name}" if knowledge_pdf
             else "This GPT has no knowledge file (a PDF with the same name).",
    )
    # Chapter 8: how to find the excerpts - by matching words, or by meaning.
    search_method = st.radio(
        "Search the book by", ["Keywords", "Embeddings"], index=1, horizontal=True,
        disabled=not use_knowledge,
        help="Keywords: count matching words (TODO 5). Embeddings: compare meaning "
             "with the local embedding model (TODOs 17-19).",
    )
    gpt_has_actions = actions.has_actions(names[choice])
    use_actions = st.toggle(
        "Use actions",
        value=gpt_has_actions,
        disabled=not gpt_has_actions,
        help="Let the LLM call the task API (actions.py)" if gpt_has_actions
             else "This GPT has no actions.",
    )
    if use_actions:
        if actions.api_is_up():
            st.caption(f"Task API: ✅ {actions.TASKS_API}")
        else:
            st.caption("Task API: ❌ not running - start it with "
                       "`cd chapter_03 && ../.venv/bin/uvicorn daily_tasks_api:app --port 8100`")
    # Stage 4: long-term memory, shared by all GPTs.
    use_memory = st.toggle("Use memory", value=True,
                           help="Remember facts about you across chats and GPTs (memory.py)")
    stored = memory.load_store()
    with st.expander(f"Memories ({len(stored)})"):
        for item in stored:
            st.caption(f"• {item['text']}")
        if stored and st.button("Forget everything"):
            memory.forget_all()
            st.rerun()
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
        # Knowledge: look up the excerpts that match this question and add them
        # to the system message for this turn only (they aren't kept in history).
        turn_prompt = system_prompt
        if use_knowledge and knowledge_pdf:
            chunks = knowledge.split_into_chunks(knowledge.load_text(knowledge_pdf))
            if search_method == "Embeddings":
                # The first time, every chunk is embedded (about a minute); after
                # that the vectors come from the cache in .cache/.
                with st.spinner("Embedding the book (first time only)..."):
                    vectors = knowledge.load_vectors(client, knowledge_pdf, chunks)
                found = knowledge.semantic_search(client, chunks, vectors, user_text)
            else:
                found = knowledge.search(chunks, user_text)
            turn_prompt = knowledge.add_knowledge(system_prompt, found)
            with st.expander(f"Knowledge: {len(found)} excerpts from {knowledge_pdf.name} "
                             f"({search_method.lower()})"):
                for i, chunk in enumerate(found, 1):
                    st.caption(f"Excerpt {i}")
                    st.text(chunk)

        # Memory (stage 4): recall facts relevant to this question.
        if use_memory:
            recalled = memory.recall(client, user_text)
            turn_prompt = memory.add_memories_to_prompt(turn_prompt, recalled)
            if recalled:
                with st.expander(f"Memory: {len(recalled)} fact(s) recalled"):
                    for fact in recalled:
                        st.caption(f"• {fact}")

        messages = build_messages(turn_prompt, st.session_state.history)
        reply = None

        # Actions: first ask the LLM with the tools attached. If it wants to call
        # one, run the calls and add the results to the messages for the final
        # answer below. (Like the history excerpts, they're kept for this turn only.)
        if use_actions:
            first = client.chat.completions.create(
                model=MODEL, messages=messages, tools=actions.task_tools(),
            ).choices[0].message
            if first.tool_calls:
                results = actions.run_tool_calls(first.tool_calls)
                # The LLM's request goes into the messages too, so the tool
                # results that follow have a call they answer.
                messages = messages + [first.model_dump(exclude_none=True)] + results
                with st.expander(f"Actions: {len(first.tool_calls)} call(s)"):
                    for call, result in zip(first.tool_calls, results):
                        st.caption(f"{call.function.name}({call.function.arguments})")
                        st.code(result["content"], language="json")
            else:
                reply = first.content or ""   # no tool needed: this is already the answer
                st.markdown(reply)

        if reply is None:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                stream=True,
            )
            reply = st.write_stream(stream)   # shows the reply as it arrives, returns the full text

    # -----------------------------------------------------------------------
    # TODO 3: remember the assistant's reply, so the next turn includes it.
    # Without this line the assistant "forgets" everything it said
    # (remember the message-history lesson from chapter 2).
    # -----------------------------------------------------------------------
    st.session_state.history.append({"role": "assistant", "content": reply})

    # Memory (stage 4): let the LLM pick out facts about you worth keeping.
    # That's one more LLM call per turn - switch "Use memory" off to skip it.
    if use_memory:
        with st.spinner("Updating memory..."):
            added = memory.add_memories(client, memory.extract_facts(client, MODEL, user_text, reply))
        if added:
            st.caption("🧠 Remembered: " + " · ".join(added))
