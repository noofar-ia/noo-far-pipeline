"""
rag/generator.py — Génération de réponse via LLM, à partir de passages RAG.
"""

import gc
import yaml
from pathlib import Path
from transformers import pipeline
import torch

_llm_cache = {}


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_llm(lang="fr"):
    """Charge (ou récupère du cache) le LLM pour la langue donnée.
    Le modèle est lu dans config.yaml (models.llm.<lang>), cache clé par nom
    de modèle : deux langues pointant sur le même modèle le partagent."""
    config = load_config()
    model_name = config["models"]["llm"][lang]

    if model_name not in _llm_cache:
        device = 0 if torch.cuda.is_available() else -1
        print(f"Chargement du LLM ({lang}) : {model_name} sur {'GPU' if device == 0 else 'CPU'}...")
        _llm_cache[model_name] = pipeline(
            "text-generation",
            model=model_name,
            device=device,
            torch_dtype=torch.float16 if device == 0 else torch.float32
        )
    return _llm_cache[model_name]


def unload_llm(model_name=None):
    """Libère un modèle précis, ou tous si model_name est None.
    Nécessaire pour comparer deux LLM sans saturer la VRAM (Whisper large
    est déjà chargé en amont)."""
    if model_name:
        _llm_cache.pop(model_name, None)
    else:
        _llm_cache.clear()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


PROMPTS = {
    "fr": """Tu es un assistant vocal qui aide des éleveurs laitiers sénégalais.
Réponds à la question UNIQUEMENT à partir des extraits fournis ci-dessous.
Si l'information n'est pas dans les extraits, dis clairement que tu ne sais pas — n'invente rien.
Réponds en français, de façon concise et orale (pas de listes à puces, une réponse qu'on peut lire à voix haute).

Extraits :
{contexte}

Question : {question}

Réponse :""",

    "wo": """Waxkat baat nga di jàppale baykati meew yi waa Senegal.
Tontu laaj bi ci liñu bind ci suuf REKK.
Sudee leeral yi nekkul ci pàcc yi, wax leen bu baax ni xamoo leen, bul xalaat dara.
Tontu ci wolof, ci anam wu gàtt te ànd ak waxtaan (amul poñ bullet; tontu bu man a jàng ak baat bu kawe).

Pàcc yi :
{contexte}

Laaj bi : {question}

Tontu :""",
}


def build_prompt(question, passages, lang="fr"):
    contexte = "\n\n".join(f"[Extrait {i+1}] {doc}" for i, (doc, meta) in enumerate(passages))
    gabarit = PROMPTS.get(lang, PROMPTS["fr"])
    return gabarit.format(contexte=contexte, question=question)


def generate(question, passages, lang="fr"):
    """Génère une réponse en langage naturel à partir de la question et des passages récupérés."""
    llm = get_llm(lang)
    prompt = build_prompt(question, passages, lang=lang)
    result = llm(prompt, max_new_tokens=150, temperature=0.3, do_sample=True)
    return result[0]["generated_text"][len(prompt):].strip()