"""Retrieval evaluation: hit-rate@k on the gold question set."""
import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from eval_set import EVAL

def main():
    chunks = json.load(open("chunks.json"))
    index = faiss.read_index("faiss.index")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    questions = [q for q, _ in EVAL]
    q_emb = model.encode(questions, normalize_embeddings=True, show_progress_bar=False)
    D, I = index.search(np.asarray(q_emb, dtype=np.float32), 5)

    hits1 = hits3 = hits5 = 0
    misses = []
    for (q, gold), idxs in zip(EVAL, I):
        retrieved = [chunks[i]["article"] for i in idxs]
        # a hit if ANY gold article appears in top-k (chunk-level -> article-level)
        if any(g in retrieved[:1] for g in gold):
            hits1 += 1
        if any(g in retrieved[:3] for g in gold):
            hits3 += 1
        if any(g in retrieved[:5] for g in gold):
            hits5 += 1
        else:
            misses.append((q, gold, retrieved))
    n = len(EVAL)
    print(f"n={n}")
    print(f"hit-rate@1: {hits1/n:.3f} ({hits1}/{n})")
    print(f"hit-rate@3: {hits3/n:.3f} ({hits3}/{n})")
    print(f"hit-rate@5: {hits5/n:.3f} ({hits5}/{n})")
    print("\nmisses@5:")
    for q, gold, ret in misses:
        print(f"  Q: {q}\n    gold={gold} retrieved={ret}")
    json.dump({"n": n, "hr1": hits1/n, "hr3": hits3/n, "hr5": hits5/n,
               "misses": [{"q": q, "gold": gold, "retrieved": ret} for q, gold, ret in misses]},
              open("metrics.json", "w"), indent=1)

if __name__ == "__main__":
    main()
