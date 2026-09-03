"""
app/gradio_app.py — Interface de démonstration visuelle.
"""

import gradio as gr
from pathlib import Path
import tempfile

from app.pipeline import process, load_config

config = load_config()

NOMS_LANGUE = {"fr": "français", "wo": "wolof", "ff": "pulaar"}
nom_langue = NOMS_LANGUE.get(config["lang"], config["lang"])


def traiter_audio(audio_path):
    """Fonction appelée par Gradio à chaque nouvel enregistrement/upload."""
    if audio_path is None:
        return "Aucun audio fourni.", None, "", ""

    resultat = process(audio_path, lang=config["lang"])

    if resultat["intent"]:
        intent_str = f"{resultat['intent']['intent']} (confiance: {resultat['intent']['confidence']:.2f})"
    else:
        intent_str = "NLU désactivé"
    latences_str = " | ".join(f"{k}: {v}s" for k, v in resultat["latences"].items())

    return (
        resultat["texte_transcrit"],
        resultat["audio_out_path"],
        intent_str,
        f"{resultat['reponse_texte']}\n\n--- Latences ---\n{latences_str}"
    )


demo = gr.Interface(
    fn=traiter_audio,
    inputs=gr.Audio(sources=["microphone", "upload"], type="filepath", label="Question vocale"),
    outputs=[
        gr.Textbox(label="Transcription (ASR)"),
        gr.Audio(label="Réponse vocale (TTS)"),
        gr.Textbox(label="Intent détecté (NLU)"),
        gr.Textbox(label="Réponse texte + latences"),
    ],
    title=f"Ñoo Far — Démo prototype ({nom_langue})",
    description="Pose une question sur l'élevage laitier, par micro ou fichier audio.",
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)