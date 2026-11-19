# DIY GPTs: chapter 3 without ChatGPT Plus

Chapter 3 of *AI Agents in Action* builds custom GPTs with ChatGPT's GPT
Builder, a no-code tool that needs a paid ChatGPT Plus subscription. This
folder rebuilds the same assistants **in code**, so they run on a free or local
model instead:

- a local model in **LM Studio** (free, offline, no rate limits),
- **Gemini**'s free tier, or
- OpenAI, if you have an API key.

Pick one of the book's instruction files (`chapter_03/*_v1.txt`) in the
sidebar. It becomes the system message of a chat with the model that `.env`
points at.

## How it differs from the book

A custom GPT in ChatGPT is: **instructions** + optional **knowledge files** +
optional **tools/actions**, wrapped in a chat UI. ChatGPT does the plumbing for
you. Here you write it, so you can see exactly what is sent to the model.

| Chapter 3 exercise (in ChatGPT) | DIY version | Status |
|---|---|---|
| 1. Culinary Companion with custom rules | Stage 1: instructions + chat (`app.py`) | ✅ done |
| 4. Knowledge assistant from uploaded files | Stage 2: Calculus Made Easy with retrieval (`knowledge.py`) | ✅ done (keywords, and embeddings since chapter 8) |
| 3. Custom action with FastAPI + ngrok | Stage 3: Task Organizer calls `../daily_tasks_api.py` through function calling (`actions.py`; local, no ngrok needed) | in progress |
| 2. Data analysis with the code interpreter | (not built: chapter 4 covers running generated code) | optional |
| 5. Publish to the GPT Store | not possible; the code is on GitHub instead | — |

What a small local model can't do, compared with ChatGPT:
- **Images.** The Culinary Companion's rule *"always create an image"* needs an
  image-generation tool, so a text model only describes the picture.
- **Following long instructions.** A 3B model follows short, explicit rules
  much better than long ones (compare Culinary Companion with Data Scout).
- **Holding a boundary.** Told to refuse off-topic questions, Llama sometimes
  refuses and then answers anyway; a larger model (Gemini) is more reliable.

The book itself builds assistants in code later: function calling in
chapter 5, retrieval in chapter 8, and a Streamlit chat app (Nexus) in
chapter 7.

## Setup

1. Create the project's virtual environment (see the main README) and install
   this folder's packages into it (Streamlit for the UI, pypdf to read PDFs,
   numpy for the embedding search):
   ```bash
   .venv/bin/pip install -r chapter_03/diy_gpts/requirements.txt
   ```
2. Create `.env` from the template and pick a provider by uncommenting its
   block:
   ```bash
   cp chapter_2/.env.example chapter_03/diy_gpts/.env
   ```
   `.env` is gitignored, so your API key stays local.
3. If you use LM Studio, start its server and load the model first:
   ```bash
   ~/.lmstudio/bin/lms server start
   ~/.lmstudio/bin/lms load llama-3.2-3b-instruct --yes
   ```

## Run it

A Streamlit app must be started with `streamlit run`, not `python app.py`.
Run as a plain script, nothing appears in the browser and the console fills up
with `missing ScriptRunContext ... bare mode` warnings.

### From a terminal

From the repo root:
```bash
.venv/bin/streamlit run chapter_03/diy_gpts/app.py
```
The app opens at <http://localhost:8501>. Stop it with `Ctrl+C`.

### From IntelliJ / PyCharm

Create the run configuration once: **Run → Edit Configurations… → + → Python**.

| Field | Value |
|---|---|
| Name | `DIY GPTs` |
| Interpreter | Use specified interpreter: `<repo>/.venv` |
| `script` / `module` dropdown | switch to **module** and enter `streamlit` |
| Script parameters | `run app.py` |
| Working directory | `<repo>/chapter_03/diy_gpts` |

Click **OK**, select the configuration next to the ▶ button and run it. The Run
panel prints `Local URL: http://localhost:8501`. The command line at its top
should end in `-m streamlit run app.py`. Stop the server with the red ■.

If a field is missing in the dialog, look under **Modify options**.

## Working on the code

Streamlit notices when `app.py` is saved. Click **Rerun** at the top right of
the page (or press `R`) to load the change. You don't need to restart the
server.

The conversation lives in `st.session_state`, in the server's memory: it
survives a Rerun, but not reloading the browser tab or restarting the server.

## Adding your own GPT

Any file in `chapter_03/` named `*_v1.txt` shows up in the sidebar. Copy one,
edit the instructions, and click Rerun.

## Stage 2: knowledge (retrieval)

A GPT gets knowledge when a PDF with the same name sits next to its
instruction file: `calculus_made_easy_v1.txt` → `calculus_made_easy.pdf`.
For those GPTs the sidebar's **Use knowledge** switch is on.

Calculus Made Easy is about 80,000 tokens; Llama's context window is 8,192.
So, like ChatGPT does behind the scenes, `knowledge.py` sends only the parts of
the book that match each question:

1. **Split** the book into overlapping chunks of 200 words (TODO 4).
2. **Search**: score every chunk against the question and keep the best 3
   (TODO 5).
3. **Inject**: add them to the system message inside `<document>` tags, for
   this turn only (TODO 6).

The **Knowledge** panel above each answer shows the excerpts the model got.
The extracted text is cached in `.cache/calculus_made_easy.txt` (gitignored).

**Things to try:** switch **Use knowledge** off and ask the same question to
compare. Without the book, Llama answers from memory and can be confidently
wrong; with it, check whether the answer uses the excerpts.

**Known limit of keyword search:** in a calculus book, `d` and `dx` appear on
almost every page, so counting matching words favours formula-heavy pages over
the passage that actually explains something. The book's definition of `d`
("merely means 'a little bit of'") ranks only 47th for the question *"what
does the little letter d in dx mean?"*. Weighting rare words higher (TF-IDF)
helps a bit, but not enough. Searching by meaning instead of by words, with
**embeddings**, is the next step (and the topic of chapter 8).

### Chapter 8 upgrade: search by meaning (TODOs 17–19)

Book: chapter 8, sections 8.3 (semantic search, p. 184–192) and 8.5 (RAG for
agent knowledge, p. 196). The sidebar's **Search the book by** switch chooses
between **Keywords** (TODO 5) and **Embeddings**:

17. `embed()`: turn texts into vectors with a local embedding model, through
    the same OpenAI client (LM Studio answers `/v1/embeddings` too).
18. `load_vectors()`: embed all 395 chunks once (about a minute on a CPU) and
    cache them in `.cache/<book>.<model>.npy`.
19. `semantic_search()`: embed the question and rank the chunks by cosine
    similarity.

It needs LM Studio's `text-embedding-nomic-embed-text-v1.5` (84 MB) loaded,
and in `diy_gpts/.env`:
```
EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5
```

Rank of the passage that actually answers the question:

| Question | Keywords | Embeddings |
|---|---|---|
| "what does the little letter d in dx mean?" | 47 | **2** (rank 1: another passage defining `d` as "a bit of") |
| "What does the long S symbol for integration mean?" | 15 | **2** |
| "What are the preliminary terrors?" | 1 | 1 |

With embeddings, Qwen answered the `d` question with the book's own words,
"a little bit of", read "dee-eks"; with keywords it got a page of integration
formulas and answered from its general knowledge.

## Stage 3: actions (function calling)

Book: chapter 3, section 3.3 "Customizing a GPT and adding custom actions"
(p. 49–56), done in code with chapter 5, section 5.2 "Executing OpenAI
functions" (p. 101–106).

In ChatGPT, a custom action is a web API the GPT may call: you paste the API's
OpenAPI spec into the GPT Builder. Here the **Task Organizer** gets a tool,
`get_tasks`, that calls the book's FastAPI service `chapter_03/daily_tasks_api.py`:

1. **Describe** the tool to the LLM in JSON Schema (TODO 7).
2. The LLM answers with a *request* to call it, e.g. `get_tasks(completed=false)`.
   It never runs anything itself.
3. **Run** it: our function calls the web API (TODO 8).
4. **Report** the results back as `tool` messages (TODO 9).
5. The LLM answers the user from those results.

**Start the task API first** (port 8100, because 8000 is often taken):
```bash
cd chapter_03 && ../.venv/bin/uvicorn daily_tasks_api:app --port 8100
```
The sidebar shows whether it's reachable. Its interactive docs, generated by
FastAPI, are at <http://localhost:8100/docs>, and the OpenAPI spec ChatGPT
would read is at <http://localhost:8100/openapi.json>.

The **Actions** panel above each answer shows the calls the LLM made and what
the API returned.

**Things to try:** "Which tasks are still open?", "What have I finished?",
"How should I organize my tasks for today?". Then switch **Use actions** off
and ask again: without the API, the model has no idea what your tasks are.

**Use a model trained for tools.** Llama 3.2 3B handles one call at a time.
Qwen2.5-Coder writes its calls as plain text, so LM Studio sees no tool call
at all. LM Studio marks tool-capable models with `tool_use`.

**Lesson learned while building this:** Llama sends the boolean argument as a
string (`"false"`). Compared with the API's real `false`, it never matches,
every task gets filtered out, and the LLM, handed an empty list, invents
tasks that look completely plausible. Always validate tool arguments.

The Task Organizer's instruction to "create a plot" needs ChatGPT's code
interpreter; a text model can only describe the plot.

## Stage 4: memory

Book: chapter 8, section 8.6 "Implementing memory in agentic systems"
(p. 200–206), plus the de-duplication idea from 8.7 (p. 206).

Knowledge is loaded in advance; **memory is written while you chat**, by an
LLM, and recalled in later chats, by every GPT. `memory.py`:

20. `extract_facts()`: the **memory function** (the book's listing 8.10). After
    each answer, the LLM picks out lasting facts about you ("The user is
    vegetarian."), returned as JSON.
21. `add_memories()`: embeds the facts and stores them in
    `.cache/memory.json` (gitignored), skipping near-duplicates of what's
    already stored.
22. `recall()`: before each answer, finds the stored facts closest to your
    question.
23. `add_memories_to_prompt()`: adds them to the system message as
    "Remembered facts", to be used only where relevant.

The sidebar has a **Use memory** switch and lists everything stored, with a
**Forget everything** button. A **Memory** panel above an answer shows what was
recalled, and "🧠 Remembered: …" below it shows what was just stored.

Example, in two separate chats with the Culinary Companion:
1. "I'm vegetarian and I love really spicy food. Suggest a quick lunch." →
   🧠 Remembered: *The user is vegetarian and loves really spicy food.*
2. New chat: "What should I cook for dinner tonight?" → recalls that fact →
   a **spicy vegetarian stir-fry** (without memory: Chicken Alfredo).
3. "What is 17 times 3?" → nothing recalled.

**The tricky part is deciding what's relevant.** A question and a fact about
you are worded very differently, so their similarity scores are close
together: unrelated questions scored 0.37–0.44 against stored facts, related
ones 0.52–0.62. `RELEVANT = 0.48` sits in between; the prompt tells the LLM
to ignore recalled facts that don't fit. The book's 8.6.2 "semantic memory"
improves this by having an LLM turn the input into questions before
searching.

Memory costs one extra LLM call per turn (plus embeddings): switch it off when
you don't need it.
