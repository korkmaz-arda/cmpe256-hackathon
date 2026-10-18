"""TF-IDF retrieval over the domain knowledge base (no API keys needed).

One shared vectorizer is fit on ALL chunks so that cross-domain cosine
scores are comparable (used by the Manager for intent classification).
Per-domain retrieval restricts to that domain's chunk indices.
"""
import json
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

KB_PATH = Path(__file__).resolve().parent.parent / "data" / "kb" / "kb.json"

_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str):
    return _TOKEN.findall(text.lower())


class KnowledgeBase:
    def __init__(self, kb_path: str = str(KB_PATH)):
        with open(kb_path, encoding="utf-8") as f:
            self.chunks = json.load(f)["chunks"]
        self.domains = sorted({c["domain"] for c in self.chunks})
        self.by_domain = {d: [i for i, c in enumerate(self.chunks)
                              if c["domain"] == d] for d in self.domains}
        self.vectorizer = TfidfVectorizer(
            tokenizer=tokenize, ngram_range=(1, 2),
            sublinear_tf=True, max_features=40000)
        self.matrix = self.vectorizer.fit_transform(
            [c["text"] for c in self.chunks])
        # domain centroids for intent classification
        self.centroids = {}
        for d, idx in self.by_domain.items():
            m = self.matrix[idx]
            self.centroids[d] = np.asarray(m.mean(axis=0)).ravel()

    def retrieve(self, query: str, domain: str, k: int = 5):
        """Top-k chunks from one domain, with cosine scores."""
        idx = self.by_domain[domain]
        q = self.vectorizer.transform([query])
        sims = cosine_similarity(q, self.matrix[idx]).ravel()
        order = np.argsort(-sims)[:k]
        return [(self.chunks[idx[i]], float(sims[i])) for i in order
                if sims[i] > 0]

    def domain_scores(self, query: str):
        """Cosine similarity of the query to each domain centroid."""
        qv = self.vectorizer.transform([query])
        qn = np.linalg.norm(qv.toarray())
        scores = {}
        for d, c in self.centroids.items():
            denom = qn * np.linalg.norm(c)
            scores[d] = float((qv.toarray().ravel() @ c) / denom) if denom else 0.0
        return scores

    def cite(self, chunk) -> str:
        return f"[{chunk['source']} #{chunk['id']}]"
