from fastapi import FastAPI, Request
from app.channels.telegram import TelegramChannel
# from app.channels.whatsapp import WhatsAppChannel  # à activer en déploiement

app = FastAPI()
telegram = TelegramChannel()

@app.post("/telegram")
async def telegram_webhook(request: Request):
    message = await telegram.parse_webhook(request)
    # → ici, appel de la logique métier commune (pipeline.py), identique pour tous les canaux
    response_text, response_audio = await process_message(message)
    await telegram.send_message(message.from_id, text=response_text, audio_path=response_audio)
    return {"ok": True}

# @app.post("/whatsapp")
# async def whatsapp_webhook(request: Request):
#     message = await whatsapp.parse_webhook(request)
#     ... même logique, juste l'adaptateur change