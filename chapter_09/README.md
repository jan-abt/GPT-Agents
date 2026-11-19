# Chapter 9: Mastering agent prompts with prompt flow (p. 212–243)

**In one sentence:** compare prompts systematically: run every variant over
the same batch of inputs, score the answers with a rubric, and let the numbers
decide.

## Key ideas

- **Systematic prompt engineering (9.1, p. 213):** write → evaluate → change →
  evaluate again, on many inputs, not one gut-feeling example.
- **Profiles vs. personas (9.2, p. 216):** the persona is the personality
  part; the profile is the whole agent prompt.
- **Prompt Flow (9.3, p. 217):** Microsoft's tool for prompt pipelines: LLM
  nodes fill **Jinja2 templates** (`{{subject}}`, `{{genre}}`), Python nodes
  process the output, and flows can be served as an API.
- **Rubrics and grounding (9.4–9.5, p. 224–229):** a rubric is a marking
  scheme (criteria + points); grounding checks the answer against what was
  asked, or against facts.
- **LLM as judge (9.6, p. 230):** an LLM scores another LLM's answers with the
  rubric.
- **Comparing profiles (9.7, p. 232):** batch runs over test requests, parse
  the scores, compare averages.

## Walkthrough

1. Look at the book's flow in `prompt_flow/recommender_with_grounding/`:
   `recommend.jinja2` and `recommender_variant_1.jinja2` (two profiles),
   `evaluate_recommendation.jinja2` (the rubric), `bulk_recommend.jsonl` (10
   test requests), `flow.dag.yaml` (how the nodes connect).
2. Run our plain-Python version, which uses those same files:
   ```bash
   cd ~/Code/GPT-Agents && .venv/bin/python chapter_09/evaluate_profiles.py   # 4 requests, ~14 min on a CPU
   ```
   TODO 24 renders a Prompt Flow chat template into messages, TODO 25 asks a
   variant, TODO 26 is the judge (JSON with scores 1–5), TODO 27 runs the batch
   and prints the comparison. `--all` runs all 10 requests.

## What we found
```
variant      subject   format    genre   custom  overall  items
variant_0       4.92     3.50     4.75     4.42     4.40     12
variant_1       4.67     3.75     4.75     4.50     4.42     12
```
- **A tie:** 12 items per variant is far too few to separate them.
- The judge caught **format** problems (a TV series offered as a podcast).
- The judge missed **invented titles** ("The Goblin Queen Chronicles: The
  Podcast") and arguably an R-rated book. It checks answers against the
  request, not against reality.
- The same model was player and referee.
- The book's rubric asks for scores 1–5 but shows an example with 8 and 10, and
  its parser breaks on small format changes; we ask for JSON with a schema.

## Setup notes
Installing `promptflow` in the shared `.venv` would downgrade about a dozen
packages other chapters use (`fastapi`, `pandas`, `protobuf`, …); a separate
environment would be about 71 MB. Our script needs nothing extra.
`chapter_09/.env` (gitignored) sets the model.
