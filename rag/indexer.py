"""
rag/indexer.py — Indexation des fiches dans ChromaDB.
"""

import yaml
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def chunk_text(text, chunk_size=400, overlap=50):
    """Découpe un texte en chunks avec chevauchement, approximation par mots."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks


def build_index(lang=None, collection_name=None):
    """Lit les fiches, les découpe, les indexe dans ChromaDB."""
    config = load_config()
    lang = lang or config["lang"]  # utilise la langue active de config.yaml par défaut
    embedding_model = config["rag"]["embedding_model"]

    project_root = Path(__file__).parent.parent
    fiches_dir = project_root / config["rag"]["fiches_dir"] / lang

    fiches = list(fiches_dir.glob("*.md")) + list(fiches_dir.glob("*.txt"))
    if not fiches:
        raise FileNotFoundError(f"Aucune fiche trouvée dans {fiches_dir}")

    client = chromadb.PersistentClient(path=str(project_root / "rag" / "chroma"))
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)

    collection_name = collection_name or f"fiches_{lang}"
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(name=collection_name, embedding_function=embedding_fn)

    documents, metadatas, ids = [], [], []
    for fiche_path in fiches:
        text = fiche_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            documents.append(chunk)
            metadatas.append({"source": fiche_path.name, "chunk_index": i})
            ids.append(f"{fiche_path.stem}_{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Indexé : {len(documents)} chunks depuis {len(fiches)} fiches dans la collection '{collection_name}'")
    return collection


if __name__ == "__main__":
    build_index()