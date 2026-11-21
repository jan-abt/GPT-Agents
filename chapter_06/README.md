# Chapter 6: Building autonomous assistants (p. 129–159)

**In one sentence:** a behavior tree gives an agent a fixed, readable
structure (steps, fallbacks, retries), and its nodes can be LLM calls: an
*agentic* behavior tree.

## Key ideas

- **Behavior trees (6.1, p. 130).** From game AI and robotics. Every node
  returns SUCCESS, FAILURE or RUNNING; one *tick* walks the tree from the root,
  top to bottom, left to right.

  | Node | Rule |
  |---|---|
  | Sequence `{-}` | children in order; fails at the first failure (an AND) |
  | Selector / Fallback `{o}` | tries children until one succeeds (an OR: plan A, else plan B) |
  | Condition | a yes/no check |
  | Action | does something |
  | Decorator | wraps one child: retry, invert, time limit |

- **Why trees (6.1.2, p. 132):** more modular and scalable than state
  machines or decision trees.
- **Agentic behavior trees (6.3, p. 143):** nodes are LLM roles. The book's
  coding challenge (6.3.2, p. 145): **Hacker** writes a solution, **Judge**
  reviews it, **Verifier** checks it.
- **Silos vs. conversation (6.3.3, 6.4):** agents can pass files or results
  instead of chatting: less noise than chapter 4's group chat, less emergent
  behaviour.
- **Back chaining (6.5, p. 155):** design a tree backwards from the goal; the
  **blackboard** is a shared key/value store nodes use to pass data.

## Walkthrough

1. **`first_btree.py`** (6.1.3):
   ```bash
   python chapter_06/first_btree.py
   ```
   Selector → (has apple → eat apple) or (has pear → eat pear). It eats the
   apple every tick, because the selector stops at the first success. Change
   `HasApple` to `if False:` and the selector falls back to the pear.
2. **`coding_challenge_abt.py`** (6.3.2, rebuilt for local models):
   ```bash
   python chapter_06/coding_challenge_abt.py
   ```
   ```
   -^- Retry (3 attempts)                TODO 16
       {-} Solve the challenge
           --> Hacker    (action)        TODO 13: LLM writes simulate_grass()
           --> Judge     (action)        TODO 14: LLM reviews and fixes it
           --> Verifier  (condition)     TODO 15: runs the book's 6 tests
   ```
   The puzzle ("Plant the Grass") is a flood fill: `x` rock, `o` dirt, `+`
   grass; grow from `(x, y)` = (row, column) up/down/left/right through dirt.
   The **Verifier shows the code and asks before running it** (separate
   process, temporary folder, 10-second limit). Watch the tree printout after
   each tick, and the blackboard keys (`solution`, `judged`, `feedback`).

## What we found
- Qwen solved it **6/6 on the first attempt** (a recursive DFS).
- In a test run, the Judge praised code that would have looped forever and
  missed the start cell. **Real tests beat an LLM reviewer**, which is why our
  Verifier runs tests instead of asking a third LLM, as the book does.
- The accepted solution still modified its input list; tests only check what
  they test.

## What isn't runnable
Sections 6.2–6.5 run in the author's **GPT Assistants Playground**, built on
OpenAI's Assistants API (OpenAI-only and paid; OpenAI announced its retirement
for 2026). The YouTube → X example (6.3.4) also needs an X account.

## Setup notes
`pip install py_trees` (under 1 MB). `chapter_06/.env` (gitignored)
sets the model; `qwen2.5-7b-instruct` works well. `--yes` skips the Verifier's
question.
