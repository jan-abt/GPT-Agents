# Chapter 6 on local models

## 6.1 Behavior trees: works as in the book

`py_trees` is small (under 1 MB) and needs no LLM:
```bash
.venv/bin/pip install py_trees
.venv/bin/python chapter_06/first_btree.py
```
Try changing `if True:` to `if False:` in `HasApple` to watch the Selector fall
back to the pear branch.

## 6.2–6.5: the GPT Assistants Playground

The book runs these sections in the author's separate Gradio app
(`GPTAssistantsPlayground`), built on **OpenAI's Assistants API**. That API is
OpenAI-only (paid), and OpenAI announced its retirement for 2026, so it
doesn't work with LM Studio or Gemini. The YouTube → X example (6.3.4) also
needs an X account with your password in a file.

## 6.3.2 Coding challenge ABT, rebuilt: `coding_challenge_abt.py`

An *agentic behavior tree*: py_trees nodes that call your local LLM.

```
-^- Retry (3 attempts)
    {-} Solve the challenge
        --> Hacker    (action)     LLM writes simulate_grass()       TODO 13
        --> Judge     (action)     LLM reviews and fixes the code    TODO 14
        --> Verifier  (condition)  runs the book's 6 tests           TODO 15
```
(TODO 16 builds and ticks the tree.)

Differences from the book:
- The **Verifier runs the real tests** (listing 6.6) instead of asking a third
  LLM whether the code looks right. LLM reviewers miss real bugs; tests don't.
- A **Retry decorator** (table 6.1) reruns the sequence when the tests fail,
  and the Hacker gets the failed tests as feedback.
- The nodes share data on the py_trees **blackboard** (section 6.5) instead of
  the book's `solution.py` / `judged_solution.py` files.

Configure the model in `chapter_06/.env` (gitignored; same format as
`chapter_2/.env.example`). `qwen2.5-7b-instruct` works well.

```bash
.venv/bin/python chapter_06/coding_challenge_abt.py
```

**The Verifier runs code the LLM wrote, on your machine.** It shows you the
code and asks before running it, in a separate process in a temporary folder,
with a 10-second time limit. `--yes` skips the question; use it only once you
trust what the model produces.

Each attempt takes a few minutes on a CPU (two LLM calls).
