# Chapter 11 on local models

The book's chapter 11 planner (`basic_nexus_planner.py`) lives inside Nexus,
which we don't install (see chapter 7), and 11.2 uses the OpenAI Assistants
API. The files in this folder (`assistants_api*.py`, `gradio_*.py`,
`streamlit_*assistants*.py`, `webcam.py`, …) are the author's Assistants API
and Gradio experiments rather than the chapter's planner; they need OpenAI.

## `planner.py`: a sequential planner with feedback (11.3, 11.5)

```
goal ──▶ PLANNER: one LLM call writes a JSON plan from the available functions   TODO 34
plan ──▶ EXECUTOR: code runs the steps in order, passing outputs along           TODO 35, 36
error ──▶ FEEDBACK: the planner gets the error and writes a new plan (3 tries)   TODO 37
```

The available functions (TODO 33) reuse earlier work: `search_calculus_book`
(chapter 8 embeddings, via DIY GPTs' `knowledge.py`), `summarize` (a semantic
function), `save_file` (writes only into `chapter_11/output/`, gitignored)
and `get_tasks` (DIY GPTs' task API, if it's running). A plan step can use an
earlier output as `"{s1}"`, and the special `for-each` function runs a
function once per list item, as in the book's planner.

Setup: `chapter_11/.env` (gitignored) needs `OPENAI_*` and `EMBEDDING_MODEL`,
as in `chapter_08/.env`; load both models in LM Studio. Then from the repo root:
```bash
.venv/bin/python chapter_11/planner.py                    # the default goal
.venv/bin/python chapter_11/planner.py "your own goal"
```

Differences from the book's planner:
- **The plan is JSON with a schema** (strings or lists of strings), so it can
  always be read; with free-form arguments, Qwen invented its own reference
  format.
- **References name the step** (`{s1}`), not the function
  (`output_GetJokeTopics`), so the same function can be used twice.
- **Errors go back to the planner as feedback** and it plans again.

## Results with qwen2.5-7b-instruct

**Default goal** (look up two topics in Calculus Made Easy, summarise each,
save both): a 5-step plan on the first attempt (two searches, two summaries,
one `save_file`), in 3 min 19 s.

**A goal needing a missing function** ("…and email the summary to my friend
Alex"):
1. The first plan called `EmailTo`, a function that exists only in the planner
   prompt's **few-shot example**. The example leaked into the plan.
2. The executor stopped: *unknown function 'EmailTo'; available: …*
3. With that feedback, the second plan saved the summary to a file instead.

Possible improvements (good exercises):
- **Validate the plan before running it** (unknown functions, wrong
  arguments, references to later steps). Here, steps s1–s2 ran twice because
  the bad step was only found during execution.
- **Use an example with the real functions**, or several varied examples, so
  example-only functions don't leak into plans.
- **Let the final report say what couldn't be done** (no email was sent).
