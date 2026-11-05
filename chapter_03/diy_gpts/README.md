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
| 4. Knowledge assistant from uploaded files | Stage 2: Calculus Made Easy with retrieval (`knowledge.py`) | ✅ done (keyword search) |
| 3. Custom action with FastAPI + ngrok | Stage 3: function calling with `../daily_tasks_api.py` (local, no ngrok needed) | planned |
| 2. Data analysis with the code interpreter | Stage 4: running generated code | optional |
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
   this folder's packages into it (Streamlit for the UI, pypdf to read PDFs):
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
