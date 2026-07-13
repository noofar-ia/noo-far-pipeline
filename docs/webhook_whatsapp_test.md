# Réception WhatsApp — webhook de test (FastAPI + ngrok + Twilio)

> **Contexte.** Ce document décrit l'architecture et la méthodologie du premier test de réception WhatsApp de bout en bout, réalisé le 13 juillet 2026 (S1, J1). Il documente comment quatre outils s'articulent pour recevoir un vocal WhatsApp jusque dans le code Python du projet, la procédure pour le reproduire, les pièges rencontrés, et ce qui distingue ce prototype de test du futur `main.py` définitif.

---

## 1. Vue d'ensemble — le schéma d'architecture

```
┌─────────────┐     ┌─────────┐     ┌──────────────┐     ┌──────────┐     ┌─────────────┐
│  Éleveur     │     │ WhatsApp│     │   Twilio     │     │  ngrok   │     │  uvicorn    │
│  (WhatsApp)  │────▶│ réseau  │────▶│  (sandbox)   │────▶│ (tunnel) │────▶│  + FastAPI  │
└─────────────┘     └─────────┘     └──────────────┘     └──────────┘     └─────────────┘
                                            │                                      │
                                            │         URL publique                │
                                            │    https://xxxx.ngrok-free.dev       │
                                            │         /whatsapp (POST)             │
                                            └───────────────────────────────────────┘
                                                                                    │
                                                                                    ▼
                                                                          Téléchargement du
                                                                          fichier audio (.ogg)
                                                                          via l'API Twilio
```

**Le principe en une phrase :** un éleveur envoie un vocal sur WhatsApp → WhatsApp le transmet à Twilio → Twilio, configuré avec une URL webhook, envoie une requête HTTP POST vers cette URL → ngrok reçoit cette requête sur Internet et la redirige vers le serveur local → uvicorn fait tourner le code FastAPI qui traite la requête → le code télécharge le fichier audio réel depuis l'URL fournie par Twilio.

**Ce que chaque flèche représente :** WhatsApp → Twilio est géré entièrement par Twilio (aucun code de notre côté). Twilio → ngrok → uvicorn est le webhook, la partie qu'on construit et teste ici. La dernière étape (téléchargement du fichier) est un second appel HTTP, distinct du premier, fait par notre propre code vers l'API Twilio.

---

## 2. Les outils en jeu — rôle de chacun

### FastAPI — le framework applicatif

Définit **ce qu'il faut faire** quand une requête arrive sur une URL précise. Dans notre code :

```python
@app.post("/whatsapp")
async def receive_whatsapp(request: Request):
    ...
```

Ce décorateur dit : « toute requête POST sur `/whatsapp` doit être traitée par cette fonction ». FastAPI ne fait rien tourner tout seul — c'est une définition, pas un processus actif.

### uvicorn — le serveur qui fait vivre FastAPI

Ouvre réellement un port réseau, écoute les connexions, comprend le protocole HTTP, et appelle la bonne fonction FastAPI selon l'URL demandée. Sans uvicorn (ou un serveur ASGI équivalent), le code FastAPI reste une définition inerte.

```powershell
uvicorn app.webhook_test:app --host 0.0.0.0 --port 8000
```

`--host 0.0.0.0` écoute sur toutes les interfaces réseau de la machine (pas seulement `localhost`) — nécessaire pour que ngrok puisse s'y connecter.

### ngrok — le tunnel vers Internet

`localhost:8000` n'existe que pour la machine elle-même — invisible depuis Internet. ngrok crée un tunnel : une connexion sortante de la machine vers les serveurs ngrok, qui donne en retour une URL publique temporaire redirigeant vers le port local.

```powershell
ngrok http 8000
```

Génère une URL du type `https://alabaster-claw-voice.ngrok-free.dev` → `http://localhost:8000`.

**Point important : cette URL change à chaque nouveau lancement** (en version gratuite). Tant que le terminal ngrok reste ouvert sans interruption, l'URL reste stable.

### Twilio — l'intermédiaire avec WhatsApp

WhatsApp ne parle pas directement à notre code — Twilio fait le pont. Deux rôles :
- **Sortant** : notre code appelle l'API Twilio pour envoyer un message (`client.messages.create(...)`)
- **Entrant** : Twilio appelle **notre** URL (le webhook configuré) à chaque message reçu sur le numéro sandbox

Le webhook se configure sur `console.twilio.com`, section sandbox WhatsApp, champ **« When a message comes in »**, avec la méthode **POST**.

### Comment ils dépendent les uns des autres

```
FastAPI définit le comportement  →  sans effet seul
uvicorn exécute FastAPI          →  nécessite FastAPI, rend le serveur actif localement
ngrok expose uvicorn             →  nécessite qu'uvicorn tourne déjà, sinon rien à exposer
Twilio appelle ngrok             →  nécessite l'URL ngrok à jour, sinon la requête échoue
```

L'ordre de démarrage compte : uvicorn doit tourner **avant** ngrok (sinon ngrok expose un port vide), et l'URL ngrok doit être **à jour dans Twilio** avant d'envoyer un message de test.

---

## 3. Méthodologie pas à pas pour reproduire

### Préparation — un seul fichier

Créer `app/webhook_test.py` :

```python
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
```

### Étape 1 — Lancer uvicorn (Terminal 1)

```powershell
conda activate noofar
cd C:\dev\noo-far-pipeline
uvicorn app.webhook_test:app --host 0.0.0.0 --port 8000
```

Vérifier : `Uvicorn running on http://0.0.0.0:8000`.

### Étape 2 — Tester en local, avant tout le reste

```powershell
Invoke-WebRequest -Uri "http://localhost:8000"
```

Doit renvoyer `{"status": "Ñoo Far webhook actif"}`. Ce test élimine toute ambiguïté avant d'ajouter ngrok et Twilio à l'équation.

### Étape 3 — Lancer ngrok (Terminal 2, nouveau terminal)

```powershell
conda activate noofar
cd C:\dev\noo-far-pipeline
ngrok http 8000
```

Noter l'URL affichée sur la ligne `Forwarding`.

### Étape 4 — Tester le tunnel, avant Twilio

Ouvrir l'URL ngrok dans un navigateur (sans rien après le domaine). Doit à nouveau afficher `{"status": "Ñoo Far webhook actif"}` — cette fois via Internet, pas `localhost`. Ce test isole un éventuel problème de tunnel d'un éventuel problème de configuration Twilio.

### Étape 5 — Configurer le webhook Twilio

Sur `console.twilio.com`, section sandbox WhatsApp, champ **« When a message comes in »** :

```
https://[URL-NGROK]/whatsapp
```

Method : **POST**. Sauvegarder.

### Étape 6 — Test manuel du endpoint, avant le vrai message

Simuler ce que Twilio enverrait, sans passer par WhatsApp — isole un problème de code d'un problème Twilio :

```powershell
Invoke-WebRequest -Uri "https://[URL-NGROK]/whatsapp" -Method POST -Body @{From="whatsapp:+221000000000"; Body="test manuel"}
```

Vérifier dans le Terminal 1 (uvicorn) que le log « Message reçu » apparaît.

### Étape 7 — Le vrai test, depuis WhatsApp

Envoyer un message vocal, depuis le WhatsApp déjà connecté à la sandbox, au numéro sandbox Twilio.

Vérifier dans le Terminal 1 : le log complet avec `From`, `Média URL`, `Média type`, et la confirmation du téléchargement du fichier.

### Étape 8 — Vérifier le fichier reçu

```powershell
Get-Item data\Test_ffmpeg\recu_test.ogg | Select-Object Name, Length
python -c "import librosa; audio, sr = librosa.load('data/Test_ffmpeg/recu_test.ogg', sr=None); print(f'Durée : {len(audio)/sr:.2f}s, SR : {sr} Hz')"
```

---

## 4. Pièges rencontrés et leurs solutions

**`curl` dans PowerShell n'est pas le vrai curl.** C'est un alias de `Invoke-WebRequest`, avec une syntaxe différente (`-X`, `-d` ne fonctionnent pas). Deux solutions : utiliser la syntaxe PowerShell native (`Invoke-WebRequest -Method POST -Body @{...}`), ou forcer le vrai binaire avec `curl.exe` (Windows 10/11 récents l'embarquent).

**L'oubli du chemin `/whatsapp` dans l'URL Twilio.** Symptôme : `405 Method Not Allowed` dans les logs uvicorn, avec `POST /` au lieu de `POST /whatsapp`. Cause : le champ Twilio contenait seulement le domaine ngrok, sans le chemin de la route. Toujours vérifier le contenu exact du champ, pas seulement qu'il est rempli.

**L'URL ngrok change à chaque redémarrage (version gratuite).** Si le terminal ngrok est fermé puis rouvert, l'ancienne URL cesse de fonctionner et Twilio doit être reconfiguré avec la nouvelle. Pour un développement suivi, garder le terminal ngrok ouvert en continu plutôt que de le relancer à chaque session.

**Sauvegarder après modification dans Twilio.** La console Twilio ne prend effet qu'après un clic explicite sur « Save » — une URL modifiée mais non sauvegardée continue de pointer vers l'ancienne configuration.

---

## 5. Limites de cette configuration — ce qui doit changer pour la suite

`webhook_test.py` est un **prototype de validation**, pas le `main.py` définitif. Plusieurs éléments manquent avant une version production-ready :

**Validation de sécurité Twilio.** N'importe qui connaissant l'URL ngrok peut actuellement envoyer une requête POST à `/whatsapp` et se faire passer pour Twilio (comme le test manuel de l'étape 6 le montre). Twilio fournit un mécanisme de signature (`X-Twilio-Signature`) à vérifier pour s'assurer que la requête vient bien de leurs serveurs — absent ici, indispensable en production.

**Gestion d'erreurs.** Le code actuel suppose que tout se passe bien (téléchargement du média, écriture du fichier). Aucun `try/except`, aucune réponse d'erreur explicite à Twilio en cas de problème.

**Pas d'intégration au pipeline réel.** Le fichier reçu est juste sauvegardé sur disque — il n'est pas encore passé à `ffmpeg` (conversion), ni à Whisper (transcription), ni au reste de la chaîne ASR → NLU → RAG → TTS. C'est le travail des jours suivants de S1 (J4-J5 : pipeline bout en bout).

**ngrok n'est pas une solution de production.** URL instable, dépendante d'un terminal ouvert sur une machine de développement. La question du vrai déploiement serveur est volontairement différée à la phase MVP (voir `JOURNAL_DECISIONS.md`, entrée du 13 juillet 2026).

**Nommage temporaire.** `webhook_test.py` devra être renommé/fusionné dans `app/main.py`, la structure définitive du service.

---

## Statut

✅ **Test de bout en bout réussi** le 13 juillet 2026 — envoi WhatsApp → Twilio → ngrok → uvicorn → FastAPI → téléchargement du fichier audio (20 971 octets, format `audio/ogg`) confirmé fonctionnel avec un vrai message vocal.
