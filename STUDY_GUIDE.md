# Study guide: *AI Agents in Action* on local models

A walk through the book's 11 chapters with this repo's code, without paid
OpenAI features. Each chapter folder has a README: the idea in one sentence,
key ideas with book page numbers, a hands-on walkthrough, and what we found
with local models.

| # | Chapter | Hands-on with | README |
|---|---|---|---|
| 1 | Introduction to agents | concepts only: the agent components map | [chapter_01](chapter_01/README.md) |
| 2 | Harnessing LLMs | the chat API, message history, JSON output, prompt tactics | [chapter_2](chapter_2/README.md) |
| 3 | GPT assistants | **DIY GPTs** stage 1: personas + chat | [chapter_03](chapter_03/README.md) |
| 4 | Multi-agent systems | AutoGen: proxy, critic, group chat | [chapter_04](chapter_04/README.md) |
| 5 | Actions | function calling; SK ideas in plain Python; DIY GPTs stage 3 | [chapter_05](chapter_05/README.md) |
| 6 | Autonomous assistants | behavior trees; a Hacker/Judge/Verifier tree | [chapter_06](chapter_06/README.md) |
| 7 | Agent platforms | Streamlit chat apps; DIY GPTs as our "Nexus" | [chapter_07](chapter_07/README.md) |
| 8 | Memory and knowledge | embeddings, Chroma; DIY GPTs stages 2 + 4 | [chapter_08](chapter_08/README.md) |
| 9 | Prompt evaluation | comparing profiles with an LLM judge | [chapter_09](chapter_09/README.md) |
| 10 | Reasoning | five techniques on problems with known answers | [chapter_10](chapter_10/README.md) |
| 11 | Planning and feedback | a planner that replans from errors | [chapter_11](chapter_11/README.md) |

The exercises are numbered **TODO 1–37** across the repo, each with its task
description above the solution. In IntelliJ: **View → Tool Windows → TODO**
(`Alt+6`).

## Before starting

**LM Studio** (the local LLM server): one script starts the server and loads
the chat and embedding models, skipping anything already running:
```bash
cd ~/Code/GPT-Agents && ./start_lmstudio.sh
```
It runs these steps (the embedding model is only needed for DIY GPTs and
chapters 8 and 11):
```bash
~/.lmstudio/bin/lms server start
~/.lmstudio/bin/lms load qwen2.5-7b-instruct --yes
~/.lmstudio/bin/lms load text-embedding-nomic-embed-text-v1.5 --yes
```
Don't run `lms load` for a model that's already loaded: it starts a second
copy (`qwen2.5-7b-instruct:2`) using the memory twice; `lms unload` removes it.
If a script says "Connection error", the server isn't running (it stops after
a restart): run the script again.

| Model | Used for |
|---|---|
| `qwen2.5-7b-instruct` (4.7 GB) | the all-rounder: chat, tool calls, code, judging |
| `llama-3.2-3b-instruct` (2.0 GB) | quick tests; tool calls only one at a time |
| `text-embedding-nomic-embed-text-v1.5` (84 MB) | embeddings |

**Python:** the shared `.venv` (Python 3.14). Each chapter README lists its
packages. **Settings:** each chapter has its own gitignored `.env` (chapter 4:
`OAI_CONFIG_LIST`); `chapter_2/.env.example` is the template.

**Run scripts from the repo root** unless a README says to `cd` into the
chapter folder. Use `~/Code/GPT-Agents/.venv/bin/python`, not `../.venv/...`
(the relative path prints harmless `sys.prefix` warnings).

## Suggested route for one session
1. Chapters 1–2 (30 min): components; `connecting.py`, `message_history.py`,
   `prompt_engineering.py`.
2. Chapters 3, 5, 8 together (60 min): DIY GPTs stages 1 → 3 → 2 + 4, the app
   growing component by component.
3. Chapter 4 (20 min): `autogen_coding_critic.py`.
4. Chapter 6 (20 min): `first_btree.py`, then the coding-challenge tree.
5. Chapter 7 (10 min): the streaming chat app.
6. Chapters 9–10 (read the results; the runs take 15–25 min each on a CPU,
   so start one early).
7. Chapter 11 (15 min): the planner, with both goals.

## Recurring lessons
- An LLM is text in, text out; tools, memory and plans are all built around
  that by your code.
- Models differ in what they were trained for (tool calls, code).
- Fluent isn't correct: check with code wherever you can.
- Structure (JSON schemas, trees, plans) makes small models reliable.
