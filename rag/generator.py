"""
rag/generator.py — Génération de réponse via LLM, à partir de passages RAG.
"""

import yaml
from pathlib import Path
from transformers import pipeline
import torch

_llm_cache = {}


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_llm():
    if "llm" not in _llm_cache:
        device = 0 if torch.cuda.is_available() else -1
        model_name = "meta-llama/Llama-3.2-3B-Instruct"  # confirmé fonctionnel en J3
        print(f"Chargement du LLM : {model_name} sur {'GPU' if device == 0 else 'CPU'}...")
        _llm_cache["llm"] = pipeline(
            "text-generation",
            model=model_name,
            device=device,
            torch_dtype=torch.float16 if device == 0 else torch.float32
        )
    return _llm_cache["llm"]


def build_prompt(question, passages):
    contexte = "\n\n".join(f"[Extrait {i+1}] {doc}" for i, (doc, meta) in enumerate(passages))
    return f"""Tu es un assistant vocal qui aide des éleveurs laitiers sénégalais.
Réponds à la question UNIQUEMENT à partir des extraits fournis ci-dessous.
Si l'information n'est pas dans les extraits, dis clairement que tu ne sais pas — n'invente rien.
Réponds en français, de façon concise et orale (pas de listes à puces, une réponse qu'on peut lire à voix haute).

Extraits :
{contexte}

Question : {question}

Réponse :"""


def generate(question, passages):
    """Génère une réponse en langage naturel à partir de la question et des passages récupérés."""
    llm = get_llm()
    prompt = build_prompt(question, passages)
    result = llm(prompt, max_new_tokens=150, temperature=0.3, do_sample=True)
    return result[0]["generated_text"][len(prompt):].strip()