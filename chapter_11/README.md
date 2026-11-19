# Chapter 11: Agent planning and feedback (p. 272–298)

**In one sentence:** an agent becomes more than a chatbot when it turns a
goal into a plan, executes it with tools, and uses errors as feedback to
replan.

## Key ideas

- **Planning is essential (11.1, p. 273):** given a multi-step goal, an LLM
  calling one tool at a time easily loses track.
- **Sequential planning (11.2, p. 277):** some platforms (OpenAI Assistants,
  Claude) plan internally; most models can only call tools.
- **A sequential planner (11.3, p. 278):** one LLM call writes the **whole plan
  up front as JSON**, a list of subtasks using only the available functions,
  including a special **for-each**. Then **code** executes the steps, passing
  outputs along. The LLM doesn't even need tool-calling support.
- **Stepwise planners (11.4, p. 285):** reasoning models (OpenAI's o1
  "Strawberry") plan and check themselves internally.
- **Planning + reasoning + evaluation + feedback (11.5, p. 288):** the book's
  synthesis. Planning ahead skips the feedback loop, so feed errors back in.

## Walkthrough

```bash
cd ~/Code/GPT-Agents && .venv/bin/python chapter_11/planner.py
cd ~/Code/GPT-Agents && .venv/bin/python chapter_11/planner.py "Find what Calculus Made Easy says about the letter d in dx, summarize it, and email the summary to my friend Alex."
```
```
goal  ──▶ PLANNER  (one LLM call → JSON plan)          TODO 34
plan  ──▶ EXECUTOR (code runs the steps)               TODO 35 (references), 36 (execution)
error ──▶ FEEDBACK (the planner replans, 3 attempts)   TODO 37
```
The available functions (TODO 33) reuse earlier work:
`search_calculus_book` (chapter 8 embeddings), `summarize` (a semantic
function), `save_file` (writes only into `chapter_11/output/`), `get_tasks`
(the DIY GPTs task API, if running). Steps refer to earlier outputs as `{s1}`.
No model-written code runs: plans can only call these functions.

## What we found
1. **Default goal:** a 5-step plan on the first attempt (two searches, two
   summaries, one file), in 3 min 19 s. One weak spot: the integration search
   found the "finding your way back" analogy, not "∫ means the sum of".
2. **Email goal:** the first plan used `EmailTo`, a function that exists only
   in the prompt's **example**; the executor stopped ("unknown function
   'EmailTo'"); with that feedback, the second plan saved the summary to a
   file instead.

Improvements worth trying: validate plans before running them (steps 1–2 ran
twice), use examples with the real functions, and make the final report say
what couldn't be done.

## About the other files here
The book's planner lives in Nexus (`basic_nexus_planner.py`); the files in
this folder (`assistants_api*.py`, `gradio_*.py`, `streamlit_*assistants*.py`,
`webcam.py`, …) are the author's OpenAI Assistants API and Gradio experiments
and need OpenAI.

## Setup notes
`chapter_11/.env` (gitignored) needs the chat model and `EMBEDDING_MODEL`, as in
`chapter_08/.env`; load both models in LM Studio.
