# My GPTs

A homemade version of the custom GPTs from chapter 3 of *AI Agents in Action*,
built without ChatGPT Plus. Pick one of the book's instruction files
(`chapter_03/*_v1.txt`) in the sidebar. It becomes the system message for a
chat with whatever LLM `.env` points at: a local model in LM Studio, Gemini
(free tier) or OpenAI.

## Setup

1. Create the project's virtual environment (see the main README) and install
   Streamlit into it:
   ```bash
   .venv/bin/pip install streamlit
   ```
2. Create `my_gpts/.env` from the template and pick a provider by
   uncommenting its block:
   ```bash
   cp chapter_2/.env.example my_gpts/.env
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
.venv/bin/streamlit run my_gpts/app.py
```
The app opens at <http://localhost:8501>. Stop it with `Ctrl+C`.

### From IntelliJ / PyCharm

Create the run configuration once: **Run → Edit Configurations… → + → Python**.

| Field | Value |
|---|---|
| Name | `My GPTs` |
| Interpreter | Use specified interpreter: `~/Code/GPT-Agents/.venv` |
| `script` / `module` dropdown | switch to **module** and enter `streamlit` |
| Script parameters | `run app.py` |
| Working directory | `<repo>/my_gpts` |

Click **OK**, select **My GPTs** next to the ▶ button and run it. The Run panel
prints `Local URL: http://localhost:8501`. The command line at its top should
end in `-m streamlit run app.py`. Stop the server with the red ■.

If a field is missing in the dialog, look under **Modify options**.

## Working on the code

Streamlit notices when `app.py` is saved. Click **Rerun** at the top right of
the page (or press `R`) to load the change. You don't need to restart the
server.

## Stages

1. **Instructions + chat** (`app.py`): the system message comes from the
   chosen instruction file, and the history is resent on every turn.
2. **Knowledge**: a Calculus Made Easy assistant that answers from
   `chapter_03/calculus_made_easy.pdf` by retrieving relevant chunks of the book
   (the book is far too long to fit in a small model's context window).
3. **Actions**: function calling, for example the `daily_tasks_api.py` custom
   action.
4. **Code interpreter**: running generated code, such as plots.
