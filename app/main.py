import yaml
from pathlib import Path
from fastapi import FastAPI, Request
from app.channels.telegram import TelegramChannel
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
    """
    Logique métier commune, indépendante du canal.
    TODO : brancher ffmpeg → transcribe.py → NLU → RAG → TTS (J3-J4).
    Pour l'instant : accusé de réception simple.
    """
    if message.audio_path:
        return f"Audio reçu : {message.audio_path}", None
    return f"Texte reçu : {message.text}", None


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