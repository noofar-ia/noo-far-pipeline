# app/channels/telegram.py
import os
import requests
from .base import MessagingChannel, IncomingMessage

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


class TelegramChannel(MessagingChannel):
    async def parse_webhook(self, request) -> IncomingMessage:
        data = await request.json()
        message = data.get("message", {})
        from_id = str(message.get("chat", {}).get("id"))
        text = message.get("text")

        audio_path = None
        voice = message.get("voice")
        if voice:
            file_id = voice["file_id"]
            audio_path = await self._download_voice(file_id)

        return IncomingMessage(from_id=from_id, text=text, audio_path=audio_path)

    async def _download_voice(self, file_id):
        # Étape 1 : obtenir le chemin du fichier
        resp = requests.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id})
        print("DEBUG getFile response:", resp.status_code, resp.json())  # ligne ajoutée
        file_path = resp.json()["result"]["file_path"]

        # Étape 2 : télécharger le fichier réel
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}"
        audio_data = requests.get(file_url).content

        local_path = f"data/telegram_audio/{file_id}.ogg"
        os.makedirs("data/telegram_audio", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(audio_data)
        return local_path

    async def send_message(self, to: str, text: str = None, audio_path: str = None):
        if text:
            requests.post(f"{TELEGRAM_API}/sendMessage", json={"chat_id": to, "text": text})
        if audio_path:
            with open(audio_path, "rb") as f:
                requests.post(f"{TELEGRAM_API}/sendVoice", data={"chat_id": to}, files={"voice": f})