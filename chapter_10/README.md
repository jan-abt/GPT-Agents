# Chapter 10: Agent reasoning and evaluation (p. 244–271)

**In one sentence:** how you prompt changes how well an LLM reasons; letting
it think step by step helps most, and only measuring against known answers
tells you what actually works.

## Key ideas

| Technique | Book | How |
|---|---|---|
| Question-and-answer | 10.1.1, p. 246 | answer from given context; say "Unsure" if not sure |
| Few-shot | 10.1.2, p. 248 | examples first (made-up words "whatpu", "farduddle") |
| Zero-shot | 10.1.3, p. 250 | no examples ("classify as neutral, negative or positive") |
| Chain of thought (CoT) | 10.2.1, p. 253 | a fully worked example first |
| Zero-shot CoT | 10.2.2, p. 257 | just add "Let's think step by step." |
| Prompt chaining | 10.2.3, p. 258 | decompose → calculate → combine, one call each |
| Self-consistency | 10.3.1, p. 262 | the same CoT several times, majority answer |
| Tree of thoughts | 10.3.2, p. 266 | three "experts" each plan; the best branch wins |

## Walkthrough

1. Skim the book's prompts in `prompt_flow/`: `zero-shot-cot-prompting/cot.jinja2`
   ("Let's think step by step") and the three `prompt-chaining/*.jinja2`
   templates.
2. Run our comparison (four time-travel word problems with answers worked out
   by hand, checked by code):
   ```bash
   cd ~/Code/GPT-Agents && .venv/bin/python chapter_10/reasoning_techniques.py   # ~25 min on a CPU
   ```
   `--quick` runs two problems. TODO 28 asks and extracts the number, 29 the
   single-call techniques, 30 chaining, 31 self-consistency (with votes), 32 the
   scoreboard.

## What we found (qwen2.5-7b-instruct)
```
technique           solved  LLM calls  seconds
direct                0/4          4       17
zero-shot CoT         3/4          4      307
few-shot CoT          3/4          4      233
chaining              2/4         12      312
self-consistency      3/4         12      589
```
- **Room to reason is what matters:** "answer only" solved nothing.
- **More calls ≠ better:** chaining did worse; one step treated a 100-year jump
  as ageing (138 instead of 38).
- **Self-consistency fixes random slips, not shared mistakes:** it outvoted a
  stray 2105 on problem 1, but on problem 3 all runs said 729: unanimous and
  wrong.
- **Problem 3 beat everything:** the answer is 730 (the preparation day is one
  of the days in the past); every technique, and the book's own worked
  example, says 729.

## Why our own problems
The book's problem files have no expected answers (an LLM judges whether
answers "match"), and its worked example contains the 729 mistake. Results vary
between runs (temperature); rerun to see how stable they are. Tree of thoughts
isn't run: many calls per problem, too slow on a CPU. `q_agent.py` is a
placeholder sketch the book doesn't use.

## Setup notes
Prompt Flow isn't installed (see chapter 9). `chapter_10/.env` (gitignored)
sets the model.
