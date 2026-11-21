"""
Chapter 10 without Prompt Flow: does the way you prompt change how well an
LLM reasons? Five techniques from the chapter, tested on the same word
problems, with answers checked by CODE against known solutions.

Book: chapter 10, "Agent reasoning and evaluation" (p. 244-271)
  10.1 Direct solution prompting (zero-shot, few-shot)        -> "direct"
  10.2.1 Chain of thought (a worked example first)            -> "few-shot CoT"
  10.2.2 Zero-shot CoT ("Let's think step by step")           -> "zero-shot CoT"
  10.2.3 Prompt chaining (decompose -> calculate -> solve)    -> "chaining"
  10.3.1 Self-consistency (several CoT answers, majority)     -> "self-consistency"
  (10.3.2 Tree of thoughts is explained in the README, not run: too slow on a CPU.)

Why not the book's problems? Its time-travel puzzles come without expected
answers (an LLM judges whether two answers "match"), and its own worked
example subtracts a day it shouldn't (see PROBLEMS[2]). These problems are in
the same style, with answers worked out by hand - so a wrong answer is
simply wrong, no judge needed (chapter 9's lesson).

Run it from the repo root (uses OPENAI_* from chapter_10/.env):
    .venv/bin/python chapter_10/reasoning_techniques.py           # all 4 problems (~25 min on a CPU)
    .venv/bin/python chapter_10/reasoning_techniques.py --quick   # first 2 problems
"""
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
SELF_CONSISTENCY_RUNS = 3

PROBLEMS = [  # (question, correct answer) - each answer worked out by hand
    ("A time traveler leaves the year 2150 and jumps back 75 years. She lives there for 12 years, "
     "then jumps forward 30 years. What year is it after the forward jump?", 2117),
    # 2150 - 75 = 2075; + 12 years lived = 2087; + 30 = 2117
    ("Leo is 30 years old when he travels from the year 2100 back to 1950. He lives in 1950 for "
     "8 years, then jumps forward 100 years. Time travel itself takes no time and does not change "
     "his age. How old is Leo after the forward jump?", 38),
    # only the 8 years he actually lives count: 30 + 8 = 38 (the jumps add nothing)
    ("Sarah travels back in time to stop an event. She meant to arrive 2 days early, but she "
     "actually arrives exactly 730 days before the event. She spends her first day in the past "
     "preparing, then waits until the event happens. How many days pass between her arrival in "
     "the past and the day of the event?", 730),
    # the preparation day is one of the 730 days - the book's worked example subtracts it (729)
    ("Max's time machine only jumps in steps of exactly 40 years. Starting in the year 2300, he "
     "makes 10 jumps backward, then 3 jumps forward, then 2 more jumps backward. In which year "
     "does he end up?", 1940),
    # net 10 - 3 + 2 = 9 jumps back; 2300 - 9 * 40 = 1940
]

ANSWER_RULE = "End your reply with a final line in exactly this form: ANSWER: <number>"


# ---------------------------------------------------------------------------
# TODO 28: one LLM call, and reading the number out of its reply.
#
# ask(): a system + user message, returns the reply text. Count every call
# in CALLS, so the results table can show what each technique costs.
#
# extract_answer(): take the number after the LAST "ANSWER:" in the reply;
# if there is none, fall back to the last number in the text. Return None
# if there's no number at all. Reasoning replies contain many numbers along
# the way, so taking just the first one would usually be wrong.
# ---------------------------------------------------------------------------
CALLS = Counter()


def ask(technique: str, system: str, user: str, temperature: float = 0) -> str:
    CALLS[technique] += 1
    response = client.chat.completions.create(
        model=MODEL, temperature=temperature,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
    )
    return response.choices[0].message.content or ""


def extract_answer(reply: str) -> int | None:
    tagged = re.findall(r"ANSWER:\s*\**\s*(-?\d[\d,]*)", reply)
    numbers = tagged or re.findall(r"-?\d[\d,]*", reply)
    return int(numbers[-1].replace(",", "")) if numbers else None


# ---------------------------------------------------------------------------
# TODO 29: three single-call techniques - only the prompt differs.
#
#   direct:         ask for the answer only, no explanation (10.1)
#   zero-shot CoT:  add "Let's think step by step." (10.2.2, the book's
#                   zero-shot-cot-prompting/cot.jinja2)
#   few-shot CoT:   show one fully worked example first (10.2.1, the book's
#                   chain-of-thought-prompting/cot.jinja2). Our example is a
#                   new one: the book's Sarah example teaches the 729 mistake.
# Each returns the extracted number.
# ---------------------------------------------------------------------------
WORKED_EXAMPLE = """Problem: Tom leaves the year 2200 and jumps back 50 years. He lives there for 5 years, then jumps forward 20 years. What year is it after the forward jump?

Chain of thought:
1. Start: 2200.
2. Jump back 50 years: 2200 - 50 = 2150.
3. He lives there 5 years, so time moves on: 2150 + 5 = 2155.
4. Jump forward 20 years: 2155 + 20 = 2175.
5. Conclusion: it is 2175.
ANSWER: 2175"""


def direct(problem: str) -> int | None:
    reply = ask("direct", "Solve the problem. Reply with the final number only, no explanation. "
                + ANSWER_RULE, problem)
    return extract_answer(reply)


def zero_shot_cot(problem: str) -> int | None:
    reply = ask("zero-shot CoT", "You are an expert in solving time travel problems. You are given "
                "a time travel problem and you have to solve it. Let's think step by step. "
                + ANSWER_RULE, problem)
    return extract_answer(reply)


def few_shot_cot(problem: str) -> int | None:
    reply = ask("few-shot CoT", "Solve time travel problems by reasoning step by step, like in this "
                f"example:\n\n{WORKED_EXAMPLE}\n\n{ANSWER_RULE}", problem)
    return extract_answer(reply)


# ---------------------------------------------------------------------------
# TODO 30: prompt chaining - three LLM calls, each feeding the next (10.2.3).
#
# The book's prompt-chaining flow: decompose_steps.jinja2 (list the steps,
# don't solve), calculate_steps.jinja2 (work out each step), and
# calculate_solution.jinja2 (combine into the final answer). The output of
# each call goes into the next call's user message.
# ---------------------------------------------------------------------------
def chaining(problem: str) -> int | None:
    steps = ask("chaining", "You are a problem solving AI assistant. Your job is to break the user's "
                "problem down into smaller steps and list the steps in the order you would solve "
                "them. Think step by step, not in generalities. Do not attempt to solve the "
                "problem, just list the steps.", problem)
    calculated = ask("chaining", "You are a problem solving AI assistant. You will be given a list "
                     "of steps that solve a problem. Your job is to calculate the output for each "
                     "of the steps in order. Do not attempt to solve the whole problem, just list "
                     "the output for each of the steps. Think step by step.",
                     f"{problem}\n\nSteps:\n{steps}")
    final = ask("chaining", "You are a problem solving AI assistant. You will be given a list of "
                "steps and the calculated output for each step. Use them to determine the final "
                "solution to the problem. " + ANSWER_RULE,
                f"{problem}\n\nSteps:\n{steps}\n\nCalculated:\n{calculated}")
    return extract_answer(final)


# ---------------------------------------------------------------------------
# TODO 31: self-consistency - ask several times, take the majority (10.3.1).
#
# Run the zero-shot CoT prompt SELF_CONSISTENCY_RUNS times with
# temperature=1, so the reasoning chains differ, extract each answer, and
# return the most common one (collections.Counter(...).most_common(1)).
# One chain of thought can slip; several rarely slip the same way.
# Return the votes too, so you can see how much the runs agreed.
# ---------------------------------------------------------------------------
def self_consistency(problem: str) -> tuple[int | None, list]:
    votes = []
    for _ in range(SELF_CONSISTENCY_RUNS):
        reply = ask("self-consistency", "You are an expert in solving time travel problems. Let's "
                    "think step by step. " + ANSWER_RULE, problem, temperature=1)
        votes.append(extract_answer(reply))
    counted = Counter(v for v in votes if v is not None)
    return (counted.most_common(1)[0][0] if counted else None), votes


# ---------------------------------------------------------------------------
# TODO 32: run every technique on every problem and print the scoreboard.
#
# Compare each answer with the known solution (plain ==, no LLM judge), and
# for each technique report: problems solved, LLM calls used, and the time
# it took.
# ---------------------------------------------------------------------------
TECHNIQUES = {"direct": direct, "zero-shot CoT": zero_shot_cot, "few-shot CoT": few_shot_cot,
              "chaining": chaining, "self-consistency": self_consistency}


def main() -> None:
    problems = PROBLEMS[:2] if "--quick" in sys.argv else PROBLEMS
    print(f"Model: {MODEL} | {len(problems)} problems x {len(TECHNIQUES)} techniques\n")
    solved, seconds = Counter(), Counter()
    for i, (problem, correct) in enumerate(problems, 1):
        print(f"Problem {i} (correct answer: {correct}): {problem[:70]}...")
        for name, technique in TECHNIQUES.items():
            start = time.time()
            result = technique(problem)
            seconds[name] += time.time() - start
            answer, extra = result if isinstance(result, tuple) else (result, None)
            ok = answer == correct
            solved[name] += ok
            votes = f"  votes {extra}" if extra is not None else ""
            print(f"   {'✓' if ok else '✗'} {name:<17} {answer}{votes}", flush=True)

    print(f"\n{'technique':<18}{'solved':>8}{'LLM calls':>11}{'seconds':>9}")
    for name in TECHNIQUES:
        print(f"{name:<18}{solved[name]:>5}/{len(problems)}{CALLS[name]:>11}{seconds[name]:>9.0f}")


if __name__ == "__main__":
    main()
