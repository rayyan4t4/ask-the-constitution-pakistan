"""Build retrieval index: article-aware chunks + MiniLM embeddings + FAISS."""
import json, re
import numpy as np

CHUNK = 800
OVERLAP = 120

def split(text):
    if len(text) <= CHUNK:
        return [text]
    parts, i = [], 0
    while i < len(text):
        j = min(i + CHUNK, len(text))
        if j < len(text):  # break at sentence end when possible
            k = text.rfind(". ", i + CHUNK - 200, j)
            if k > i + 200:
                j = k + 1
        parts.append(text[i:j].strip())
        i = j - OVERLAP if j < len(text) else j
    return [p for p in parts if p]

def main():
    arts = json.load(open("articles.json"))
    chunks = []
    for a in arts:
        header = f"Article {a['article']}: {a['title']}"
        for k, part in enumerate(split(a["text"])):
            chunks.append({
                "article": a["article"],
                "title": a["title"],
                "part": k,
                "n_parts": 0,  # filled below
                "text": f"{header}\n{part}",
                "source": a["source"],
            })
    # fill n_parts
    from collections import Counter
    counts = Counter((c["article"]) for c in chunks)
    for c in chunks:
        c["n_parts"] = counts[c["article"]]

    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    emb = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    import faiss
    index = faiss.IndexFlatIP(emb.shape[1])
    index.add(np.asarray(emb, dtype=np.float32))
    faiss.write_index(index, "faiss.index")
    json.dump(chunks, open("chunks.json", "w"), ensure_ascii=False, indent=1)
    np.save("embeddings.npy", emb)
    print(f"chunks={len(chunks)} dim={emb.shape[1]}")
    # coverage: every article has >=1 chunk, every chunk non-empty
    assert len({c["article"] for c in chunks}) == len(arts), "coverage broken"
    assert all(len(c["text"]) > 30 for c in chunks), "empty chunk found"
    print("coverage OK:", len(arts), "articles ->", len(chunks), "chunks")

if __name__ == "__main__":
    main()
