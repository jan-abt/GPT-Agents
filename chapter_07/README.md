# Chapter 7 on local models

## 7.2 The Streamlit chat apps: work as in the book

Both scripts use the plain `openai` client, so they run on LM Studio. Give
this folder its own `.env` (gitignored; same format as
`chapter_2/.env.example`), then from the repo root:
```bash
.venv/bin/streamlit run chapter_07/chatgpt_clone_response.py
.venv/bin/streamlit run chapter_07/chatgpt_clone_streaming.py
```
They differ only in how the reply arrives: all at once behind a spinner
(`response`), or word by word with `st.write_stream()` (`streaming`). This is
the same pattern as stage 1 of `chapter_03/diy_gpts`.

## 7.1, 7.3–7.5: Nexus, the author's agent platform

The book installs Nexus with
`pip install git+https://github.com/cxbxmxcx/Nexus.git` on Python 3.10. Its
dependencies are pinned to 2024 versions (`chromadb 0.4`, `langchain 0.1`,
`fastapi 0.110`, …) and are heavy, so they are unlikely to install on
Python 3.14. We skipped installing it and read these sections for the ideas,
which `chapter_03/diy_gpts` already implements:

| Nexus (book) | DIY GPTs |
|---|---|
| agent **profile** with a persona (YAML file, 7.3) | instruction files `chapter_03/*_v1.txt` |
| agent **engine** that calls the LLM (7.4) | `app.py`'s chat loop |
| **actions**: native and semantic functions (7.5) | `actions.py` (stage 3), `chapter_05/movie_recommender.py` |
| knowledge/memory (later chapters) | `knowledge.py` (stage 2) |

One Nexus convenience DIY GPTs doesn't have: an `@agent_action` decorator
generates the tool's JSON Schema from the Python function's signature and
docstring, where DIY GPTs writes it by hand (`task_tools()`).
