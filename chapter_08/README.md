# Chapter 8: Understanding agent memory and knowledge (p. 180–211)

**In one sentence:** agents look things up by *meaning* using embeddings;
**knowledge** is loaded in advance, **memory** is written by an LLM while the
agent works.

## Key ideas

- **RAG (8.1–8.2, p. 181):** retrieval-augmented generation: find the
  relevant pieces, put them in the prompt, then answer.
- **Vector similarity (8.3.1–8.3.2, p. 184):** turn texts into vectors and
  compare them with **cosine similarity** (1 = same direction, 0 = unrelated).
  TF-IDF vectors count *words*.
- **Embeddings (8.3.3, p. 189):** vectors from a model, so similar *meaning*
  gives similar vectors (768 numbers with `nomic-embed-text`).
- **Vector databases (8.3.4, p. 190):** store vectors and search them; Chroma
  reports *distance* (lower = closer).
- **Chunking (8.4, p. 192):** split documents into overlapping pieces before
  embedding.
- **Memory (8.6, p. 200):** short-term = the chat history; long-term =
  *semantic* (facts), *episodic* (events), *procedural* (skills = tools). A
  **memory function** (an LLM prompt) decides what to store.
- **Compression (8.7, p. 207):** cluster similar memories and summarise each
  cluster.

## Walkthrough

Load the embedding model first: `~/.lmstudio/bin/lms load text-embedding-nomic-embed-text-v1.5`
```bash
cd ~/Code/GPT-Agents/chapter_08
~/Code/GPT-Agents/.venv/bin/python document_vector_database.py
```
1. **`document_vector_similarity.py`**: TF-IDF similarity of 8 sentences as a
   heatmap (opens in the browser).
2. **`document_vector_database.py`**: TF-IDF search. Try "blue sky", then
   "something to eat in the morning": it returns fox sentences (they share only
   "the").
3. **`document_visualizing_embeddings.py`**: the same sentences as embeddings,
   in 3D; the sky, breakfast and fox sentences form clusters.
4. **`document_query_chromadb.py`**: embeddings in Chroma. "something to eat in
   the morning" now finds the **breakfast** sentence, with no word in common.
5. **DIY GPTs stage 2 with embeddings** (`chapter_03/diy_gpts/knowledge.py`,
   TODOs 17–19): pick **Calculus Made Easy**, switch **Search the book by**
   between Keywords and Embeddings, and ask "what does the little letter d in
   dx mean?". Open the **Knowledge** panel to see the excerpts.
6. **DIY GPTs stage 4, memory** (`memory.py`, TODOs 20–23): tell the Culinary
   Companion "I'm vegetarian and love spicy food", start a **New chat**, ask
   "What should I cook tonight?". The sidebar lists the memories, with
   **Forget everything**.

## What we found
| Question | Keywords | Embeddings |
|---|---|---|
| book's definition of `d` ("a little bit of") | rank 47 | rank 2 |
| "long S" (integration) | rank 15 | rank 2 |

Memory: related questions scored 0.52–0.62 against stored facts, unrelated
ones 0.37–0.44; the floor `RELEVANT = 0.48` sits between them. A question and
a fact are worded differently, which is why the book's 8.6.2 has an LLM
rephrase questions first.

## Setup notes
`.venv/bin/pip install scikit-learn plotly chromadb` (about 142 MB).
`chapter_08/.env` (gitignored) adds
`EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5`; the two embedding
scripts read it and `OPENAI_BASE_URL`. Not runnable on Python 3.14: the
`langChain_*.py` scripts (removed LangChain imports) and `SK_semantic_*.py`
(Semantic Kernel).
