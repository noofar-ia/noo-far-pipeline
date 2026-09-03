"""
tts/synthesize.py — Synthèse vocale, routée par famille de modèle.

- MMS-TTS (facebook/mms-tts-*) : VitsModel de transformers.
- Kiriku (AIHubSN/Kiriku-Wolof-TTS) : VITS Coqui, via coqui-tts + Synthesizer.
Contrat de sortie identique pour les deux : (audio: np.ndarray, sr: int).
"""

import gc
import yaml
from pathlib import Path
import torch
import numpy as np
import soundfile as sf
import sys

_models_cache = {}


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ── Backend MMS-TTS (transformers) ───────────────────────────────
def _load_mms(model_name):
    from transformers import VitsModel, AutoTokenizer
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Chargement TTS MMS : {model_name} sur {device}...")
    model = VitsModel.from_pretrained(model_name).to(device)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return ("mms", model, tokenizer, device)


def _synth_mms(entry, texte):
    _, model, tokenizer, device = entry
    inputs = tokenizer(texte, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        output = model(**inputs).waveform
    audio = output.cpu().numpy().squeeze()
    return audio, model.config.sampling_rate


# ── Backend Kiriku (coqui-tts) ───────────────────────────────────
def _load_kiriku(model_name):
    # Shim : isin_mps_friendly retiré en transformers v5, importé par coqui-tts (chemin xTTS).
    import transformers.pytorch_utils as pu
    if not hasattr(pu, "isin_mps_friendly"):
        pu.isin_mps_friendly = lambda elements, test_elements: torch.isin(elements, test_elements)

    from huggingface_hub import snapshot_download
    from TTS.utils.synthesizer import Synthesizer

    ckpt = snapshot_download(repo_id=model_name)
    use_cuda = torch.cuda.is_available()
    print(f"Chargement TTS Kiriku : {model_name} sur {'cuda' if use_cuda else 'cpu'}...")
    synth = Synthesizer(
        tts_checkpoint=str(Path(ckpt) / "model.pth"),
        tts_config_path=str(Path(ckpt) / "config.json"),
        use_cuda=use_cuda,
    )
    return ("kiriku", synth)


def _synth_kiriku(entry, texte):
    _, synth = entry
    # .lower() est déjà appliqué par tts/frontend.py en amont ; ne pas le refaire ici.
    wav = synth.tts(texte)
    audio = np.asarray(wav, dtype=np.float32)
    return audio, synth.output_sample_rate


# ── Routage ──────────────────────────────────────────────────────
def get_tts_model(lang=None):
    config = load_config()
    lang = lang or config["lang"]
    if lang not in _models_cache:
        model_name = config["models"]["tts"][lang]
        if "kiriku" in model_name.lower():
            _models_cache[lang] = _load_kiriku(model_name)
        else:
            _models_cache[lang] = _load_mms(model_name)
    return _models_cache[lang]


def synthesize(texte, lang=None, output_path=None):
    """
    Synthétise un texte en audio.

    Returns:
        tuple (array numpy float32, sample_rate int)
    """
    entry = get_tts_model(lang)
    backend = entry[0]

    if backend == "kiriku":
        audio, sr = _synth_kiriku(entry, texte)
    else:
        audio, sr = _synth_mms(entry, texte)

    if output_path:
        sf.write(str(output_path), audio, sr)

    return audio, sr


def unload_tts(lang=None):
    """Libère le modèle TTS d'une langue précise, ou tous si lang est None."""
    if lang:
        _models_cache.pop(lang, None)
    else:
        _models_cache.clear()
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    texte = sys.argv[1] if len(sys.argv) > 1 else "Bonjour, ceci est un test."
    lang = sys.argv[2] if len(sys.argv) > 2 else None

    output_dir = Path(__file__).parent.parent / "data" / "tts_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "tts_test_output.wav"

    audio, sr = synthesize(texte, lang, output_path=output_path)
    print(f"Audio généré ({len(audio)/sr:.2f}s) → {output_path}")