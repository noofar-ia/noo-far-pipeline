"""
tts/synthesize.py — Synthèse vocale via MMS-TTS.
"""

import yaml
from pathlib import Path
from transformers import VitsModel, AutoTokenizer
import torch
import soundfile as sf
import sys
import os


_models_cache = {}


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_tts_model(lang=None):
    config = load_config()
    lang = lang or config["lang"]
    if lang not in _models_cache:
        model_name = config["models"]["tts"][lang]
        device = "cuda" if torch.cuda.is_available() else "cpu"

        print(f"Chargement du modèle TTS ({lang}) : {model_name} sur {device}...")
        model = VitsModel.from_pretrained(model_name).to(device)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        _models_cache[lang] = (model, tokenizer, device)
    return _models_cache[lang]


def synthesize(texte, lang=None, output_path=None):
    """
    Synthétise un texte en audio.

    Args:
        texte (str) : le texte à synthétiser
        lang (str) : code langue, doit exister dans config.yaml (models.tts.<lang>)
        output_path (str | Path, optionnel) : si fourni, sauvegarde le WAV à ce chemin

    Returns:
        tuple (array numpy, sample_rate)
    """
    model, tokenizer, device = get_tts_model(lang)
    inputs = tokenizer(texte, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output = model(**inputs).waveform

    audio = output.cpu().numpy().squeeze()
    sr = model.config.sampling_rate

    if output_path:
        sf.write(str(output_path), audio, sr)

    return audio, sr


if __name__ == "__main__":
    texte = sys.argv[1] if len(sys.argv) > 1 else "Bonjour, ceci est un test."
    lang = sys.argv[2] if len(sys.argv) > 2 else None

    output_dir = Path(__file__).parent.parent / "data" / "tts_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "tts_test_output.wav"

    audio, sr = synthesize(texte, lang, output_path=output_path)
    print(f"Audio généré ({len(audio)/sr:.2f}s) → {output_path}")