# Chapter 8 on local models

## Setup

```bash
.venv/bin/pip install scikit-learn plotly chromadb      # about 142 MB in total
~/.lmstudio/bin/lms load text-embedding-nomic-embed-text-v1.5
```
Give this folder its own `.env` (gitignored; same format as
`chapter_2/.env.example`), with one extra line for the embedding model:
```
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
```

## 8.3 Semantic search: the four document scripts work

Run them from this folder (`cd chapter_08`). They're interactive.

| Section | Script | Notes |
|---|---|---|
| 8.3.1 Vector similarity | `document_vector_similarity.py` | TF-IDF + cosine similarity, plotted as a heatmap. Unchanged |
| 8.3.2 Vector databases | `document_vector_database.py` | a TF-IDF search engine. Unchanged |
| 8.3.3 Document embeddings | `document_visualizing_embeddings.py` | embeddings reduced to 3D with PCA |
| 8.3.4 Querying Chroma | `document_query_chromadb.py` | embeddings stored and searched in Chroma |

The two embedding scripts were changed in one place each: the client reads
`OPENAI_BASE_URL` (LM Studio) and the model name comes from `EMBEDDING_MODEL`,
instead of OpenAI's `text-embedding-ada-002`. Without those settings they
behave as in the book.

**Words vs. meaning**, on the book's eight sample sentences:

| Query | TF-IDF (8.3.2) top match | Embeddings + Chroma (8.3.4) top match |
|---|---|---|
| "blue sky" | The sky is blue and beautiful. | The sky is blue and beautiful. |
| "something to eat in the morning" | The quick brown fox jumps over the lazy dog. (it shares only "the") | A king's breakfast has sausages, ham, bacon, eggs, toast, and beans |

## Not runnable on Python 3.14

- **8.4 LangChain scripts** (`langChain_*.py`, `testing.py`): they use imports
  such as `langchain.document_loaders` that newer LangChain versions removed.
  `chapter_03/diy_gpts/knowledge.py` does the same splitting into chunks.
- **8.6 Semantic Kernel memory scripts** (`SK_semantic_*.py`): Semantic Kernel
  doesn't install on Python 3.14, and the scripts use its old API.
