"""
app/pipeline.py — Orchestration complète : audio -> ASR -> NLU -> RAG+LLM -> frontend -> TTS -> audio.
"""

import subprocess
from pathlib import Path
import time

import yaml

from asr.transcribe import transcribe
from nlu.client import parse_intent
from rag.retriever import retrieve
from rag.generator import generate
from tts.frontend import preparer_pour_tts
from tts.synthesize import synthesize


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def convert_to_wav16k(input_path, output_path):
    """Conversion via ffmpeg — préinstallé sur Codespace, pas de build statique nécessaire ici."""
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path), "-ar", "16000", "-ac", "1", str(output_path)],
        check=True,
        capture_output=True
    )


def process(audio_in_path, lang="fr"):
    """
    Traite un audio entrant de bout en bout et retourne le chemin de l'audio de réponse.

    Args:
        audio_in_path (str | Path) : chemin du fichier audio reçu (n'importe quel format ffmpeg)
        lang (str) : langue à utiliser pour ASR/RAG/TTS

    Returns:
        dict : {audio_out_path, texte_transcrit, intent, reponse_texte, texte_tts, latences}
    """
    config = load_config()
    t0 = time.time()
    audio_in_path = Path(audio_in_path)

    # 1. Conversion
    wav_path = audio_in_path.with_suffix(".16k.wav")
    convert_to_wav16k(audio_in_path, wav_path)
    t1 = time.time()

    # 2. ASR
    texte = transcribe(wav_path, lang=lang)
    t2 = time.time()

    # 3. NLU — optionnel (B). intent_info non utilisé pour router ; modèle Rasa
    #    entraîné en FR, donc bruit sur du wolof. Désactivable par config.
    if config.get("nlu", {}).get("enabled", False):
        intent_info = parse_intent(texte)
    else:
        intent_info = None
    t3 = time.time()

    # 4. RAG — mode de retrieval par langue (G), lang transmis à generate (D)
    mode = config["rag"]["retrieval"][lang]
    passages = retrieve(texte, lang=lang, mode=mode)
    reponse_texte = generate(texte, passages, lang=lang)
    t4 = time.time()

    # 5. Frontend texte (H) — verbalisation nombres, lexique, .lower() Kiriku.
    #    Entre generate et synthesize : ce que le TTS ne sait pas prononcer
    #    est transformé ici.
    texte_tts = preparer_pour_tts(reponse_texte, lang=lang, modele=config["models"]["tts"][lang])
    t5 = time.time()

    # 6. TTS
    audio_out_path = audio_in_path.parent / f"{audio_in_path.stem}_reponse.wav"
    synthesize(texte_tts, lang=lang, output_path=audio_out_path)
    t6 = time.time()

    return {
        "audio_out_path": str(audio_out_path),
        "texte_transcrit": texte,
        "intent": intent_info,
        "reponse_texte": reponse_texte,
        "texte_tts": texte_tts,          # ce que le frontend a produit — pour le diagnostic
        "latences": {
            "conversion": round(t1 - t0, 2),
            "asr": round(t2 - t1, 2),
            "nlu": round(t3 - t2, 2),
            "rag_llm": round(t4 - t3, 2),
            "frontend": round(t5 - t4, 2),
            "tts": round(t6 - t5, 2),
            "total": round(t6 - t0, 2),
        }
    }