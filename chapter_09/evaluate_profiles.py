"""
Chapter 9 without Prompt Flow: compare two agent profiles with an LLM judge.

Book: chapter 9, sections 9.4-9.7 (p. 225-247): rubrics, grounding, and
"Comparing profiles: getting the perfect profile". The book does this with
Microsoft's Prompt Flow (the flow in prompt_flow/recommender_with_grounding),
which would downgrade a dozen packages in this project's environment. Here
it's plain Python, using the book's own prompt templates from that folder:

    for each test request (bulk_recommend.jsonl):
        for each profile variant (recommend.jinja2, recommender_variant_1.jinja2):
            the LLM recommends 3 items                       TODO 24, 25
            an LLM judge scores them with a rubric (1-5)     TODO 26
    average the scores per variant and compare               TODO 27

That's "systematic prompt engineering" (9.1): instead of trying a prompt and
deciding by feel, run every variant over the same batch of inputs and let a
rubric decide.

Run it from the repo root (uses OPENAI_* from chapter_09/.env):
    .venv/bin/python chapter_09/evaluate_profiles.py            # first 4 requests
    .venv/bin/python chapter_09/evaluate_profiles.py --all      # all 10 (slow on a CPU)
"""
import json
import os
import re
import sys
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv
from jinja2 import Template
from openai import OpenAI

HERE = Path(__file__).resolve().parent
FLOW = HERE / "prompt_flow" / "recommender_with_grounding"   # the book's templates and inputs
load_dotenv(HERE / ".env")
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

VARIANTS = {                                  # the two profiles the book compares (9.7)
    "variant_0": FLOW / "recommend.jinja2",              # "You have vast knowledge of everything..."
    "variant_1": FLOW / "recommender_variant_1.jinja2",  # "You are an expert on {{subject}}..."
}
RUBRIC = FLOW / "evaluate_recommendation.jinja2"         # the judge's profile and rubric (9.5)
CRITERIA = ["subject", "format", "genre", "custom"]


# ---------------------------------------------------------------------------
# TODO 24: turn a Prompt Flow chat template into a messages list.
#
# The book's .jinja2 files are Jinja2 templates with Prompt Flow's chat
# layout: a line "system:" followed by the system message, then a line
# "user:" followed by the user message. Fill the template's placeholders
# ({{subject}}, {{format}}, ...) with jinja2's Template(text).render(**inputs),
# then split the result at those two marker lines and return
#   [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
#
# Hint: re.split(r"^(system|user):\s*$", text, flags=re.M) gives
# ["", "system", "<system text>", "user", "<user text>"].
# ---------------------------------------------------------------------------
def render_chat(template_path: Path, **inputs) -> list[dict]:
    text = Template(template_path.read_text(encoding="utf-8")).render(**inputs)
    parts = re.split(r"^(system|user):\s*$", text, flags=re.M)
    return [{"role": role, "content": content.strip()}
            for role, content in zip(parts[1::2], parts[2::2])]


# ---------------------------------------------------------------------------
# TODO 25: ask a profile variant for its recommendations.
#
# Render the variant's template with the request's inputs and send it to the
# LLM. Use temperature=1 and max_tokens=256, as the book's flow does - the
# variants should be compared on their normal, somewhat varied output.
# ---------------------------------------------------------------------------
def recommend(variant: Path, request: dict) -> str:
    response = client.chat.completions.create(
        model=MODEL, temperature=1, max_tokens=256,
        messages=render_chat(variant, **request),
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# TODO 26: the LLM judge - score each recommended item with the rubric.
#
# Render the book's rubric template with the request plus the recommendations,
# and ask for JSON matching SCORES_SCHEMA: one entry per recommended item,
# with a 1-5 score for subject, format and genre - and, added here, "custom":
# does the item respect the request's special instruction ("don't include any
# R rated content")? That's GROUNDING (9.5): checking the answer against what
# was actually asked for.
#
# Why JSON instead of the book's text format? The book's rubric asks for
# scores from 1 to 5 but shows an example with 8 and 10, and its parser
# (parsing_results.py) crashes as soon as a line doesn't look exactly like
# "Key: value". A schema with "minimum": 1, "maximum": 5 makes the model
# return exactly what the code can read (chapter 2's json_output.py).
# Use temperature=0: a judge should be consistent.
# ---------------------------------------------------------------------------
SCORE = {"type": "integer", "minimum": 1, "maximum": 5}
SCORES_SCHEMA = {
    "name": "rubric_scores",
    "schema": {
        "type": "object",
        "properties": {"items": {"type": "array", "items": {
            "type": "object",
            "properties": {"title": {"type": "string"}, **{c: SCORE for c in CRITERIA}},
            "required": ["title", *CRITERIA],
        }}},
        "required": ["items"],
    },
}
JSON_NOTE = ("\n\nIgnore the example output format above. Score every recommended item on "
             "subject, format, genre and custom (how well it follows the special instructions), "
             "each from 1 to 5, and answer only with JSON.")


def judge(request: dict, recommendations: str) -> list[dict]:
    messages = render_chat(RUBRIC, recommendations=recommendations, **request)
    messages[0]["content"] += JSON_NOTE
    response = client.chat.completions.create(
        model=MODEL, temperature=0, messages=messages,
        response_format={"type": "json_schema", "json_schema": SCORES_SCHEMA},
    )
    try:
        return json.loads(response.choices[0].message.content)["items"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []                      # an unreadable verdict counts as no scores


# ---------------------------------------------------------------------------
# TODO 27: run the batch and compare the variants.
#
# For every request and every variant: recommend, judge, and keep each
# item's scores. Then print, per variant, the average of every criterion and
# the overall average - the book's grounding.py (average per item) and
# aggregation.py (totals per variant) in one table. The higher overall
# average wins.
# ---------------------------------------------------------------------------
def main() -> None:
    requests = [json.loads(line) for line in (FLOW / "bulk_recommend.jsonl").read_text().splitlines()
                if line.strip()]
    if "--all" not in sys.argv:
        requests = requests[:4]
    print(f"Model: {MODEL} | {len(requests)} requests x {len(VARIANTS)} variants\n")

    scores = {name: [] for name in VARIANTS}           # variant -> list of item score dicts
    for i, request in enumerate(requests, 1):
        print(f"[{i}/{len(requests)}] {request['format']} about {request['subject']} "
              f"({request['genre']}), '{request['custom']}'")
        for name, template in VARIANTS.items():
            items = judge(request, recommend(template, request))
            scores[name] += items
            titles = ", ".join(item["title"] for item in items) or "(no scores)"
            print(f"   {name}: {titles}")

    print(f"\n{'variant':<11}" + "".join(f"{c:>9}" for c in CRITERIA) + f"{'overall':>9}{'items':>7}")
    for name, items in scores.items():
        if not items:
            print(f"{name:<11}(no scores)")
            continue
        per_criterion = [mean(item[c] for item in items) for c in CRITERIA]
        print(f"{name:<11}" + "".join(f"{v:>9.2f}" for v in per_criterion)
              + f"{mean(per_criterion):>9.2f}{len(items):>7}")


if __name__ == "__main__":
    main()
