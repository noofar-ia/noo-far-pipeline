"""
prepare_audio.py — étape de production du pipeline ASR Ñoo Far.

Convertit les audios bruts (.wav/.m4a/…) en 16 kHz mono, les transcrit avec
Whisper, et écrit le résultat dans un CSV. À lancer une fois par lot de
fichiers ; le notebook d'analyse consomme le CSV produit — il ne retranscrit
pas.

Idempotent : une conversion déjà faite est sautée ; le CSV n'est réécrit que
s'il manque (ou avec --force). Le CSV est suffixé par le nom du modèle, pour
qu'un changement de modèle ne serve pas un cache périmé.

Usage:
    python asr/prepare_audio.py
    python asr/prepare_audio.py --force                       # retranscrit
    python asr/prepare_audio.py --model openai/whisper-large-v3
    python asr/prepare_audio.py --skip-transcription          # conversion seule
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import librosa
import pandas as pd

# Racine du dépôt = parent du dossier asr/ qui contient ce script.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "test_asr_fr"

# Extensions considérées comme des sources audio à convertir.
AUDIO_EXTS = {".wav", ".m4a", ".mp3", ".flac", ".ogg"}


def fichiers_sources(audio_dir: Path) -> list[Path]:
    """Audios bruts du dossier — tout sauf les sorties *_16k.wav déjà générées."""
    return sorted(
        p for p in audio_dir.iterdir()
        if p.suffix.lower() in AUDIO_EXTS and not p.stem.endswith("_16k")
    )


def convertir_en_16k(audio_dir: Path) -> None:
    """Convertit chaque source en {stem}_16k.wav (16 kHz mono). Saute l'existant."""
    if shutil.which("ffmpeg") is None:
        sys.exit("ffmpeg introuvable dans le PATH — installe-le avant de lancer.")

    sources = fichiers_sources(audio_dir)
    if not sources:
        print("  Aucune source à convertir.")
        return

    for src in sources:
        dst = audio_dir / f"{src.stem}_16k.wav"
        if dst.exists():
            print(f"  [saut]    {dst.name}")
            continue
        print(f"  [convert] {src.name} -> {dst.name}")
        subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error",
             "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)],
            check=True,
        )


def transcrire(audio_dir: Path, model_name: str, force: bool = False) -> Path:
    """Transcrit les *_16k.wav avec Whisper et écrit un CSV suffixé par le modèle."""
    slug = model_name.split("/")[-1]
    csv_path = audio_dir / f"transcriptions_{slug}_fr.csv"

    if csv_path.exists() and not force:
        print(f"  {csv_path.name} déjà présent — --force pour retranscrire.")
        return csv_path

    audio_files = sorted(audio_dir.glob("*_16k.wav"))
    if not audio_files:
        sys.exit(f"Aucun fichier *_16k.wav dans {audio_dir} — lance la conversion d'abord.")

    # Imports lourds différés : on ne les paie que si on transcrit vraiment.
    import torch
    from transformers import pipeline

    device = 0 if torch.cuda.is_available() else -1  # entier attendu par le pipeline
    print(f"  Chargement de {model_name} (device={device})…")
    asr = pipeline("automatic-speech-recognition", model=model_name, device=device)

    lignes = []
    for path in audio_files:
        print(f"  [asr] {path.name}")
        res = asr(str(path), return_timestamps=True)
        lignes.append({
            "fichier": path.name,
            "transcription": res["text"],
            "duree_s": round(librosa.get_duration(path=str(path)), 2),
        })

    df = pd.DataFrame(lignes)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"  Écrit : {csv_path.name} ({len(df)} lignes)")
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prépare les audios bruts pour l'analyse ASR (conversion + transcription)."
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help=f"dossier audio (défaut : {DEFAULT_DATA_DIR})")
    parser.add_argument("--model", default="openai/whisper-medium",
                        help="modèle Whisper (défaut : openai/whisper-medium)")
    parser.add_argument("--force", action="store_true",
                        help="retranscrit même si le CSV existe déjà")
    parser.add_argument("--skip-transcription", action="store_true",
                        help="ne fait que la conversion 16 kHz")
    args = parser.parse_args()

    audio_dir: Path = args.data_dir
    if not audio_dir.is_dir():
        sys.exit(f"Dossier introuvable : {audio_dir}")

    print(f"== Conversion 16 kHz mono — {audio_dir} ==")
    convertir_en_16k(audio_dir)

    if args.skip_transcription:
        print("Transcription sautée (--skip-transcription).")
        return

    print(f"== Transcription — {args.model} ==")
    transcrire(audio_dir, args.model, force=args.force)
    print("Terminé.")


if __name__ == "__main__":
    main()