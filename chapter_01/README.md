# Chapter 1: Introduction to agents and their world (p. 1–15)

**In one sentence:** an agent is an LLM that acts on your behalf, built from a
few components that the rest of the book adds one by one.

There is no code for this chapter. Read it as the map for chapters 2–11.

## Key ideas

**1.1 What an agent is (p. 1).** A spectrum, from a plain chat (you ask, the
LLM answers) to an autonomous agent (you give a goal; it plans, uses tools and
checks its own work).

**1.2 The component systems of an agent (p. 4).** Every later chapter adds
one of these. Where to find each in this repo:

| Component | What it does | Where we built it |
|---|---|---|
| Profile / persona | who the agent is and how it behaves | ch 2 personas; ch 3 instruction files (`chapter_03/*_v1.txt`) |
| Actions / tools | what it can *do* | ch 5 function calling; DIY GPTs stage 3 (`actions.py`) |
| Knowledge | reference material it can look up | DIY GPTs stage 2 (`knowledge.py`); ch 8 embeddings |
| Memory | what it learns and keeps while working | DIY GPTs stage 4 (`memory.py`) |
| Reasoning and evaluation | thinking step by step, checking answers | ch 10 (`reasoning_techniques.py`); ch 9 judge |
| Planning and feedback | breaking a goal into steps, recovering from errors | ch 11 (`planner.py`); ch 6 retry tree |

**1.3 Why now (p. 9).** LLMs became good enough to drive these components.

**1.4 The AI interface (p. 11).** A natural-language layer in front of
existing services, so people (and other agents) can use them by asking.
Chapter 5's semantic service layer and our Task Organizer are examples.

**1.5 The agent landscape (p. 12).** Platforms such as ChatGPT GPTs, AutoGen,
CrewAI and Semantic Kernel. They differ in names and convenience; underneath,
they all use the same few mechanisms you'll build by hand here.

## Discussion before chapter 2
- Which component would you need first for a useful assistant of your own?
- Look at `chapter_03/diy_gpts/app.py`: it combines four of the six
  components in one small app.
