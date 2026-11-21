# Chapter 5: Empowering agents with actions (p. 98–128)

**In one sentence:** with function calling, the LLM *chooses* which of your
functions to call and with what arguments; your code runs it and hands the
result back.

## Key ideas

- **The LLM never runs anything (5.2, p. 101).** You send a JSON Schema
  description of each function (`tools=`). The model answers with a request:
  `recommend({"topic": "time travel movie"})`. Your code looks the name up,
  runs the real function, and sends the result back as a message with the role
  **`tool`**. A second call turns it into a normal answer.
- **The LLM sees descriptions, never code.** Name, description and parameters
  are all it knows about a function, so write them carefully.
- **Parallel calls (5.2.2, p. 103):** several tool calls in *one* reply. It's
  a model skill (the right output format), not concurrency.
- **Semantic Kernel (5.3–5.5, p. 107–125):** Microsoft's wrapper for the same
  loop. A *native* function is ordinary code; a *semantic* function is a prompt
  template run by the LLM; a *plugin* groups them; the *kernel* runs the loop
  and fills templates.
- **Semantic service layer (5.5, p. 118):** an LLM with tools in front of an
  existing API, so it can be used in plain language. The book wraps a movie
  database; DIY GPTs stage 3 wraps a task list.

## Walkthrough

```bash
(cd chapter_05 && python first_function.py)
```
1. **`first_function.py`**: one tool, two questions. The output is the *request*
   only (`Function(arguments=..., name='recommend')`). Note the invented
   `"rating": "good"` the user never asked for.
2. **`parallel_functions.py`**: the full loop: request → run `recommend()` →
   `tool` message → answer. Three items in one question needs three calls in
   one reply. Change the question to one item to see it with a weaker model.
3. **`movie_recommender.py`** (from the repo root:
   `python chapter_05/movie_recommender.py`): section 5.4 without
   Semantic Kernel. TODO 10 native function (`seen_movies.txt`), TODO 11 the
   "kernel" filling `{{$input}}` and `{{SeenMoviesPlugin.LoadSeenMovies}}`,
   TODO 12 turning the book's `plugins/Recommender/Recommend_Movies` prompt
   folder into a function.
4. **DIY GPTs stage 3** (the chapter 3 custom action, done with this chapter's
   loop). Start the task API, then the app, and pick **Task Organizer**:
   ```bash
   (cd chapter_03 && uvicorn daily_tasks_api:app --port 8100)
   ```
   Read `diy_gpts/actions.py` TODOs 7–9; the **Actions** panel shows each call
   and its result. Compare <http://localhost:8100/docs>, the OpenAPI spec
   ChatGPT would read.

## What we found
| Model | Single call | Parallel (3 in one reply) |
|---|---|---|
| llama-3.2-3b-instruct | works, but sent `false` as the string `"false"` and picked wrong filters | format error |
| qwen2.5-7b-instruct | 3/3, real booleans, right filters | 2/3 |
| qwen2.5-coder-7b (deleted) | 0/3: wrote calls as plain text | 0/3 |

With an empty result (the `"false"` bug), the model **invented tasks** that
looked plausible. Validate tool arguments; don't trust them blindly.

## Setup notes
`chapter_05/.env` (gitignored) sets the model; use `qwen2.5-7b-instruct` for
tool calls. The `SK_*.py` scripts need an old Semantic Kernel API that doesn't
install on Python 3.14; `test_tmdb_service.py` needs a TMDB API key.
