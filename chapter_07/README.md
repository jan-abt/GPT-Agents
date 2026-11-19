# Chapter 7: Assembling and using an agent platform (p. 160–179)

**In one sentence:** an agent platform puts the components in one app (a chat
UI, agent profiles, actions, later knowledge and memory); the book's is
**Nexus**, ours is **DIY GPTs**.

## Key ideas

- **Nexus (7.1, p. 161):** the author's Streamlit platform: choose an LLM, a
  persona and actions per chat.
- **Streamlit chat apps (7.2, p. 165):** a chat UI in about 35 lines. Two
  ways to show the reply: all at once behind a spinner, or **streamed** word
  by word with `st.write_stream()`.
- **Profiles and personas (7.3, p. 170):** Nexus describes an agent in a YAML
  file with sections for persona, actions, knowledge, memory, evaluation and
  planning (chapter 1's component list as a file format).
- **The agent engine (7.4, p. 172):** a class wrapping the LLM: send
  messages, keep history, run tools.
- **Actions (7.5, p. 174):** native and semantic functions, as in chapter 5.
  Nexus's `@agent_action` decorator **generates the JSON Schema tool
  description from the function's signature and docstring**; DIY GPTs writes
  it by hand (`task_tools()`).

## Walkthrough

1. The two chat apps (they read `chapter_07/.env`):
   ```bash
   cd ~/Code/GPT-Agents && .venv/bin/streamlit run chapter_07/chatgpt_clone_response.py
   cd ~/Code/GPT-Agents && .venv/bin/streamlit run chapter_07/chatgpt_clone_streaming.py
   ```
   Compare the scripts: they differ only in how the reply arrives.
2. Ask "Name the three primary colours", then "which two of them make
   green?". We got "red and green make green" (it had chosen the RGB colour
   model, where the question doesn't fit). With "…in one short sentence", the
   model chose paint colours and answered correctly. Precise questions matter
   (chapter 2); fluent isn't correct.
3. Map Nexus onto DIY GPTs:

   | Nexus | DIY GPTs (`chapter_03/diy_gpts`) |
   |---|---|
   | profile / persona | `chapter_03/*_v1.txt` instruction files |
   | agent engine | the chat loop in `app.py` |
   | actions | `actions.py` (stage 3) |
   | knowledge, memory | `knowledge.py`, `memory.py` (stages 2, 4) |

## What isn't installed
Nexus pins 2024 package versions (`chromadb 0.4`, `langchain 0.1`,
`fastapi 0.110`, …), wants Python 3.10, and is heavy. We use DIY GPTs instead;
Nexus reappears in the book in chapters 8 and 11, rebuilt there too.
