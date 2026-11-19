"""
Chapter 11 without Nexus: a sequential planner with feedback, on a local LLM.

Book: chapter 11, section 11.3 "Building a sequential planner" (p. 278-285)
and the feedback ideas of 11.5 (p. 288-295). The book's planner
(basic_nexus_planner.py) lives inside Nexus; this is the same design in
plain Python:

    goal ──▶ PLANNER (one LLM call) ──▶ JSON plan: a list of steps, each
             calling one of the AVAILABLE FUNCTIONS                   TODO 34
    plan ──▶ EXECUTOR (code, no LLM) runs the steps in order, feeding
             each step's output into later steps                      TODO 35, 36
    error ──▶ FEEDBACK: the error goes back to the planner, which
             writes a corrected plan (up to 3 attempts)               TODO 37

The available functions (TODO 33) reuse what you built earlier:
  search_calculus_book  embedding search from chapter 8 (DIY GPTs knowledge.py)
  summarize             a semantic function (chapter 5): a prompt run by the LLM
  save_file             a native function (chapter 5), writing into chapter_11/output/
  get_tasks             the task API from DIY GPTs stage 3 (only if it's running)

Why plan first? Calling tools one at a time, an LLM easily loses track of a
multi-step goal (11.1). Writing the whole plan up front, then letting code
execute it, keeps the steps in order and the LLM out of the bookkeeping.

Run it from the repo root (uses OPENAI_* and EMBEDDING_MODEL from chapter_11/.env):
    .venv/bin/python chapter_11/planner.py                    # the default goal
    .venv/bin/python chapter_11/planner.py "your own goal"
"""
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "chapter_03" / "diy_gpts"))   # reuse DIY GPTs' modules
import actions     # noqa: E402  (DIY GPTs stage 3: the task API)
import knowledge   # noqa: E402  (DIY GPTs stage 2 + chapter 8: embedding search)

load_dotenv(HERE / ".env")
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OUTPUT_DIR = HERE / "output"                                       # gitignored
BOOK = HERE.parent / "chapter_03" / "calculus_made_easy.pdf"

DEFAULT_GOAL = ("Find what the book Calculus Made Easy says about the meaning of the letter d "
                "in dx, and what it says about integration as summing up. Summarize each in two "
                "sentences, and save both summaries together in a file called calculus_notes.txt.")


# ---------------------------------------------------------------------------
# TODO 33: the AVAILABLE FUNCTIONS - real code the plan can call.
#
# Each entry has the function itself, a description, and its arguments with
# a description each. The planner only ever sees describe_functions(), the
# text version - exactly like the book's [AVAILABLE FUNCTIONS] section, and
# like the tool descriptions of chapter 5 (the LLM never sees the code).
# Any argument may receive a list (from an earlier step); join lists into one
# text where a function needs text.
# ---------------------------------------------------------------------------
def as_text(value) -> str:
    return "\n\n".join(map(str, value)) if isinstance(value, list) else str(value)


def search_calculus_book(query) -> str:
    chunks = knowledge.split_into_chunks(knowledge.load_text(BOOK))
    vectors = knowledge.load_vectors(client, BOOK, chunks)
    return "\n\n".join(knowledge.semantic_search(client, chunks, vectors, as_text(query), k=2))


def summarize(text) -> str:
    response = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": "Summarize the text in at most two sentences. "
                                                "Use only what the text says."},
                  {"role": "user", "content": as_text(text)}])
    return response.choices[0].message.content or ""


def save_file(filename, text) -> str:
    name = Path(as_text(filename)).name or "output.txt"   # a bare name: never outside output/
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / name).write_text(as_text(text), encoding="utf-8")
    return f"saved {len(as_text(text))} characters to chapter_11/output/{name}"


def get_tasks(completed="") -> str:
    if not actions.api_is_up():
        raise RuntimeError("the task API is not running (start it on port 8100)")
    return actions.get_tasks(None if completed in ("", None) else completed)


FUNCTIONS = {
    "search_calculus_book": {"fn": search_calculus_book,
                             "description": "search the book Calculus Made Easy by meaning; returns the two best-matching passages",
                             "args": {"query": "what to look for, in plain words"}},
    "summarize": {"fn": summarize,
                  "description": "summarize a text in at most two sentences",
                  "args": {"text": "the text to summarize"}},
    "save_file": {"fn": save_file,
                  "description": "save a text to a file",
                  "args": {"filename": "a plain file name such as notes.txt", "text": "the text to save"}},
    "get_tasks": {"fn": get_tasks,
                  "description": "get the user's daily tasks as JSON",
                  "args": {"completed": "'true' for finished tasks, 'false' for open ones, '' for all"}},
}


def describe_functions() -> str:
    lines = []
    for name, f in FUNCTIONS.items():
        lines.append(f"{name}\n  description: {f['description']}\n  args:")
        lines += [f"  - {arg}: {desc}" for arg, desc in f["args"].items()]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TODO 34: the PLANNER - one LLM call that turns a goal into a JSON plan.
#
# The prompt follows the book's listing 11.3: the planner's job, the rules,
# the special for-each function, one worked example, the available
# functions, the goal - and any feedback from failed earlier plans.
# Answer with JSON matching PLAN_SCHEMA (chapter 2's json_schema technique):
# every argument is a string or a list of strings, so the executor can always
# read the plan. Our references are "{s1}" - the book uses "output_<Function>",
# which breaks when the same function is used twice.
# ---------------------------------------------------------------------------
PLANNER_PROMPT = """You are a planner. Your job is to create a properly formatted JSON plan, step by step, that satisfies the goal.
Create a list of subtasks. Each subtask calls one function from the [AVAILABLE FUNCTIONS] list - never any other function.
Base your choice on the functions' names and descriptions, and give each function the arguments it needs.
Number the steps "s1", "s2", ... To use the output of an earlier step as an argument, write its id in braces, e.g. "text": "{{s1}}". You can also combine outputs: "text": ["{{s2}}", "{{s3}}"].
The plan should be as short as possible.

[SPECIAL FUNCTIONS]
for-each
  description: run a function once for each item of a list; its output is the list of results
  args:
  - list: a list of items, or "{{sN}}" for a step whose output is a list
  - function: the function to run for each item
  - arg: the name of that function's argument that receives the item

[EXAMPLE]
Available functions: GetJokeTopics (no args), Joke (args: topic), EmailTo (args: text, recipient)
Goal: "Get a list of joke topics and generate a different joke for each topic. Email the jokes to a friend."
Plan: {{"subtasks": [
  {{"id": "s1", "function": "GetJokeTopics", "args": {{}}}},
  {{"id": "s2", "function": "for-each", "args": {{"list": "{{s1}}", "function": "Joke", "arg": "topic"}}}},
  {{"id": "s3", "function": "EmailTo", "args": {{"text": "{{s2}}", "recipient": "friend"}}}}]}}

[AVAILABLE FUNCTIONS]
{functions}
{feedback}"""

VALUE = {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]}
PLAN_SCHEMA = {
    "name": "plan",
    "schema": {
        "type": "object",
        "properties": {"subtasks": {"type": "array", "items": {
            "type": "object",
            "properties": {"id": {"type": "string"}, "function": {"type": "string"},
                           "args": {"type": "object", "additionalProperties": VALUE}},
            "required": ["id", "function", "args"],
        }}},
        "required": ["subtasks"],
    },
}


def create_plan(goal: str, feedback: list[str]) -> list[dict]:
    notes = ("\n[FEEDBACK FROM EARLIER PLANS - fix these problems]\n" + "\n".join(f"- {f}" for f in feedback)
             if feedback else "")
    response = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": PLANNER_PROMPT.format(functions=describe_functions(),
                                                                       feedback=notes)},
                  {"role": "user", "content": f"[GOAL]\n{goal}"}],
        response_format={"type": "json_schema", "json_schema": PLAN_SCHEMA},
    )
    return json.loads(response.choices[0].message.content)["subtasks"]


# ---------------------------------------------------------------------------
# TODO 35: fill in references to earlier outputs.
#
# An argument "{s1}" (alone) becomes step s1's output itself - which may be a
# list (for-each results). Inside a longer text, "Notes: {s1}" gets the
# output pasted in as text. Lists of arguments are resolved item by item.
# A reference to a step that doesn't exist (yet) is an error the planner
# must hear about.
# ---------------------------------------------------------------------------
REF = re.compile(r"\{(s\d+)\}")


def resolve(value, outputs: dict):
    if isinstance(value, list):
        return [resolve(v, outputs) for v in value]
    for ref in REF.findall(value):
        if ref not in outputs:
            raise ValueError(f"{value!r} refers to step {ref}, which hasn't run yet")
    whole = REF.fullmatch(value)
    if whole:
        return outputs[whole.group(1)]
    return REF.sub(lambda m: as_text(outputs[m.group(1)]), value)


# ---------------------------------------------------------------------------
# TODO 36: the EXECUTOR - run the plan, step by step, with code.
#
# For each subtask: resolve its arguments, then either run "for-each" (call
# the named function once per list item, passing the item as `arg`) or look
# the function up in FUNCTIONS and call it. Keep every output under the
# step's id. Raise an error with a clear message for an unknown function or
# a wrong argument - the message becomes the planner's feedback.
# Note: no LLM decides anything here. The plan is followed exactly.
# ---------------------------------------------------------------------------
def call(name: str, args: dict):
    if name not in FUNCTIONS:
        raise ValueError(f"unknown function {name!r}; available: {', '.join(FUNCTIONS)}")
    allowed = FUNCTIONS[name]["args"]
    wrong = [a for a in args if a not in allowed]
    if wrong:
        raise ValueError(f"{name} has no argument(s) {wrong}; its arguments are {list(allowed)}")
    return FUNCTIONS[name]["fn"](**args)


def execute_plan(plan: list[dict]) -> dict:
    outputs = {}
    for step in plan:
        args = {k: resolve(v, outputs) for k, v in step["args"].items()}
        print(f"   {step['id']}: {step['function']}({json.dumps(step['args'])[:110]})", flush=True)
        try:
            if step["function"] == "for-each":
                items = args["list"] if isinstance(args.get("list"), list) else [args.get("list")]
                result = [call(args["function"], {args["arg"]: item}) for item in items]
            else:
                result = call(step["function"], args)
        except KeyError as e:
            raise ValueError(f"step {step['id']} ({step['function']}) is missing the argument {e}") from None
        except Exception as e:
            raise ValueError(f"step {step['id']} ({step['function']}) failed: {e}") from None
        outputs[step["id"]] = result
        print(f"       -> {as_text(result)[:150].replace(chr(10), ' ')}", flush=True)
    return outputs


# ---------------------------------------------------------------------------
# TODO 37: plan, execute, and use FEEDBACK when something goes wrong (11.5).
#
# Up to 3 attempts: make a plan (passing the feedback collected so far),
# execute it, and stop on success. On an error, add its message to the
# feedback list and plan again - the planner now knows what went wrong.
# After success, one last LLM call writes a short answer for the user from
# the step outputs (the book's Nexus passes them to the agent the same way).
# ---------------------------------------------------------------------------
def main() -> None:
    goal = " ".join(a for a in sys.argv[1:]) or DEFAULT_GOAL
    print(f"Model: {MODEL}\nGoal: {goal}\n")
    feedback: list[str] = []
    for attempt in range(1, 4):
        plan = create_plan(goal, feedback)
        print(f"Plan, attempt {attempt}: {len(plan)} steps")
        try:
            outputs = execute_plan(plan)
            break
        except ValueError as e:
            print(f"   ✗ {e}\n")
            feedback.append(str(e))
    else:
        print("✗ no working plan after 3 attempts")
        return

    results = "\n\n".join(f"[{step}] {as_text(out)}" for step, out in outputs.items())
    answer = client.chat.completions.create(
        model=MODEL, temperature=0,
        messages=[{"role": "system", "content": "Report to the user, in a few sentences, what was "
                                                "done for their goal, using only these step results."},
                  {"role": "user", "content": f"Goal: {goal}\n\nStep results:\n{results}"}],
    ).choices[0].message.content
    print(f"\n✓ Done.\n{answer}")


if __name__ == "__main__":
    main()
