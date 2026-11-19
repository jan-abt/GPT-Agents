# Chapter 10 on local models

The book runs each reasoning technique as a Microsoft **Prompt Flow** flow
(`prompt_flow/`). As in chapter 9, `promptflow` would downgrade packages other
chapters use, so the techniques are rebuilt in plain Python. They are only
prompts, so nothing is lost.

## `reasoning_techniques.py`: five techniques, one scoreboard

Every technique answers the same time-travel word problems, and **code**
checks each answer against a solution worked out by hand:

| Technique | Book | How | LLM calls |
|---|---|---|---|
| direct | 10.1 | "reply with the final number only" | 1 |
| zero-shot CoT | 10.2.2 | "Let's think step by step." | 1 |
| few-shot CoT | 10.2.1 | a fully worked example first | 1 |
| chaining | 10.2.3 | decompose → calculate → solve (the book's three prompts) | 3 |
| self-consistency | 10.3.1 | zero-shot CoT 3 times at temperature 1, majority vote | 3 |

TODOs 28–32 describe each part above its code. Configure the model in
`chapter_10/.env` (gitignored; same format as `chapter_2/.env.example`), then
from the repo root:
```bash
.venv/bin/python chapter_10/reasoning_techniques.py           # 4 problems, 36 LLM calls
.venv/bin/python chapter_10/reasoning_techniques.py --quick   # first 2 problems
```

**Why our own problems?** The book's problem files have no expected answers;
an LLM judges whether two answers "match" (`evaluate_answer.jinja2`), which
chapter 9 showed is unreliable. And the book's own worked example (Sarah, who
arrives 2 years early) answers 729 days by subtracting the day she spent
preparing, although that day was spent in the past too. Problem 3 here tests
exactly that trap, and the few-shot example is a new one, so the model isn't
taught the mistake.

## Tree of thoughts (10.3.2): explained, not run

The book's `tree-of-thoughts` flow asks for **three "experts"**, each writing a
step-by-step plan in `<expert1>…</expert1>` tags. The plans are split apart,
each is followed to an answer, and an evaluation step picks the best branch.
It's self-consistency with **different strategies** rather than repeated tries
of one. It costs many calls per problem (plans, solutions, evaluation), which
on a CPU means many minutes per problem.

## Not covered

`q_agent.py` is a sketch of Q-learning with placeholder code (random
"embeddings"). The book doesn't use it as an exercise.

## Results with qwen2.5-7b-instruct (4 problems, on a CPU)

```
technique           solved  LLM calls  seconds
direct                0/4          4       17
zero-shot CoT         3/4          4      307
few-shot CoT          3/4          4      233
chaining              2/4         12      312
self-consistency      3/4         12      589
```

- **Reasoning steps matter most:** asking for the number only solved nothing;
  every technique that let the model reason solved most problems.
- **More calls didn't buy more accuracy:** chaining (3 calls) did worse than a
  single "Let's think step by step" - one step treated a 100-year jump as
  ageing (Leo: 138 instead of 38).
- **Self-consistency fixes random slips, not shared mistakes:** on problem 1 it
  outvoted a stray 2105 ([2117, 2105, 2117]); on problem 3 all three runs said
  729 - unanimous and wrong.
- **Problem 3 beat every technique:** all answered 729 (or 2), subtracting the
  preparation day - the same mistake as the book's own worked example.
- Results vary between runs (temperature, model); rerun to see how stable they are.
