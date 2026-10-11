"""Retrieval + generation over the Constitution of Pakistan."""
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

_model = None
_index = None
_chunks = None

def load():
    global _model, _index, _chunks
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _index = faiss.read_index("faiss.index")
        _chunks = json.load(open("chunks.json"))
    return _model, _index, _chunks

def retrieve(query, k=5):
    model, index, chunks = load()
    q = model.encode([query], normalize_embeddings=True)
    D, I = index.search(np.asarray(q, dtype=np.float32), k)
    results = []
    for score, i in zip(D[0], I[0]):
        c = chunks[int(i)]
        results.append({
            "article": c["article"], "title": c["title"],
            "text": c["text"], "score": float(score),
            "source": c["source"],
        })
    return results

def build_context(results):
    parts = []
    for r in results:
        parts.append(f"[Article {r['article']}: {r['title']}]\n{r['text']}")
    return "\n\n".join(parts)

SYSTEM = (
    "You answer questions about the Constitution of Pakistan using ONLY the excerpts provided. "
    "Cite the article number for every factual claim, e.g. (Article 19). "
    "If the excerpts do not contain the answer, say so plainly instead of guessing. "
    "Keep answers concise and in plain language."
)

def generate(question, results, api_key, model="poolside/laguna-s-2.1:free"):
    import requests
    context = build_context(results)
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"},
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        },
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
