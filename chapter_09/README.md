# Chapter 9 on local models

The book builds everything in this chapter with Microsoft's **Prompt Flow**
(the YAML + Jinja2 flows in `prompt_flow/`), mostly through its VS Code
extension. On this project's Python 3.14 environment, installing
`promptflow` would downgrade a dozen packages other chapters use (`fastapi`,
`starlette`, `pandas`, `protobuf`, `opentelemetry`…). A separate environment
would work (about 71 MB), but we rebuilt the chapter's core idea in plain
Python instead.

## `evaluate_profiles.py`: comparing profiles with an LLM judge (9.4–9.7)

It uses the book's own files from `prompt_flow/recommender_with_grounding/`:
the two recommender profiles (`recommend.jinja2`, `recommender_variant_1.jinja2`),
the rubric (`evaluate_recommendation.jinja2`) and the test requests
(`bulk_recommend.jsonl`).

```
for each test request:
    for each profile variant:
        the LLM recommends 3 items                    TODO 24 (render the template), 25
        an LLM judge scores each item 1-5             TODO 26
average the scores per variant and compare            TODO 27
```

Configure the model in `chapter_09/.env` (gitignored; same format as
`chapter_2/.env.example`), then from the repo root:
```bash
.venv/bin/python chapter_09/evaluate_profiles.py         # first 4 requests (16 LLM calls)
.venv/bin/python chapter_09/evaluate_profiles.py --all   # all 10 (40 calls; slow on a CPU)
```

Changes from the book's flow:
- **The judge answers in JSON**, with a schema that enforces scores from 1 to 5.
  The book's rubric asks for 1–5 but shows an example with 8 and 10, and its
  parser (`parsing_results.py`) breaks as soon as the LLM formats a line
  differently.
- **A fourth criterion, `custom`**: does the item respect the request's special
  instruction ("don't include any R rated content")? That's grounding: checking
  the answer against what was actually asked.

Keep in mind that **the same model plays recommender and judge**, so it may
favour its own style; and a judge scores what it believes about a book or film,
which may itself be wrong. LLM judges are useful for comparing variants, not
as proof of quality.
