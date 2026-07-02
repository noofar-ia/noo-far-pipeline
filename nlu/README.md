# NLU — Service Rasa (Ñoo Far)

Compréhension du langage pour Ñoo Far : classification d'**intents** et
extraction d'**entités** à partir du texte transcrit par Whisper.

Tourne comme un **service séparé** que `app/pipeline.py` interroge en HTTP.
L'intent détecté est ensuite transmis au RAG, qui génère la réponse.

> ⚠️ **Environnement distinct du pipeline principal.** Rasa embarque
> TensorFlow et une pile de dépendances épinglée, incompatible avec le
> stack PyTorch de `noofar`. **Ne jamais installer Rasa dans l'environnement
> du pipeline.**

---

## Prérequis

- **Python 3.10** (Rasa 3.6.x ne supporte pas Python ≥ 3.11)
- conda

## Installation

```bash
# Environnement dédié (depuis la racine du dépôt)
conda create -n noofar-rasa python=3.10 -y
conda activate noofar-rasa

pip install --upgrade pip
pip install rasa==3.6.21

# Dépendances figées (reproduction à l'identique)
# pip install -r nlu/requirements-rasa.txt
```

> Note portabilité : `requirements-rasa.txt` a été généré sous Windows et
> contient des paquets spécifiques (`pywin32`, `pyreadline3`). Sur Mac/Linux,
> le régénérer ou retirer ces lignes.

---

## Structure

```
nlu/
├── config.yml           # pipeline NLU (tokenizer, featurizers, DIETClassifier)
├── domain.yml           # déclaration des intents + entités
├── data/
│   ├── fr/intents.yml   # exemples d'entraînement — français
│   └── wo/intents.yml   # exemples d'entraînement — wolof (à venir, août)
└── requirements-rasa.txt
```

## Entraînement

```bash
conda activate noofar-rasa
cd nlu
rasa train nlu          # entraîne uniquement le NLU (pas de dialogue)
```

Le modèle entraîné est écrit dans `nlu/models/`.

## Lancement du service

```bash
conda activate noofar-rasa
cd nlu
rasa run --enable-api --port 5005
```

Le pipeline interroge ensuite l'endpoint `/model/parse` (port 5005,
configuré dans `config/config.yaml` → `services.rasa_url`) pour obtenir
l'intent et les entités d'un texte.

---

## Intents actuels

Politesse : `salutation`, `au_revoir`
Métier : `sante_animale`, `vaccination`, `alimentation`, `reproduction`,
`production_laitiere`, `conduite_elevage`
Technique : `nlu_fallback` (repli automatique si confiance faible)

**Entités :** `animal`, `maladie`, `symptome`

> Les exemples d'entraînement actuels sont un **modèle de travail**.
> Le contenu réel (formulations de terrain) sera validé avec CRAC-UGB.