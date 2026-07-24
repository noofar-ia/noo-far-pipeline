"""
asr/transcribe.py — Transcription audio via Whisper.

Fonction principale : transcribe(wav_path, lang) -> texte
Le modèle utilisé est déterminé par config/config.yaml (models.asr.<lang>).
"""

import yaml
from pathlib import Path
from transformers import pipeline
import torch

_models_cache = {}


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_asr_model(lang="fr"):
    """Charge (ou récupère du cache) le modèle ASR pour la langue donnée."""
    if lang not in _models_cache:
        config = load_config()
        model_name = config["models"]["asr"][lang]
        device = 0 if torch.cuda.is_available() else -1

        print(f"Chargement du modèle ASR ({lang}) : {model_name} sur {'GPU' if device == 0 else 'CPU'}...")
        _models_cache[lang] = pipeline(
            "automatic-speech-recognition",
            model=model_name,
            device=device
        )
    return _models_cache[lang]


def transcribe(wav_path, lang="fr"):
    """
    Transcrit un fichier audio WAV en texte.

    Args:
        wav_path (str | Path) : chemin vers le fichier audio (WAV, idéalement 16kHz mono)
        lang (str) : code langue ("fr", "wo"...), doit exister dans config.yaml

    Returns:
        str : le texte transcrit

    Note : return_timestamps=True est nécessaire pour les audios de plus de 30s
    (sinon Whisper lève une ValueError en mode long-form). Effet de bord :
    peut favoriser les hallucinations sur silences prolongés — non traité ici,
    voir trim_silence() prévu à la mise au propre.
    """
    asr = get_asr_model(lang)
    result = asr(str(wav_path), return_timestamps=True)
    return result["text"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage : python transcribe.py chemin/vers/audio.wav [lang=fr]")
        sys.exit(1)

    wav_path = sys.argv[1]
    lang = sys.argv[2] if len(sys.argv) > 2 else "fr"

    texte = transcribe(wav_path, lang)
    print(f"\nTranscription ({lang}) : {texte}")