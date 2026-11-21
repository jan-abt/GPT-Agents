"""
DIY GPTs - stage 3: actions (function calling).

In chapter 3, ChatGPT's custom actions let a GPT call a web API: you paste
the API's OpenAPI spec into the GPT Builder, and ChatGPT decides when to call
it. Here we do the same with chapter 5's function calling:

    1. describe a function to the LLM as a tool (JSON Schema)     TODO 7
    2. the LLM replies "call get_tasks(...)" - it never runs code itself
    3. our code runs the function, which calls the web API        TODO 8
    4. the results go back to the LLM as "tool" messages           TODO 9
    5. the LLM answers the user, using those results

The web API is the book's chapter_03/daily_tasks_api.py (FastAPI). Start it
before chatting, from the repo root:
    cd chapter_03 && ../.venv/bin/uvicorn daily_tasks_api:app --port 8100
Its interactive docs are at http://localhost:8100/docs
"""
import json
from pathlib import Path

import requests

TASKS_API = "http://localhost:8100"

# GPTs that can use the actions below, by instruction file name.
GPTS_WITH_ACTIONS = {"task_organizer_v1"}


def has_actions(instructions_path: Path) -> bool:
    return instructions_path.stem in GPTS_WITH_ACTIONS


def api_is_up() -> bool:
    """True if the task API answers (used for the status in the sidebar)."""
    try:
        return requests.get(f"{TASKS_API}/tasks", timeout=1).ok
    except requests.RequestException:
        return False


# ---------------------------------------------------------------------------
# TODO 7: describe the get_tasks function to the LLM.
#
# Return a list with one tool, in the same format as `tools` in
# chapter_05/first_function.py:
#   - type "function", name "get_tasks"
#   - a description the LLM can match requests against, e.g.
#     "Get the user's list of daily tasks."
#   - one OPTIONAL parameter "completed" of type "boolean": true for only the
#     finished tasks, false for only the open ones, left out for all tasks.
#     Give it a description too - the LLM reads it to decide the value.
#
# (In ChatGPT this description came from FastAPI's OpenAPI spec; open
# http://localhost:8100/openapi.json to compare.)
# ---------------------------------------------------------------------------
def task_tools() -> list[dict]:
    return [{
        "type": "function",
        "function": {
            "name": "get_tasks",
            "description": "Get the user's list of daily tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "completed": {
                        "type": "boolean",
                        "description": "true for only the finished tasks, false for only "
                                       "the open ones; leave it out to get all tasks.",
                    },
                },
                "required": [],          # completed is optional
            },
        },
    }]


# ---------------------------------------------------------------------------
# TODO 8: the function the LLM can call.
#
# Fetch the tasks from the API (GET {TASKS_API}/tasks, which returns a JSON
# list like [{"id": 1, "description": "Buy groceries", "completed": false}, ...]),
# keep only the ones matching `completed` if it isn't None, and return them as
# a JSON string - the LLM reads text, not Python objects.
#
# Hints: requests.get(url, timeout=5).json(); json.dumps(...)
#
# Careful: never trust the LLM's arguments blindly. Llama 3.2 sends the
# boolean as a STRING ("false" instead of false). Then task["completed"] ==
# completed is never true, every task gets filtered out, and the LLM - given
# an empty list - happily invents tasks. Accept both forms, e.g. by turning
# a string into a bool first: completed = str(completed).lower() == "true"
# ---------------------------------------------------------------------------
def get_tasks(completed: bool | None = None) -> str:
    tasks = requests.get(f"{TASKS_API}/tasks", timeout=5).json()
    if completed is not None:
        completed = str(completed).lower() == "true"   # accepts True as well as "true"
        tasks = [task for task in tasks if task["completed"] == completed]
    return json.dumps(tasks)


# The functions the LLM is allowed to call, by the name it uses for them.
FUNCTIONS = {"get_tasks": get_tasks}


# ---------------------------------------------------------------------------
# TODO 9: run the calls the LLM asked for, and build the replies.
#
# For each call in `tool_calls` (from response.choices[0].message.tool_calls):
#   - look up the function by call.function.name in FUNCTIONS
#   - turn call.function.arguments (a JSON string) into a dict
#   - call the function with those arguments (**kwargs)
#   - make a message {"role": "tool", "tool_call_id": call.id, "content": result}
# Return the list of those messages.
#
# This is step 3-4 of parallel_functions.py in chapter 5.
# ---------------------------------------------------------------------------
def run_tool_calls(tool_calls) -> list[dict]:
    messages = []
    for call in tool_calls:
        function = FUNCTIONS[call.function.name]              # only functions we allow
        args = json.loads(call.function.arguments or "{}")    # '{"completed": false}' -> dict
        result = function(**args)
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return messages
