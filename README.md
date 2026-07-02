# Ñoo Far — Pipeline

**Assistant vocal multilingue (wolof, pulaar) pour les éleveurs laitiers du nord du Sénégal.**

Ñoo Far permet à un éleveur de poser une question vocale — en wolof ou en pulaar — sur la conduite de son élevage laitier (santé animale, alimentation, reproduction, production…) et de recevoir une réponse vocale, adossée aux fiches techniques de l'ISRA. L'objectif : rendre l'information agricole accessible dans les langues réellement parlées sur le terrain, y compris pour des locuteurs peu à l'aise avec l'écrit ou le français.

Projet porté par **Banaan Food**, en partenariat avec **ISRA-LNERV** (garant scientifique) et **UFR CRAC-UGB** (garant linguistique). Candidat à une bourse **Masakhane**.

> ⚠️ **État du projet : prototype en construction.** L'infrastructure et la configuration sont en place ; les briques applicatives (`asr`, `nlu`, `rag`, `tts`, `app`) sont à l'état de squelette. Premier prototype français visé pour la mi-juillet, baseline wolof pour début août.

---

## Architecture du pipeline

Le traitement d'une requête suit une chaîne de quatre étapes :

```
Audio (WhatsApp)
    │
    ▼
[ ASR ]   Whisper          → transcription du wolof/pulaar en texte
    │
    ▼
[ NLU ]   Rasa (service)   → intention de l'éleveur + entités
    │
    ▼
[ RAG ]   ChromaDB + BM25  → fiches ISRA pertinentes
    │
    ▼
[ TTS ]   MMS-TTS          → réponse vocale
    │
    ▼
Réponse vocale (WhatsApp)
```

Le **débruitage** (Resemble Enhance) sert uniquement à la préparation du corpus, hors du pipeline temps réel : en production, Whisper reçoit l'audio brut.

L'étape **NLU tourne comme un service séparé** (Rasa, environnement distinct) que le pipeline interroge en HTTP — voir [`nlu/README.md`](nlu/README.md).

---

## Installation

> **Prérequis : Python 3.10**, ffmpeg, git.
> Cette section installe l'environnement du **pipeline** (ASR, RAG, TTS, app).
> L'étape NLU tourne dans un service Rasa séparé, dans son propre
> environnement — voir [`nlu/README.md`](nlu/README.md).

```bash
# Cloner le dépôt
git clone https://github.com/noofar-ia/noo-far-pipeline
cd noo-far-pipeline

# Environnement (conda recommandé)
conda create -n noofar python=3.10 -y
conda activate noofar

# ffmpeg — selon l'OS :
conda install -c conda-forge ffmpeg      # portable Windows / Mac / Linux
# ou : sudo apt-get update && sudo apt-get install ffmpeg -y   (Ubuntu/Colab)

# Dépendances Python
pip install --upgrade pip
pip install -r requirements.lock.txt     # versions figées (reproduction à l'identique)

# Configuration
cp config/.env.example config/.env       # puis éditer avec les tokens (HF, Twilio)
```

> `requirements.txt` = référence lisible et commentée.
> `requirements.lock.txt` = versions exactes, à utiliser pour reproduire l'environnement.

---

## Lancement

Le pipeline complet nécessite **deux services** en parallèle (deux terminaux).

**Terminal 1 — Service NLU (environnement `noofar-rasa`)**
```bash
conda activate noofar-rasa
cd nlu
rasa run --enable-api --port 5005
```

**Terminal 2 — Application (environnement `noofar`)**
```bash
conda activate noofar

# Option A — Webhook FastAPI (production / WhatsApp)
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Option B — Démo Gradio (test / partenaires)
python app/gradio_app.py
```

---

## Structure du projet

```
noo-far-pipeline/
├── config/           # config.yaml (langue, modèles, RAG) + .env.example
├── enhance/          # débruitage (préparation corpus, hors temps réel)
├── asr/              # inférence Whisper + fine-tuning LoRA
├── nlu/              # service Rasa (intents fr/wo) — voir nlu/README.md
├── rag/              # indexation ChromaDB + retrieval hybride + fiches ISRA
├── tts/              # inférence MMS-TTS
├── app/              # webhook WhatsApp (FastAPI) + orchestration + démo Gradio
└── notebooks/        # tests A/B débruitage, baselines ASR/RAG, démo pipeline
```

---

## Modèles

Modèles hébergés sous l'organisation **`noofar-ia`** sur Hugging Face
*(dépôts privés pour l'instant — publication prévue une fois les modèles prêts)* :

| Modèle | Rôle | Base | Licence |
|--------|------|------|---------|
| `whisper-wolof`   | ASR wolof   | OpenAI Whisper | MIT |
| `whisper-pulaar`  | ASR pulaar  | OpenAI Whisper | MIT |
| `mms-tts-wolof`   | TTS wolof   | Meta MMS       | CC-BY-NC 4.0 |
| `mms-tts-pulaar`  | TTS pulaar  | Meta MMS       | CC-BY-NC 4.0 |

---

## Partenaires

- **ISRA-LNERV** — Institut Sénégalais de Recherches Agricoles (garant scientifique)
- **UFR CRAC-UGB** — Université Gaston Berger (garant linguistique)
- **Banaan Food** — porteur du projet

---

## Licence

Le **code** de ce dépôt est publié sous licence **MIT** (voir [`LICENSE`](LICENSE)).

⚠️ **Licence mixte — attention aux modèles.** Les modèles ne sont pas tous sous
la même licence que le code :
- Modèles **Whisper** (ASR) : MIT.
- Modèles **MMS-TTS** (TTS) : **CC-BY-NC 4.0 — usage non commercial uniquement**,
  contrainte héritée du modèle de base MMS de Meta.

Autrement dit, le code est librement réutilisable, mais toute utilisation des
modèles TTS (et de la démo qui les embarque) est restreinte à un usage non
commercial tant que MMS reste le modèle de base.