"""
DIY GPTs - stage 4: long-term memory.

Book: chapter 8, section 8.6 "Implementing memory in agentic systems"
(p. 200-206), and the de-duplication idea of 8.7 "Understanding memory and
knowledge compression" (p. 206).

Knowledge (stage 2) is loaded in advance. Memory is WRITTEN while you chat:

    after each answer:   your message ──LLM──▶ facts ──embed──▶ store      TODO 20, 21
    before each answer:  your question ──embed──▶ closest facts ──▶ prompt  TODO 22, 23

So it's the retrieval of stage 2, plus a step where an LLM decides what is
worth remembering (the book's "memory function", listing 8.10). Memories are
kept in a file, so they survive a new chat, another GPT, and a restart.

The store is one JSON file, .cache/memory.json (gitignored), shared by all
GPTs: the Culinary Companion can use what you told the Task Organizer.
Each memory: {"text": "The user is vegetarian.", "vector": [768 numbers]}.
"""
import json
from pathlib import Path

import numpy as np

from knowledge import CACHE_DIR, embed

STORE = CACHE_DIR / "memory.json"


def load_store(path: Path = STORE) -> list[dict]:
    """All memories, or an empty list if there are none yet."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def save_store(memories: list[dict], path: Path = STORE) -> None:
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(memories), encoding="utf-8")


def forget_all(path: Path = STORE) -> None:
    path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# TODO 20: the MEMORY FUNCTION - let the LLM pick out facts worth keeping.
#
# Send the user's message (and the assistant's reply, for context) with
# MEMORY_FUNCTION as the system message, and return the facts as a list of
# short sentences, e.g. ["The user is vegetarian.", "The user likes time
# travel movies."] - or [] when there is nothing personal to remember.
#
# Ask for JSON with response_format json_schema (chapter 2's json_output.py)
# so the reply can be parsed reliably: {"facts": ["...", "..."]}.
#
# Compare the book's listing 8.10, which summarises the whole conversation.
# Here we only keep lasting facts about the USER, so the store doesn't fill
# up with general knowledge the LLM already has.
# ---------------------------------------------------------------------------
MEMORY_FUNCTION = (
    "You maintain a memory of facts about the user. From the conversation below, extract "
    "lasting facts about the USER: preferences, diet, interests, plans, family, work, "
    "possessions. Write each as one short sentence starting with 'The user'. Ignore questions, "
    "general knowledge, and anything the assistant said about itself. If there is nothing "
    'personal to remember, return an empty list. Answer only with JSON: {"facts": [...]}'
)
FACTS_SCHEMA = {
    "name": "memories",
    "schema": {
        "type": "object",
        "properties": {"facts": {"type": "array", "items": {"type": "string"}}},
        "required": ["facts"],
    },
}


def extract_facts(client, model: str, user_text: str, reply: str) -> list[str]:
    response = client.chat.completions.create(
        model=model, temperature=0,
        messages=[
            {"role": "system", "content": MEMORY_FUNCTION},
            {"role": "user", "content": f"User: {user_text}\n\nAssistant: {reply}"},
        ],
        response_format={"type": "json_schema", "json_schema": FACTS_SCHEMA},
    )
    try:
        facts = json.loads(response.choices[0].message.content)["facts"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return []                     # an unparsable reply: remember nothing this time
    return [f.strip() for f in facts if isinstance(f, str) and f.strip()]


# ---------------------------------------------------------------------------
# TODO 21: store new facts - but not the ones we already know.
#
# Embed the facts (knowledge.embed, with the "search_document: " prefix).
# For each new fact, compare it with every stored memory by cosine
# similarity; if one is very close (>= DUPLICATE, e.g. "The user likes time
# travel movies" vs "The user enjoys time-travel films"), skip it. Otherwise
# append {"text": ..., "vector": [...]} and save the store.
# Return the facts that were actually added (the app shows them).
#
# This is the simplest form of 8.7's compression: instead of clustering and
# summarising duplicates later, don't store them in the first place.
# ---------------------------------------------------------------------------
DUPLICATE = 0.92


def _unit(vectors: np.ndarray) -> np.ndarray:
    """Scale every row to length 1, so a dot product is the cosine similarity."""
    return vectors / np.linalg.norm(vectors, axis=-1, keepdims=True)


def add_memories(client, facts: list[str], path: Path = STORE) -> list[str]:
    if not facts:
        return []
    memories = load_store(path)
    known = _unit(np.array([m["vector"] for m in memories])) if memories else np.empty((0, 0))
    added = []
    for fact, vector in zip(facts, _unit(embed(client, facts, prefix="search_document: "))):
        if len(known) and (known @ vector).max() >= DUPLICATE:
            continue                                            # already remembered
        memories.append({"text": fact, "vector": vector.tolist()})
        known = np.vstack([known, vector]) if len(known) else vector[None, :]
        added.append(fact)
    save_store(memories, path)
    return added


# ---------------------------------------------------------------------------
# TODO 22: recall the memories that matter for this question.
#
# Embed the question ("search_query: " prefix), score every memory by cosine
# similarity, and return the texts of the best k - but only those scoring at
# least RELEVANT. Without that floor, "What's 2+2?" would drag in "The user
# is vegetarian" just because it's the closest of a few memories.
#
# Measured with nomic-embed-text: unrelated questions ("What is 17 times 3?",
# "How do I fix a flat tyre?") score 0.37-0.44 against stored facts; related
# ones ("What should I cook for dinner?" vs "The user is vegetarian and loves
# spicy food") score 0.52-0.62. The gap is small - a question and a fact are
# worded very differently - so the floor sits just above the unrelated ones,
# and the prompt (TODO 23) tells the LLM to ignore what doesn't fit.
# ---------------------------------------------------------------------------
RELEVANT = 0.48


def recall(client, question: str, k: int = 3, path: Path = STORE) -> list[str]:
    memories = load_store(path)
    if not memories:
        return []
    question_vector = _unit(embed(client, [question], prefix="search_query: ")[0])
    scores = _unit(np.array([m["vector"] for m in memories])) @ question_vector
    best = np.argsort(scores)[::-1][:k]
    return [memories[i]["text"] for i in best if scores[i] >= RELEVANT]


# ---------------------------------------------------------------------------
# TODO 23: add the recalled memories to the GPT's instructions.
#
# Like add_knowledge() (TODO 6): the system prompt, then a short note, then
# the memories as a list - the "Remembered facts" of the book's figure 8.14.
# Tell the model to use them only when they're relevant, or it will mention
# your diet in every answer.
# ---------------------------------------------------------------------------
def add_memories_to_prompt(system_prompt: str, memories: list[str]) -> str:
    if not memories:
        return system_prompt
    facts = "\n".join(f"- {m}" for m in memories)
    return (f"{system_prompt}\n\nRemembered facts about the user (from earlier conversations). "
            f"Use them only where they are relevant to the request:\n{facts}")
