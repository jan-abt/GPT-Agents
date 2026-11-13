"""
Section 5.4 without Semantic Kernel: native + semantic functions in plain Python.

Book: chapter 5, section 5.4 "Synergizing semantic and native functions"
  5.4.1 Creating and registering a semantic skill/plugin   p. 111  (SK_first_skill.py)
  5.4.2 Applying native functions                          p. 115  (SK_native_functions.py)
  5.4.3 Embedding native functions within semantic ones    p. 117  (SK_semantic_native_functions.py)

The book's scripts need an old Semantic Kernel (SK) API that no longer exists
and doesn't install on Python 3.14. But SK is only a convenience layer over
two simple ideas, rebuilt here:

  * a NATIVE function is ordinary code: it reads files, calls APIs, computes.
    Here: load_seen_movies() reads seen_movies.txt.                    TODO 10
  * the KERNEL fills a template's placeholders: {{$name}} with a value you
    pass in, {{Plugin.Function}} with the result of calling a native function.
    That's render_template().                                           TODO 11
  * a SEMANTIC function is a prompt template run through the LLM. SK stores
    it as a folder with skprompt.txt (the prompt) and config.json (the
    description and LLM settings), e.g. plugins/Recommender/Recommend_Movies.
    load_semantic_function() turns such a folder into a Python function. TODO 12

Two ways to combine them, as in the book:
  1. code calls the native function and passes its result to the semantic one
     (5.4.1/5.4.2);
  2. the prompt template itself calls the native function, via
     {{SeenMoviesPlugin.LoadSeenMovies}} (5.4.3).

Run it from the repo root (it uses OPENAI_* from chapter_05/.env):
    .venv/bin/python chapter_05/movie_recommender.py
"""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


# ---------------------------------------------------------------------------
# TODO 10: the NATIVE function - plain code, no LLM.
#
# Read seen_movies.txt (one movie per line) and return the titles as one
# comma-separated string: "The Matrix, The Matrix Reloaded, ..."
# Skip empty lines and strip spaces and newlines.
#
# This is SK's MySeenMoviesDatabase.load_seen_movies() (listing in 5.4.2),
# minus the @kernel_function decorator - which only adds a description so an
# LLM could choose to call it, like task_tools() in DIY GPTs.
# ---------------------------------------------------------------------------
def load_seen_movies() -> str:
    lines = (HERE / "seen_movies.txt").read_text(encoding="utf-8").splitlines()
    return ", ".join(line.strip() for line in lines if line.strip())


# The native functions a template may call, by the name SK gives them:
# "<PluginName>.<FunctionName>".
NATIVE_FUNCTIONS = {"SeenMoviesPlugin.LoadSeenMovies": load_seen_movies}


# ---------------------------------------------------------------------------
# TODO 11: fill in a prompt template - the "kernel" part.
#
# Replace every placeholder in `template`:
#   {{$name}}             -> variables["name"]     (SK's context variables, 5.3.2)
#   {{Plugin.Function}}   -> NATIVE_FUNCTIONS["Plugin.Function"]()   (5.4.3)
# A placeholder may have spaces inside the braces: {{ $input }}.
#
# Hint: re.sub() accepts a function as the replacement. The pattern
#   r"\{\{\s*(\$?[\w.]+)\s*\}\}"
# captures "$input" or "SeenMoviesPlugin.LoadSeenMovies"; look at the first
# character to tell which kind it is.
# ---------------------------------------------------------------------------
def render_template(template: str, variables: dict[str, str]) -> str:
    def fill(match: re.Match) -> str:
        name = match.group(1)
        if name.startswith("$"):                 # {{$input}}: a value passed in
            return str(variables.get(name[1:], ""))
        return NATIVE_FUNCTIONS[name]()          # {{Plugin.Function}}: run native code

    return re.sub(r"\{\{\s*(\$?[\w.]+)\s*\}\}", fill, template)


# ---------------------------------------------------------------------------
# TODO 12: turn an SK semantic-function folder into a Python function.
#
# The folder holds skprompt.txt (the prompt template) and config.json
# (description + LLM settings under "completion": max_tokens, temperature...).
# Return a function `run(**variables) -> str` that:
#   - fills the template with render_template(prompt, variables)
#   - sends it to the LLM as the user message, using max_tokens and
#     temperature from config.json
#   - returns the LLM's reply text
#
# This is what SK's kernel.import_plugin_from_prompt_directory() did (5.4.1).
# ---------------------------------------------------------------------------
def load_semantic_function(folder: Path):
    prompt = (folder / "skprompt.txt").read_text(encoding="utf-8")
    config = json.loads((folder / "config.json").read_text(encoding="utf-8"))
    settings = config["completion"]

    def run(**variables: str) -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": render_template(prompt, variables)}],
            max_tokens=settings.get("max_tokens", 256),
            temperature=settings.get("temperature", 0),
        )
        return response.choices[0].message.content

    return run


if __name__ == "__main__":
    print(f"Model: {MODEL}\n")

    # 1. Code chains the two (5.4.1 + 5.4.2): native result -> semantic input.
    recommend = load_semantic_function(HERE / "plugins" / "Recommender" / "Recommend_Movies")
    seen = load_seen_movies()
    print("Native function, load_seen_movies():\n ", seen)
    print("\nSemantic function, Recommend_Movies (input = the list above):")
    print(recommend(input=seen))

    # 2. The template calls the native function itself (5.4.3).
    template = (
        "You are a wise movie recommender and you have been asked to recommend a movie to a user.\n"
        "You have a list of movies that the user has watched before.\n"
        "You want to recommend a movie that the user has not watched before.\n"
        "Movie List: {{SeenMoviesPlugin.LoadSeenMovies}}."
    )
    filled = render_template(template, {})
    print("\n" + "-" * 70)
    print("Template after render_template() - the native call is already filled in:\n")
    print(filled)
    reply = client.chat.completions.create(
        model=MODEL, messages=[{"role": "user", "content": filled}], temperature=0, max_tokens=256,
    ).choices[0].message.content
    print("\nLLM reply:\n" + reply)
