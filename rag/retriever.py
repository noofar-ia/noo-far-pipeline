"""
rag/retriever.py — Récupération hybride BM25 + embeddings.
"""

import yaml
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi


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

        client = chromadb.PersistentClient(path=str(Path(__file__).parent / "chroma"))
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
        self.collection = client.get_collection(
            name=collection_name or f"fiches_{lang}",
            embedding_function=embedding_fn
         )

        # Récupérer tous les documents pour construire l'index BM25
        all_docs = self.collection.get()
        self.documents = all_docs["documents"]
        self.metadatas = all_docs["metadatas"]
        self.ids = all_docs["ids"]
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
        """Fusionne sémantique + BM25, dédoublonne, garde les k meilleurs."""
        k = k or self.top_k
        semantic = self.retrieve_semantic(question, k=k)
        bm25 = self.retrieve_bm25(question, k=k)

        seen = set()
        combined = []
        # Alterner pour donner une chance égale aux deux méthodes
        for sem, lex in zip(semantic, bm25):
            for doc, meta in (sem, lex):
                key = meta["source"] + str(meta["chunk_index"])
                if key not in seen:
                    seen.add(key)
                    combined.append((doc, meta))
        return combined[:k]


def retrieve(question, lang= None, mode="hybrid"):
    """Point d'entrée simple pour le reste du pipeline."""
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