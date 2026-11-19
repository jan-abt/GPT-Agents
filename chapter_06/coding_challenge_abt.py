"""
Section 6.3.2 without the GPT Assistants Playground: an agentic behavior tree
(ABT) that solves a coding challenge with your local LLM.

Book: chapter 6, section 6.3.2 "Building a coding challenge ABT" (p. 145-149).
The book builds this on OpenAI's Assistants API inside the author's
Playground app. Here it's py_trees (section 6.1) + the plain chat API you
used since chapter 2, so it runs on LM Studio.

The tree (figure 6.8, plus a Retry decorator):

    Retry (up to 3 attempts)                       TODO 16
    └── Sequence: solve the challenge
        ├── Hacker    action     LLM writes a solution      TODO 13
        ├── Judge     action     LLM reviews and fixes it   TODO 14
        └── Verifier  condition  run the challenge's tests  TODO 15

Two changes from the book:
  * the Verifier runs the real tests (pass/fail) instead of asking a third
    LLM whether the code looks right;
  * if the tests fail, the Retry decorator runs the sequence again, and the
    Hacker gets the failed tests as feedback.

The nodes pass data through the py_trees BLACKBOARD (section 6.5), a shared
key/value store, instead of the book's solution.py / judged_solution.py files.

SAFETY: the Verifier runs code the LLM wrote, on your machine. It shows you
the code and asks before running it (in a separate Python process, in a
temporary folder, with a 10-second time limit). Add --yes to skip the
question once you trust it.

Run it from the repo root (uses OPENAI_* from chapter_06/.env):
    .venv/bin/python chapter_06/coding_challenge_abt.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import py_trees
from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ASK_BEFORE_RUNNING = "--yes" not in sys.argv

# ---------------------------------------------------------------------------
# The challenge (listing 6.5) and its tests (listing 6.6), from Edabit.
# (The book's example is missing two commas between the grid rows; fixed here.)
# ---------------------------------------------------------------------------
CHALLENGE = """Plant the Grass

You will be given a matrix representing a field g and two numbers x, y coordinate.
There are three types of possible characters in the matrix:
  x representing a rock.
  o representing a dirt space.
  + representing a grassed space.
You have to simulate grass growing from the position (x, y).
Grass can grow in all four directions (up, left, right, down).
Grass can only grow on dirt spaces and can't go past rocks.
Return the simulated matrix.

Example:
simulate_grass([
  "xxxxxxx",
  "xooooox",
  "xxxxoox",
  "xoooxxx",
  "xxxxxxx"
], 1, 1) -> [
  "xxxxxxx",
  "x+++++x",
  "xxxx++x",
  "xoooxxx",
  "xxxxxxx"
]

Notes: there will always be rocks on the perimeter. x is the row, y is the column.
Write a Python function simulate_grass(g, x, y) that returns the new matrix as a list of strings."""

TESTS = [  # (grid, x, y, expected)
    (["xxxxxxx", "xooooox", "xxxxoox", "xoooxxx", "xxxxxxx"], 1, 1,
     ["xxxxxxx", "x+++++x", "xxxx++x", "xoooxxx", "xxxxxxx"]),
    (["xxxxxxx", "xoxooox", "xxoooox", "xooxxxx", "xoxooox", "xoxooox", "xxxxxxx"], 2, 3,
     ["xxxxxxx", "xox+++x", "xx++++x", "x++xxxx", "x+xooox", "x+xooox", "xxxxxxx"]),
    (["xxxxxx", "xoxoox", "xxooox", "xoooox", "xoooox", "xxxxxx"], 1, 1,
     ["xxxxxx", "x+xoox", "xxooox", "xoooox", "xoooox", "xxxxxx"]),
    (["xxxxx", "xooox", "xooox", "xooox", "xxxxx"], 1, 1,
     ["xxxxx", "x+++x", "x+++x", "x+++x", "xxxxx"]),
    (["xxxxxx", "xxxxox", "xxooox", "xoooxx", "xooxxx", "xooxxx", "xxooox", "xxxoxx", "xxxxxx"], 4, 1,
     ["xxxxxx", "xxxx+x", "xx+++x", "x+++xx", "x++xxx", "x++xxx", "xx+++x", "xxx+xx", "xxxxxx"]),
    (["xxxxxxxxxxx", "xoxooooooox", "xoxoxxxxxox", "xoxoxoooxox", "xoxoxoxoxox", "xoxoxoxoxox",
      "xoxoxxxoxox", "xoxoooooxox", "xoxxxxxxxox", "xooooooooox", "xxxxxxxxxxx"], 1, 1,
     ["xxxxxxxxxxx", "x+x+++++++x", "x+x+xxxxx+x", "x+x+x+++x+x", "x+x+x+x+x+x", "x+x+x+x+x+x",
      "x+x+xxx+x+x", "x+x+++++x+x", "x+xxxxxxx+x", "x+++++++++x", "xxxxxxxxxxx"]),
]


def ask_llm(system: str, user: str) -> str:
    """One chat request - the same call as chapter 2's connecting.py."""
    response = client.chat.completions.create(
        model=MODEL, temperature=0.3,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return response.choices[0].message.content or ""


def extract_code(reply: str) -> str | None:
    """The longest ```python block in an LLM reply, or None if there is none."""
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", reply, re.S)
    return max(blocks, key=len).strip() if blocks else None


# ---------------------------------------------------------------------------
# TODO 13: the Hacker - an ACTION node that asks the LLM for a solution.
#
# In update():
#   - build a prompt from the challenge (self.bb.challenge) and, if a previous
#     attempt failed, the test report (self.bb.feedback), so the LLM can learn
#     from its mistakes
#   - ask the LLM with HACKER_ROLE as the system message
#   - pull the code out of the reply with extract_code()
#   - store it on the blackboard (self.bb.solution) and return SUCCESS;
#     return FAILURE if the reply contained no code block
#
# The blackboard keys a node uses are registered in __init__, with READ or
# WRITE access, so py_trees can check who may change what.
# ---------------------------------------------------------------------------
HACKER_ROLE = (
    "You are the Hacker, an expert Python programmer. Solve the coding challenge. "
    "Reply with only the complete solution in one ```python code block. Define the function "
    "exactly as the challenge names it. No example usage, no tests, no input(), no print()."
)


class Hacker(py_trees.behaviour.Behaviour):
    def __init__(self, name: str = "Hacker"):
        super().__init__(name)
        self.bb = self.attach_blackboard_client(name=name)
        self.bb.register_key("challenge", access=py_trees.common.Access.READ)
        self.bb.register_key("feedback", access=py_trees.common.Access.READ)
        self.bb.register_key("solution", access=py_trees.common.Access.WRITE)

    def update(self) -> py_trees.common.Status:
        prompt = self.bb.challenge
        if self.bb.feedback:
            prompt += ("\n\nYour previous solution failed these tests - fix it:\n"
                       + self.bb.feedback)
        print(f"\n[{self.name}] asking {MODEL} for a solution...")
        code = extract_code(ask_llm(HACKER_ROLE, prompt))
        if code is None:
            print(f"[{self.name}] the reply contained no code block")
            return py_trees.common.Status.FAILURE
        self.bb.solution = code
        print(f"[{self.name}] wrote {code.count(chr(10)) + 1} lines")
        return py_trees.common.Status.SUCCESS


# ---------------------------------------------------------------------------
# TODO 14: the Judge - an ACTION node that reviews and improves the solution.
#
# Same pattern as the Hacker, with a different role: give the LLM the challenge
# AND the Hacker's code (self.bb.solution), ask it to check the code against
# the challenge's example and fix any bugs, and store the code from its reply
# as self.bb.judged. Print the review part of the reply (the text before the
# code block), so you can see what the Judge found.
#
# This is the "critic" idea from chapter 4 (autogen_coding_critic.py), now as
# a fixed step in a tree instead of a nested chat.
# ---------------------------------------------------------------------------
JUDGE_ROLE = (
    "You are the Judge, a strict reviewer of coding-challenge solutions. Check the solution "
    "against the challenge and its example, step by step. Reply with a short review (at most "
    "3 bullet points), then the complete corrected solution in one ```python code block. If the "
    "solution is already correct, return it unchanged. No example usage, no tests, no print()."
)


class Judge(py_trees.behaviour.Behaviour):
    def __init__(self, name: str = "Judge"):
        super().__init__(name)
        self.bb = self.attach_blackboard_client(name=name)
        self.bb.register_key("challenge", access=py_trees.common.Access.READ)
        self.bb.register_key("solution", access=py_trees.common.Access.READ)
        self.bb.register_key("judged", access=py_trees.common.Access.WRITE)

    def update(self) -> py_trees.common.Status:
        print(f"\n[{self.name}] reviewing the solution...")
        reply = ask_llm(JUDGE_ROLE, f"Challenge:\n{self.bb.challenge}\n\n"
                                    f"Solution:\n```python\n{self.bb.solution}\n```")
        code = extract_code(reply)
        if code is None:
            print(f"[{self.name}] the reply contained no code block")
            return py_trees.common.Status.FAILURE
        review = reply.split("```")[0].strip()
        print(f"[{self.name}] review:\n{review or '(no comments)'}")
        self.bb.judged = code
        return py_trees.common.Status.SUCCESS


# ---------------------------------------------------------------------------
# TODO 15: the Verifier - a CONDITION node that runs the tests.
#
# Condition nodes don't change the world; they answer yes/no as SUCCESS or
# FAILURE. Here: "does the judged solution pass all tests?"
#   - show the code and, unless --yes was given, ask before running it
#   - write the code plus a small test script into a temporary folder and run
#     it with a separate Python process (subprocess.run, with a timeout), so a
#     bad solution can't hang or crash this program
#   - SUCCESS if every test passes; otherwise store a short report of the
#     failed tests in self.bb.feedback (the Hacker reads it on the next try)
#     and return FAILURE
#
# The book asks a third LLM (the Verifier assistant) whether the code is
# right. Running real tests is objective: the code either works or it doesn't.
# ---------------------------------------------------------------------------
TEST_RUNNER = """
import json, sys
from solution import simulate_grass
failures = []
for i, (grid, x, y, expected) in enumerate(json.load(open("tests.json")), 1):
    try:
        got = simulate_grass(list(grid), x, y)
    except Exception as e:
        got = f"{type(e).__name__}: {e}"
    if got != expected:
        failures.append(f"Test {i}: simulate_grass({grid}, {x}, {y})\\n  expected {expected}\\n  got      {got}")
print(json.dumps(failures))
"""


class Verifier(py_trees.behaviour.Behaviour):
    def __init__(self, name: str = "Verifier"):
        super().__init__(name)
        self.bb = self.attach_blackboard_client(name=name)
        self.bb.register_key("judged", access=py_trees.common.Access.READ)
        self.bb.register_key("feedback", access=py_trees.common.Access.WRITE)

    def update(self) -> py_trees.common.Status:
        code = self.bb.judged
        print(f"\n[{self.name}] the code to test:\n{'-' * 60}\n{code}\n{'-' * 60}")
        if ASK_BEFORE_RUNNING and input("Run the tests on this code? [y/N] ").strip().lower() != "y":
            print(f"[{self.name}] not run - counts as a failure")
            self.bb.feedback = "The code was not tested."
            return py_trees.common.Status.FAILURE

        with tempfile.TemporaryDirectory() as folder:
            Path(folder, "solution.py").write_text(code, encoding="utf-8")
            Path(folder, "tests.json").write_text(json.dumps(TESTS), encoding="utf-8")
            Path(folder, "run_tests.py").write_text(TEST_RUNNER, encoding="utf-8")
            try:
                result = subprocess.run([sys.executable, "run_tests.py"], cwd=folder,
                                        capture_output=True, text=True, timeout=10)
            except subprocess.TimeoutExpired:
                self.bb.feedback = "The code took longer than 10 seconds (endless loop?)."
                print(f"[{self.name}] ✗ timeout")
                return py_trees.common.Status.FAILURE

        if result.returncode != 0:  # the code didn't even load (syntax error, wrong name...)
            self.bb.feedback = result.stderr.strip().splitlines()[-1] if result.stderr else "The code crashed."
            print(f"[{self.name}] ✗ the code crashed: {self.bb.feedback}")
            return py_trees.common.Status.FAILURE

        failures = json.loads(result.stdout.strip().splitlines()[-1])
        print(f"[{self.name}] {len(TESTS) - len(failures)}/{len(TESTS)} tests passed")
        if failures:
            self.bb.feedback = "\n".join(failures[:2])   # two examples are enough feedback
            return py_trees.common.Status.FAILURE
        return py_trees.common.Status.SUCCESS


# ---------------------------------------------------------------------------
# TODO 16: build the tree and tick it until it finishes.
#
#   - a Sequence (memory=True) with the Hacker, the Judge and the Verifier
#   - wrapped in a Retry decorator (py_trees.decorators.Retry) allowing 3
#     failures - when its child fails, Retry answers RUNNING instead of
#     FAILURE, so the next tick runs the sequence again
#   - put the challenge on the blackboard, and an empty feedback
#   - tick until the root's status is SUCCESS or FAILURE, printing the tree
#     with py_trees.display.unicode_tree(root, show_status=True) after each
#     tick
# ---------------------------------------------------------------------------
def main() -> None:
    solve = py_trees.composites.Sequence(name="Solve the challenge", memory=True)
    solve.add_children([Hacker(), Judge(), Verifier()])
    root = py_trees.decorators.Retry(name="Retry (3 attempts)", child=solve, num_failures=3)

    setup = py_trees.blackboard.Client(name="Setup")
    setup.register_key("challenge", access=py_trees.common.Access.WRITE)
    setup.register_key("feedback", access=py_trees.common.Access.WRITE)
    setup.challenge = CHALLENGE
    setup.feedback = ""

    tree = py_trees.trees.BehaviourTree(root)
    print(f"Model: {MODEL}\n\n{py_trees.display.unicode_tree(root)}")
    tick = 0
    while root.status not in (py_trees.common.Status.SUCCESS, py_trees.common.Status.FAILURE):
        tick += 1
        print(f"\n{'=' * 25} Tick {tick} {'=' * 25}")
        tree.tick()
        print("\n" + py_trees.display.unicode_tree(root, show_status=True))

    print("\nResult:", "✓ solved" if root.status == py_trees.common.Status.SUCCESS
          else "✗ not solved after 3 attempts")


if __name__ == "__main__":
    main()
