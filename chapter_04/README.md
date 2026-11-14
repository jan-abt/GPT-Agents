# Chapter 4 on local and free models

The book runs chapter 4 with GPT-4 and the 2024 versions of AutoGen and
CrewAI. Those packages have changed a lot since then. This page explains how
to run the chapter with a local model in LM Studio (or Gemini's free tier) on
current packages, and which parts don't work any more.

## What works where

| Section | Book uses | Status here |
|---|---|---|
| 4.2–4.3 AutoGen: agents, critic, group chat | `pyautogen` 0.2 | ✅ works with **AG2 0.14** (see below) |
| 4.4–4.5 CrewAI | `crewai[tools]` | ❌ CrewAI needs Python ≤ 3.13; this venv is 3.14 |
| 4.4.2 AgentOps | `agentops` | installs, but it's a cloud service (sign-up + API key; agent conversations are sent to their servers) |
| 4.1 AutoGen Studio | `autogenstudio` | ❌ doesn't install on 3.14, and today's version is a rewrite whose UI no longer matches the book |
| `describe_image.py` | GPT-4 Vision | needs a vision model; the local Llama is text-only |

## Why AG2 0.14

- `pip install pyautogen` now installs Microsoft's rewritten AutoGen (0.7+),
  which has a different API: the book's `from autogen import AssistantAgent, ...`
  fails.
- **AG2** is the community fork that kept the original API. Its 1.x versions
  changed the API again, so install the last 0.x version:
  ```bash
  .venv/bin/pip install "ag2[openai]<1"
  ```
- AG2 0.14 removed `config_list_from_json()`. The four `autogen_*.py` scripts
  have one changed line each:
  ```python
  config_list = LLMConfig.from_json(path="OAI_CONFIG_LIST").config_list
  ```
  Everything else is the book's code.

## Configure the model

The scripts read `OAI_CONFIG_LIST` from this folder (gitignored). For LM Studio:
```bash
cp chapter_04/OAI_CONFIG_LIST.lmstudio.sample chapter_04/OAI_CONFIG_LIST
```
The sample uses `llama-3.2-3b-instruct`. A 7B model writes noticeably better
code and more reliably answers with a ` ```python ` block: change `"model"` to
`qwen2.5-7b-instruct` (4.7 GB, Q4_K_M GGUF). In a comparison on the book's
snake-game task, it matched the code-specialised `qwen2.5-coder-7b-instruct`
(valid Python with game over, growing snake, food and arrow keys each time) in
about half the time, and unlike the Coder model it also handles tool calls.

For Gemini's free tier, use this content instead (your key, model of choice):
```json
[
    {
        "model": "gemini-3.5-flash-lite",
        "api_key": "<your Gemini API key>",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/"
    }
]
```
Agent conversations use many requests; Gemini's free tier allows about 20 per
day per model, so LM Studio is the better choice here.

## Run the scripts

The scripts are plain Python (not Streamlit). In IntelliJ, open the script and
click ▶. The run configuration's **working directory must be `chapter_04`**,
because that's where `OAI_CONFIG_LIST` is looked up. From a terminal:
```bash
cd chapter_04 && ../.venv/bin/python autogen_start.py
```

Suggested order: `autogen_start.py` → `autogen_coding_critic.py` →
`autogen_coding_critic_cache.py` → `autogen_coding_group.py`.

The book's task in every script is a snake game with Pygame. `pygame` has no
build for Python 3.14; the community edition is a drop-in replacement
(`import pygame` still works, about 12 MB):
```bash
.venv/bin/pip install pygame-ce
```

## ⚠️ These agents run code on your computer

The user agent (`UserProxyAgent`) executes the Python code the model writes,
with `use_docker: False`, directly on your machine, in `chapter_04/working/`
(gitignored).

- `autogen_start.py` and the two `autogen_coding_critic*.py` scripts use
  `human_input_mode="ALWAYS"`: the agent stops and waits for you in the Run
  console before each step. **Read the code before you press Enter.** Type
  `exit` to stop.
- **`autogen_coding_group.py` uses `human_input_mode="NEVER"`**: it runs
  whatever code the model writes, without asking, for up to 20 rounds. Change
  it to `"ALWAYS"` before running it, at least until you've seen what the
  local model produces.

The book recommends Docker for running agent code safely; that's
`"use_docker": True` (requires Docker to be installed).

## What to expect from a 3B model

- Simple two-agent chats work well.
- Code quality is modest: expect a snake game that needs a few rounds of
  fixes, or doesn't run. Seeing the critic catch (or miss) problems is part of
  the lesson.
- In a group chat the manager uses the model to pick who speaks next. Small
  models are unreliable at this, so the conversation may wander or loop.
  Gemini does better if you have requests left.
