"""
app/pipeline.py — Orchestration complète : audio -> ASR -> NLU -> RAG+LLM -> TTS -> audio.
"""

import subprocess
from pathlib import Path
import time

from asr.transcribe import transcribe
from nlu.client import parse_intent
from rag.retriever import retrieve
from rag.generator import generate
from tts.synthesize import synthesize


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
        dict : {audio_out_path, texte_transcrit, intent, reponse_texte, latences}
    """
    t0 = time.time()
    audio_in_path = Path(audio_in_path)

    wav_path = audio_in_path.with_suffix(".16k.wav")
    convert_to_wav16k(audio_in_path, wav_path)
    t1 = time.time()

    texte = transcribe(wav_path, lang=lang)
    t2 = time.time()

    intent_info = parse_intent(texte)
    t3 = time.time()

    passages = retrieve(texte, lang=lang, mode="semantic")
    reponse_texte = generate(texte, passages)
    t4 = time.time()

    audio_out_path = audio_in_path.parent / f"{audio_in_path.stem}_reponse.wav"
    synthesize(reponse_texte, lang=lang, output_path=audio_out_path)
    t5 = time.time()

    return {
        "audio_out_path": str(audio_out_path),
        "texte_transcrit": texte,
        "intent": intent_info,
        "reponse_texte": reponse_texte,
        "latences": {
            "conversion": round(t1 - t0, 2),
            "asr": round(t2 - t1, 2),
            "nlu": round(t3 - t2, 2),
            "rag_llm": round(t4 - t3, 2),
            "tts": round(t5 - t4, 2),
            "total": round(t5 - t0, 2),
        }
    }