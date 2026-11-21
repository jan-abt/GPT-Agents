# Chapter 4: Exploring multi-agent systems (p. 68–97)

**In one sentence:** several agents with different roles (writer, reviewer,
user proxy) working on one task do better than one prompt, and the way they
talk to each other matters.

## Key ideas

- **Roles (4.2.2, p. 79):** the same LLM with different system messages
  (Engineer, Reviewer) acts as a team. One checking the other's work catches
  what a single pass misses.
- **The user proxy:** an agent that stands in for you. It doesn't call the
  LLM; it asks you for input and **runs the code** other agents write, then
  reports the output back. This is the "code interpreter" idea from chapter 3.
- **Nested chat vs. group chat (4.3, p. 82):** a nested chat passes work along
  agent by agent (it can lose information, like the telephone game); a group
  chat shares one conversation, with a manager LLM choosing who speaks next.
- **Cache (4.2.3, p. 81):** stored replies make reruns instant and identical.
- **CrewAI (4.4–4.5, p. 84–95):** the same goal with a different design:
  agents with role, goal and backstory work through explicit tasks,
  sequentially or hierarchically. **AgentOps (4.4.2, p. 87)** shows the cost:
  one joke from the book's crew cost over 50 cents on GPT-4.
- **Agent-written code is fragile:** libraries change after the model's
  training, so the book prefers giving agents tested tools (chapter 5).

## Walkthrough

Every script's task is a snake game. **These agents run model-written code on
your machine:** read it before pressing Enter.
```bash
(cd chapter_04 && python autogen_start.py)
```
1. **`autogen_start.py`**: user proxy + assistant. At the prompt, **Enter**
   runs the code in the last message, **text** sends feedback, **`exit`**
   stops. If the model's reply has no ` ```python ` block, Enter sends an empty
   message (we saw Llama answer "your input was incomplete").
2. **`autogen_coding_critic.py`**: after the Engineer answers, a nested chat
   with the **Reviewer** runs automatically, listing issues.
3. **`autogen_coding_critic_cache.py`**: the same, cached in `.cache/42`; run
   it twice. Change `cache_seed` for a fresh answer.
4. **`autogen_coding_group.py`**: a group chat; watch the order in which the
   manager picks speakers. (Set to `human_input_mode="ALWAYS"` here; the book
   uses `"NEVER"`, which runs code unasked for up to 20 rounds.)

## What works where

| Section | Status here |
|---|---|
| 4.2–4.3 AutoGen | ✅ with **AG2 0.14** (below) |
| 4.1 AutoGen Studio | ❌ doesn't install on Python 3.14; today's version no longer matches the book's UI |
| 4.4–4.5 CrewAI | ❌ needs Python ≤ 3.13 (read for the ideas) |
| 4.4.2 AgentOps | a cloud service (sign-up; conversations go to their servers) |
| `describe_image.py` | needs a vision model and an OpenAI key |

## Setup notes
- `pip install pyautogen` now installs Microsoft's rewritten AutoGen with a
  different API. Use the fork that kept the book's API:
  `pip install "ag2[openai]<1"`. Each script has one changed line:
  `LLMConfig.from_json(path="OAI_CONFIG_LIST").config_list`.
- `OAI_CONFIG_LIST` (gitignored) in this folder picks the model: copy
  `OAI_CONFIG_LIST.lmstudio.sample` and set `"model"` to `qwen2.5-7b-instruct`.
  For Gemini, use its `base_url` and your key; agent runs use many requests.
- The snake game needs `pygame-ce` (`pygame` has no build for Python 3.14):
  `pip install pygame-ce`.
- Run from this folder (IntelliJ: working directory `chapter_04`), because
  `OAI_CONFIG_LIST` is looked up there. Generated code goes to `working/`.
