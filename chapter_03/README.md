# Chapter 3: Engaging GPT assistants (p. 39–67)

**In one sentence:** a custom GPT is instructions + optional knowledge +
optional actions, wrapped in a chat; we rebuild ChatGPT's no-code GPT Builder
in code as **DIY GPTs** (`diy_gpts/`).

The book builds everything in ChatGPT (paid). `diy_gpts/README.md` documents
the app in detail; this page is the walkthrough.

## Key ideas

| Book section | ChatGPT feature | DIY GPTs |
|---|---|---|
| 3.1 GPTs in ChatGPT (p. 40) | instructions = the system message | stage 1, `app.py` |
| 3.2 Data Scout (p. 44) | code interpreter on a CSV | not built (chapter 4 runs generated code) |
| 3.3 Custom actions (p. 49–56) | a web API described by its OpenAPI spec | stage 3, `actions.py` (chapter 5's technique) |
| 3.4 Knowledge (p. 56–62) | uploaded files, searched per question | stage 2, `knowledge.py` (chapter 8 adds embeddings) |
| 3.5 Publishing (p. 62) | the GPT Store | our GitHub fork |

The instruction files are in this folder: `culinary_companion_v1.txt`,
`calculus_made_easy_v1.txt`, `task_organizer_v1.txt`, … Any `*_v1.txt` shows up
in the app.

## Walkthrough (stage 1: instructions + chat)

```bash
cd ~/Code/GPT-Agents && .venv/bin/streamlit run chapter_03/diy_gpts/app.py
```
(In IntelliJ: a Python run configuration with module `streamlit`, parameters
`run app.py`, working directory `chapter_03/diy_gpts`.)

1. Pick **Culinary Companion**, open **Instructions (system message)**, and ask
   for a recipe. The instructions are all the GPT "is".
2. Read `app.py`, TODOs 1–3: load the instructions, build `messages` (system
   message + history), save each reply to the history. Without TODO 3 the
   assistant forgets what it said.
3. Note what a text model can't do: the instructions say "always create an
   image", so the model *describes* one. In ChatGPT that's a tool call.
4. Ask an off-topic question (how to repair a motorcycle). The GPT only has
   the boundaries its instructions give it; a 3B model often refused and then
   answered anyway.

Stages 2–4 are walked through with chapters 5 (actions) and 8 (knowledge,
memory).

## Setup notes
`diy_gpts/.env` (gitignored) holds the chat model and `EMBEDDING_MODEL`.
Packages: `.venv/bin/pip install -r chapter_03/diy_gpts/requirements.txt`.
