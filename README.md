# Study guide: *AI Agents in Action* on local models

The code for Micheal Lanham's book *AI Agents in Action* (Manning), forked from [cxbxmxcx/GPT-Agents](https://github.com/cxbxmxcx/GPT-Agents)
and adapted to run on free, local models (LM Studio) or Gemini's free tier
instead of paid OpenAI features. Where the book's tools no longer install on
Python 3.14 or need OpenAI-only services, the chapters' ideas are rebuilt in
plain Python as exercises.

This guide walks through the book's 11 chapters with this repo's code. Each
chapter folder has a README: the idea in one sentence, key ideas with book
page numbers, a hands-on walkthrough, and what we found with local models.

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

> **First time?** You need Python with the project's packages, **LM Studio**
> and the **Qwen** model. See
> [Installing the prerequisites (Linux and Mac)](#installing-the-prerequisites-linux-and-mac)
> at the end of this page.

**LM Studio** (the local LLM server): one script starts the server and loads
the chat and embedding models, skipping anything already running:
```bash
./start_lmstudio.sh
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

**When you're done**, free the memory (about 5 GB) with:
```bash
./stop_lmstudio.sh
```
It unloads all models, stops the server and stops LM Studio's background
service. If the LM Studio app is open, that service belongs to the app: quit
the app to stop it. Nothing is deleted; `./start_lmstudio.sh` brings it all
back.

| Model | Used for |
|---|---|
| `qwen2.5-7b-instruct` (4.7 GB) | the all-rounder: chat, tool calls, code, judging |
| `llama-3.2-3b-instruct` (2.0 GB) | quick tests; tool calls only one at a time |
| `text-embedding-nomic-embed-text-v1.5` (84 MB) | embeddings |

**Python:** the shared `.venv` (Python 3.14). Each chapter README lists its
packages. **Settings:** each chapter has its own gitignored `.env` (chapter 4:
`OAI_CONFIG_LIST`); `chapter_2/.env.example` is the template.

**All commands in the guides run from the repo root, with the venv active.**
Once per terminal, in the repo folder (wherever you cloned it):
```bash
source .venv/bin/activate
```
Then `python`, `pip`, `streamlit` and `uvicorn` are the venv's. Scripts that
must run inside their chapter folder are written as
`(cd chapter_04 && python autogen_start.py)`: the parentheses bring you back
to the root afterwards. In IntelliJ, the project's interpreter is this `.venv`.

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

## Installing the prerequisites (Linux and Mac)

Everything here is free. Downloads are large (about 7.5 GB in total), so the
model commands below can resume after an interrupted connection.

### 1. Python and the packages
Python 3.12 or newer (this repo was tested with 3.14).
- **Linux (Ubuntu/Debian):** `sudo apt install python3 python3-venv`
- **Mac:** install Python from [python.org](https://www.python.org/downloads/)
  or with Homebrew: `brew install python`

Then, in the repo folder, create the virtual environment and install
everything the chapters use (118 packages, about 280 MB):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install openai python-dotenv streamlit pypdf numpy fastapi uvicorn requests "ag2[openai]<1" pygame-ce py_trees scikit-learn plotly chromadb
```
(Each chapter README also lists just the packages that chapter needs.)

### 2. LM Studio
- **Linux:** download the `.deb` from [lmstudio.ai](https://lmstudio.ai/download)
  and install it: `sudo apt install ./LM-Studio-*.deb` (an AppImage is offered too).
- **Mac (Apple Silicon):** download the `.dmg` from
  [lmstudio.ai](https://lmstudio.ai/download) and drag LM Studio into Applications.

Start LM Studio once: that installs its command-line tool at
`~/.lmstudio/bin/lms`, which the scripts use. The embedding model
(`text-embedding-nomic-embed-text-v1.5`) comes with LM Studio.

### 3. The models
| Model | File (Q4_K_M GGUF) | Size | Needed? |
|---|---|---|---|
| `qwen2.5-7b-instruct` | `bartowski/Qwen2.5-7B-Instruct-GGUF` | 4.7 GB | yes |
| `llama-3.2-3b-instruct` | `bartowski/Llama-3.2-3B-Instruct-GGUF` | 2.0 GB | optional (quick tests) |

**Simplest:** let LM Studio download it, and choose the `Q4_K_M` file when asked:
```bash
~/.lmstudio/bin/lms get --select https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF
```
(Or use the search in LM Studio's app.)

**On an unreliable connection:** download with `curl`, which resumes where it
stopped; rerun the same command after an interruption. Linux:
```bash
mkdir -p ~/.lmstudio/models/bartowski/Qwen2.5-7B-Instruct-GGUF && cd ~/.lmstudio/models/bartowski/Qwen2.5-7B-Instruct-GGUF && F=Qwen2.5-7B-Instruct-Q4_K_M.gguf && until [ "$(stat -c%s "$F" 2>/dev/null)" = 4683074240 ]; do curl -L -C - --connect-timeout 60 --speed-limit 1000 --speed-time 120 -o "$F" "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/$F" || sleep 30; done
```
Mac (same, but its `stat` is written `stat -f%z`):
```bash
mkdir -p ~/.lmstudio/models/bartowski/Qwen2.5-7B-Instruct-GGUF && cd ~/.lmstudio/models/bartowski/Qwen2.5-7B-Instruct-GGUF && F=Qwen2.5-7B-Instruct-Q4_K_M.gguf && until [ "$(stat -f%z "$F" 2>/dev/null)" = 4683074240 ]; do curl -L -C - --connect-timeout 60 --speed-limit 1000 --speed-time 120 -o "$F" "https://huggingface.co/bartowski/Qwen2.5-7B-Instruct-GGUF/resolve/main/$F" || sleep 30; done
```
For Llama, replace `Qwen2.5-7B-Instruct` with `Llama-3.2-3B-Instruct` in the
folder and file names, and `4683074240` with `2019377696`.

Check that a download is complete and undamaged (`sha256sum` on Linux,
`shasum -a 256` on Mac):

| File | SHA-256 |
|---|---|
| `Qwen2.5-7B-Instruct-Q4_K_M.gguf` | `65b8fcd92af6b4fefa935c625d1ac27ea29dcb6ee14589c55a8f115ceaaa1423` |
| `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | `6c1a2b41161032677be168d354123594c0e6e67d2b9227c84f296ad037c728ff` |

**On a Mac,** LM Studio also offers faster **MLX** versions of these models.
They show up under a different name; put the name `lms ls` shows into your
`.env` files as `OPENAI_MODEL`.

### 4. Check
```bash
./start_lmstudio.sh
~/.lmstudio/bin/lms ls
```
`lms ls` should list `qwen2.5-7b-instruct` and
`text-embedding-nomic-embed-text-v1.5`. Then create the chapters' `.env` files
from `chapter_2/.env.example`, as described in "Before starting".

## About the book
*AI Agents in Action* (Manning Publications) explores agents and assistants
powered by large language models: what agents are, their components
(profiles, actions, knowledge, memory, planning), natural-language interfaces,
and the tools and platforms for building them. The original code is at
[cxbxmxcx/GPT-Agents](https://github.com/cxbxmxcx/GPT-Agents); for the book,
see [Manning Publications](https://www.manning.com/).
