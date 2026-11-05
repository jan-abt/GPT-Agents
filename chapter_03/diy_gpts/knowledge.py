"""
DIY GPTs - stage 2: knowledge.

In ChatGPT you upload files to a GPT's "knowledge". Behind the scenes ChatGPT
splits them into chunks, finds the chunks that best match each question, and
adds only those to the prompt. A whole book doesn't fit into a small model's
context window (Calculus Made Easy is about 80,000 tokens, Llama's window is
8,192), so we do the same here, in three steps:

    split_into_chunks()  ->  search()  ->  add_knowledge()
         TODO 4               TODO 5          TODO 6

A GPT gets knowledge when a PDF with the same name sits next to its
instruction file:  calculus_made_easy_v1.txt  ->  calculus_made_easy.pdf
"""
import re
from pathlib import Path

from pypdf import PdfReader

CACHE_DIR = Path(__file__).parent / ".cache"     # extracted text, gitignored

# Words too common to say anything about what a question is about.
STOPWORDS = set("""
a about above after again all also am an and any are as at be because been
before being below between both but by can could did do does doing down during
each few for from further had has have having he her here hers him his how i
if in into is it its itself just me more most my no nor not now of off on once
only or other our out over own please same she should so some such tell than
that the their them then there these they this those through to too under
until up very was we were what when where which while who whom why will with
would you your yours
""".split())


def knowledge_file_for(instructions_path: Path) -> Path | None:
    """The PDF that belongs to a GPT's instruction file, or None if it has none."""
    pdf = instructions_path.with_name(instructions_path.stem.removesuffix("_v1") + ".pdf")
    return pdf if pdf.exists() else None


def load_text(pdf_path: Path) -> str:
    """The PDF's text. Extracting it takes a few seconds, so it's done once and
    cached in .cache/<name>.txt (open that file to see what the model works with)."""
    cache = CACHE_DIR / (pdf_path.stem + ".txt")
    if not cache.exists():
        text = "\n".join(page.extract_text() or "" for page in PdfReader(pdf_path).pages)
        CACHE_DIR.mkdir(exist_ok=True)
        cache.write_text(text, encoding="utf-8")
    return cache.read_text(encoding="utf-8")


def words_of(text: str) -> list[str]:
    """Lowercase words without punctuation: "What's dx?" -> ["what", "s", "dx"]"""
    return re.findall(r"[a-z0-9]+", text.lower())


# ---------------------------------------------------------------------------
# TODO 4: split the book into chunks of `size` words.
#
# Each chunk starts `size - overlap` words after the previous one, so
# neighbouring chunks share `overlap` words. That way a sentence cut at the
# end of one chunk is still whole at the start of the next.
#
#   text = "w1 w2 w3 w4 w5 w6 w7",  size=4, overlap=2
#   ->  ["w1 w2 w3 w4", "w3 w4 w5 w6", "w5 w6 w7"]
#
# Hints: text.split() gives the list of words; range() takes a step argument;
# " ".join(...) turns a list of words back into a string.
# ---------------------------------------------------------------------------
def split_into_chunks(text: str, size: int = 200, overlap: int = 50) -> list[str]:
    words = text.split()
    step = size - overlap                      # 150: each chunk starts 150 words after the previous one
    chunks = []
    for start in range(0, len(words), step):   # 0, 150, 300, 450, ...
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):         # this chunk reached the end of the book
            break
    return chunks

# ---------------------------------------------------------------------------
# TODO 5: return the `k` chunks that best match the question.
#
# A simple score that works surprisingly well: for each chunk, count how
# often the question's important words (not in STOPWORDS) appear in it.
# Then sort the chunks by score, highest first, and keep the first k.
#
# Hints: words_of() gives you the words of the question and of each chunk;
# sorted(..., key=..., reverse=True) sorts by any score you compute.
# ---------------------------------------------------------------------------
def search(chunks: list[str], question: str, k: int = 3) -> list[str]:
    # The words that say what the question is about: "what does dx mean" -> ["dx", "mean"]
    terms = [w for w in words_of(question) if w not in STOPWORDS]

    def score(chunk: str) -> int:
        chunk_words = words_of(chunk)
        return sum(chunk_words.count(term) for term in terms)

    return sorted(chunks, key=score, reverse=True)[:k]   # best first, keep k


# ---------------------------------------------------------------------------
# TODO 6: add the chunks to the GPT's instructions.
#
# Return the system prompt, followed by a short note telling the model to
# answer from the excerpts, followed by each chunk wrapped in delimiters:
#
#   <document>
#   ...chunk text...
#   </document>
#
# (The delimiters tactic from chapter 2: the tags show the model where the
# book's text starts and ends, so it doesn't mistake it for instructions.)
# ---------------------------------------------------------------------------
def add_knowledge(system_prompt: str, chunks: list[str]) -> str:
    documents = "\n\n".join(f"<document>\n{chunk}\n</document>" for chunk in chunks)
    note = ("Answer using the following excerpts from the book. "
            "If they don't cover the question, say so before answering from your own knowledge.")
    return f"{system_prompt}\n\n{note}\n\n{documents}"
