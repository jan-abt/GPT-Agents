# Chapter 2: Harnessing the power of large language models (p. 16–37)

**In one sentence:** an LLM is a stateless text-in, text-out service; you
talk to it with a list of role-tagged messages, and how you write them
(prompt engineering) changes the answers a lot.

## Key ideas

- **The chat completions API (2.1, p. 16).** You send `messages`, a list of
  `{"role": ..., "content": ...}`, and get one reply back. Roles: `system`
  (instructions), `user` (you), `assistant` (earlier replies). The API is
  stateless: it remembers nothing, so to continue a conversation you resend
  the whole history every time.
- **Any OpenAI-compatible server works (2.2, p. 20).** LM Studio, Gemini and
  others accept the same request format; switching is `OPENAI_BASE_URL` +
  `OPENAI_MODEL` in `.env`, with no code changes.
- **Prompt engineering tactics (2.3, p. 25):** detailed queries (p. 28),
  personas (p. 29), delimiters (p. 30), steps (p. 31), examples (p. 32),
  output length (p. 33).
- **Choosing a model (2.4, p. 34):** size, speed, cost and skills differ.

## Walkthrough

Start LM Studio (see the study guide), then run each script from this folder:
```bash
cd ~/Code/GPT-Agents/chapter_2
~/Code/GPT-Agents/.venv/bin/python connecting.py
```
1. **`connecting.py`**: the smallest possible request, a system message plus
   one question ("What is the capital of France?").
2. **`message_history.py`**: the history is resent: earlier question, earlier
   answer ("Paris"), and a new question ("an interesting fact of Paris") that
   only makes sense with that history. It prints the full JSON response:
   look at `usage` (tokens) and `finish_reason`.
3. **`json_output.py`**: `response_format` with a JSON schema forces the
   reply into a fixed structure (`city`, `interesting_fact`) that code can
   read. Used again in chapters 9 and 11.
4. **`prompt_engineering.py`**: a menu of the tactics in `prompts/`. Most files
   hold two versions of a prompt (weaker, then better); compare the answers.
   - `using_delimiters.jsonl`: without tags, the model *answered* "What time
     does the museum open?" instead of translating it; with `<text>` tags it
     translated.
   - `provide_examples.jsonl` (one prompt): an example exchange plus the
     explicit rule "limit all future replies to a single sentence". In our
     tests, examples without that rule gave long replies.
5. `lmstudio_server.py`: LM Studio's own minimal example ("answer in rhymes").

## What we found with small local models
- Explicit rules beat implied ones; small models weigh the end of the user
  message most.
- Fixed wording (a label, a heading) is more reliable added by code than
  requested from the model.
- Ambiguous questions get confident wrong answers (chapter 7's "which two
  primary colours make green?" example).

## Setup notes
`chapter_2/.env` (gitignored) is created from `.env.example`, which also
explains which local model suits which chapter. Requests to Gemini's free tier
are limited to about 20 per day per model.
