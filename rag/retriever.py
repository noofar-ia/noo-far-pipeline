"""
rag/retriever.py — Récupération hybride BM25 + embeddings.
"""

import yaml
from pathlib import Path
import numpy as np
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi


def _minmax(scores):
    """Normalise un vecteur de scores dans [0, 1] pour rendre sémantique et BM25 comparables."""
    scores = np.asarray(scores, dtype=float)
    lo, hi = scores.min(), scores.max()
    if hi - lo < 1e-9:
        return np.zeros_like(scores)
    return (scores - lo) / (hi - lo)


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


class HybridRetriever:
    def __init__(self, lang=None, collection_name=None):
        config = load_config()
        lang = lang or config["lang"]  # utilise la langue active de config.yaml par défaut
        self.top_k = config["rag"].get("top_k", 3)
        embedding_model = config["rag"]["embedding_model"]
        hybrid_weights = config["rag"].get("hybrid_weights", {"semantic": 0.5, "bm25": 0.5})
        self.w_semantic = hybrid_weights["semantic"]
        self.w_bm25 = hybrid_weights["bm25"]

        client = chromadb.PersistentClient(path=str(Path(__file__).parent / "chroma"))
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
        self.collection = client.get_collection(
            name=collection_name or f"fiches_{lang}",
            embedding_function=self.embedding_fn
         )

        # Récupérer tous les documents (+ embeddings) pour construire l'index BM25 et la fusion pondérée
        all_docs = self.collection.get(include=["documents", "metadatas", "embeddings"])
        self.documents = all_docs["documents"]
        self.metadatas = all_docs["metadatas"]
        self.ids = all_docs["ids"]
        doc_embeddings = np.array(all_docs["embeddings"])
        self.doc_embeddings_norm = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)
        tokenized = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized)

    def retrieve_semantic(self, question, k=None):
        k = k or self.top_k
        results = self.collection.query(query_texts=[question], n_results=k)
        return list(zip(results["documents"][0], results["metadatas"][0]))

    def retrieve_bm25(self, question, k=None):
        k = k or self.top_k
        tokenized_q = question.lower().split()
        scores = self.bm25.get_scores(tokenized_q)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        return [(self.documents[i], self.metadatas[i]) for i in top_indices]

    def retrieve_hybrid(self, question, k=None):
        """Fusionne sémantique + BM25 par somme pondérée de scores normalisés (min-max par requête).

        Poids par défaut 0.2/0.8 (config rag.hybrid_weights) : le modèle d'embedding actuel
        n'est pas entraîné sur le wolof et produit un effet "hub" (un document scorant haut
        pour presque toutes les requêtes, cf. diagnostic S2-J3) — sous-pondérer le sémantique
        neutralise ce biais sans perdre l'apport ponctuel du signal sémantique.
        """
        k = k or self.top_k
        q_embedding = np.array(self.embedding_fn([question])[0])
        q_embedding_norm = q_embedding / np.linalg.norm(q_embedding)
        sem_scores = self.doc_embeddings_norm @ q_embedding_norm

        tokenized_q = question.lower().split()
        bm25_scores = np.asarray(self.bm25.get_scores(tokenized_q))

        combined = self.w_semantic * _minmax(sem_scores) + self.w_bm25 * _minmax(bm25_scores)
        top_indices = np.argsort(-combined)[:k]
        return [(self.documents[i], self.metadatas[i]) for i in top_indices]


def retrieve(question, lang=None, mode=None):
    """Point d'entrée simple pour le reste du pipeline."""
    config = load_config()
    lang = lang or config["lang"]

    if mode is None:
        mode = config["rag"]["retrieval"].get(lang, "semantic")

    retriever = HybridRetriever(lang=lang)
    if mode == "hybrid":
        return retriever.retrieve_hybrid(question)
    elif mode == "semantic":
        return retriever.retrieve_semantic(question)
    elif mode == "bm25":
        return retriever.retrieve_bm25(question)
    else:
        raise ValueError(f"mode inconnu : {mode}")


if __name__ == "__main__":
    import sys
    question = sys.argv[1] if len(sys.argv) > 1 else "Quand vacciner mes vaches ?"
    resultats = retrieve(question)
    print(f"\nQuestion : {question}\n")
    for i, (doc, meta) in enumerate(resultats, 1):
        print(f"--- Résultat {i} (source: {meta['source']}) ---")
        print(doc[:200] + "...\n")