"""
rag/generator.py — Génération de réponse via LLM, à partir de passages RAG.
"""

import gc
import yaml
from pathlib import Path
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
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
    Vide _llm_cache (chemin pipeline() générique) et _oolel_cache (chemin
    Oolel dédié au wolof) — un seul point d'entrée pour décharger le LLM
    quel que soit le chemin emprunté par generate()."""
    if model_name:
        _llm_cache.pop(model_name, None)
        _oolel_cache.pop(model_name, None)
    else:
        _llm_cache.clear()
        _oolel_cache.clear()
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
}


LABEL_EXTRAIT = {"fr": "Extrait", "wo": "Pàcc"}


def build_prompt(question, passages, lang="fr"):
    label = LABEL_EXTRAIT.get(lang, "Extrait")
    contexte = "\n\n".join(f"[{label} {i+1}] {doc}" for i, (doc, meta) in enumerate(passages))
    gabarit = PROMPTS.get(lang, PROMPTS["fr"])
    return gabarit.format(contexte=contexte, question=question)


OOLEL_MODEL_NAME = "soynade-research/Oolel-v0.1"

_oolel_cache = {}
_system_wo_cache = None


def _load_system_wo():
    """Charge SYSTEM_WO depuis rag/prompts/system_wo.txt (une seule fois, mis en cache)."""
    global _system_wo_cache
    if _system_wo_cache is None:
        system_wo_path = Path(__file__).parent / "prompts" / "system_wo.txt"
        if not system_wo_path.exists():
            raise FileNotFoundError(f"SYSTEM_WO introuvable : {system_wo_path}")
        _system_wo_cache = system_wo_path.read_text(encoding="utf-8").strip()
    return _system_wo_cache


def get_oolel():
    """Charge (ou récupère du cache) Oolel-v0.1 et son tokenizer, dédiés au wolof."""
    if OOLEL_MODEL_NAME not in _oolel_cache:
        print(f"Chargement d'Oolel : {OOLEL_MODEL_NAME}...")
        tokenizer = AutoTokenizer.from_pretrained(OOLEL_MODEL_NAME)
        model = AutoModelForCausalLM.from_pretrained(
            OOLEL_MODEL_NAME, dtype=torch.float16, device_map="auto"
        )
        _oolel_cache[OOLEL_MODEL_NAME] = (model, tokenizer)
    return _oolel_cache[OOLEL_MODEL_NAME]


def generate_wo(question, passages):
    """Génère une réponse en wolof via Oolel-v0.1 (chat template SYSTEM_WO + gabarit user validé)."""
    model, tokenizer = get_oolel()
    system_wo = _load_system_wo()
    contexte = "\n\n".join(doc for doc, meta in passages)

    messages = [
        {"role": "system", "content": system_wo},
        {"role": "user", "content": f"Xibaar bi:\n{contexte}\n\nLaaj bi: {question}"},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(**inputs, max_new_tokens=384, do_sample=False)
    tokens_generes = outputs[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(tokens_generes, skip_special_tokens=True).strip()


def generate(question, passages, lang="fr"):
    """Génère une réponse en langage naturel à partir de la question et des passages récupérés."""
    if lang == "wo":
        return generate_wo(question, passages)
    llm = get_llm(lang)
    prompt = build_prompt(question, passages, lang=lang)
    result = llm(prompt, max_new_tokens=150, temperature=0.3, do_sample=True)
    return result[0]["generated_text"][len(prompt):].strip()