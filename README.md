# Ask the Constitution — Pakistan

A retrieval-augmented chatbot over the Constitution of Pakistan (1973, as amended).
Ask questions in plain language; answers are grounded in the actual articles with citations.

**Live app:** (link after deploy)
**Author:** Rayyan Khan — [rayyankhan.online](https://rayyankhan.online)

## How it works

1. **Corpus** — `crawl.py` scrapes the full constitution text (323 articles, numbers 1–280
   complete, + 5 schedules) from pakistani.org into `articles.json`.
2. **Index** — `build_index.py` splits long articles into ~800-char chunks (each prefixed
   with its article header so citations stay clean), embeds with `all-MiniLM-L6-v2`,
   and builds a FAISS inner-product index (`faiss.index`, `chunks.json`).
3. **Retrieval** — `rag.py` embeds the query and returns the top-5 chunks.
4. **Generation** — the top chunks + question go to an LLM (OpenRouter free tier)
   with a strict "answer only from the excerpts, cite every claim" system prompt.

## Evaluation

`evaluate.py` runs 30 hand-written questions against gold article labels (`eval_set.py`):

| metric | result |
|---|---|
| hit-rate@1 | 0.867 (26/30) |
| hit-rate@3 | 0.933 (28/30) |
| hit-rate@5 | 1.000 (30/30) |

Baseline for comparison: asking the LLM the same questions with **no retrieval**.
RAG answers cite specific articles; the no-retrieval baseline frequently answers
vaguely or hedges. See `metrics.json` for per-question results.

## Project layout

- `crawl.py` — scrape constitution text → `articles.json`
- `build_index.py` — chunk + embed + FAISS index
- `evaluate.py` / `eval_set.py` — retrieval evaluation
- `rag.py` — retrieval + generation logic
- `streamlit_app.py` — the web app
- `Ask_the_Constitution.ipynb` — end-to-end notebook (crawl → index → evaluate)

## Run locally

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python crawl.py && python build_index.py && python evaluate.py
OPENROUTER_API_KEY=... streamlit run streamlit_app.py
```

On Streamlit Cloud, set `OPENROUTER_API_KEY` in the app's Secrets.

## Limitations

- Informational only — **not legal advice**. Consult a lawyer for real cases.
- The model can only answer from the constitution text; it has no knowledge of
  case law or post-crawl amendments.
- Retrieval is semantic, not exact: unusually phrased questions can miss the
  right article (see misses in `metrics.json`).
