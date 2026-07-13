from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import os
from dotenv import load_dotenv
import requests

load_dotenv("config/.env")

app = FastAPI()

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")


@app.post("/whatsapp")
async def receive_whatsapp(request: Request):
    form = await request.form()
    from_number = form.get("From")
    body = form.get("Body")
    media_url = form.get("MediaUrl0")
    media_type = form.get("MediaContentType0")

    print(f"\n--- Message reçu ---")
    print(f"De : {from_number}")
    print(f"Texte : {body}")
    print(f"Média URL : {media_url}")
    print(f"Média type : {media_type}")

    if media_url:
        response = requests.get(media_url, auth=(ACCOUNT_SID, AUTH_TOKEN))
        with open("data/Test_ffmpeg/recu_test.ogg", "wb") as f:
            f.write(response.content)
        print(f"Fichier audio téléchargé : data/Test_ffmpeg/recu_test.ogg ({len(response.content)} octets)")

    return PlainTextResponse("", status_code=200)


@app.get("/")
async def health_check():
    return {"status": "Ñoo Far webhook actif"}