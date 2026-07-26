from dotenv import load_dotenv
load_dotenv("config/.env")

import yaml
from pathlib import Path
from fastapi import FastAPI, Request
from app.channels.telegram import TelegramChannel
from app.pipeline import process
# from app.channels.whatsapp import WhatsAppChannel  # à activer en déploiement


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()
app = FastAPI()

telegram = TelegramChannel() if config["messaging"]["telegram"]["enabled"] else None
# whatsapp = WhatsAppChannel() if config["messaging"]["whatsapp"]["enabled"] else None


async def process_message(message):
    """Logique métier commune, appelle le pipeline complet si un audio est présent."""
    if message.audio_path:
        resultat = process(message.audio_path, lang=config["lang"])
        print(f"[pipeline] intent={resultat['intent']['intent']} "
              f"latence_totale={resultat['latences']['total']}s")
        return resultat["reponse_texte"], resultat["audio_out_path"]

    return "Envoie-moi un message vocal pour que je puisse t'aider.", None


@app.post("/telegram")
async def telegram_webhook(request: Request):
    if not telegram:
        return {"error": "Telegram non activé dans config.yaml"}

    message = await telegram.parse_webhook(request)
    response_text, response_audio = await process_message(message)
    await telegram.send_message(message.from_id, text=response_text, audio_path=response_audio)
    return {"ok": True}


# @app.post("/whatsapp")
# async def whatsapp_webhook(request: Request):
#     message = await whatsapp.parse_webhook(request)
#     ... même logique, juste l'adaptateur change


@app.get("/")
async def health_check():
    return {"status": "Ñoo Far actif", "canal": config["messaging"]["provider"]}