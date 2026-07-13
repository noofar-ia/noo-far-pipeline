# Journal de décisions — Ñoo Far

> Ce document trace les décisions techniques et méthodologiques prises au fil du projet — celles qui méritent d'être retrouvables plus tard, sans pour autant justifier une entrée dans le README ou l'ONBOARDING. Chaque entrée : contexte, ce qui a été tenté, la décision, et ce qui reste à faire si applicable.

---

## 13 juillet 2026 — Resemble Enhance : abandon temporaire (sprint fondations)

**Contexte.** Test prévu du sprint fondations : installer et valider Resemble Enhance sur Google Colab, pour le débruitage audio en préparation de corpus.

**Ce qui a été tenté.**
- Installation standard (`pip install resemble_enhance`) → échec immédiat : le paquet exige `torch==2.1.1`, indisponible pour Python 3.12 (version actuelle des runtimes Colab). Écart créé par l'âge du paquet (dépendances figées fin 2023) face à l'évolution de l'écosystème.
- Tentative en mode dégradé (`pip install resemble_enhance --no-deps`) puis installation manuelle des dépendances une à une, en versions non épinglées.
- `deepspeed` (la dépendance la plus à risque) a fini par s'installer (version 0.19.2 au lieu de 0.12.4 requis par le paquet).
- Au terme de l'installation, **17 conflits de dépendances** recensés par pip : torch, torchaudio, torchvision, numpy, scipy, pandas, gradio, librosa, matplotlib, rich, soundfile, tqdm, omegaconf, tabulate, celluloid, ptflops, resampy — tous décalés entre la version figée par le paquet (fin 2023) et l'environnement Colab actuel (mi-2026), soit environ 2,5 ans d'écart cumulé.

**Décision : reporté à la phase MVP.** Le risque de bugs silencieux (résultats faux sans erreur explicite, notamment via le changement de version majeure numpy 1.26→2.0) est jugé trop élevé pour un contournement de sprint. Le rapport temps/bénéfice ne justifie pas de pousser plus loin aujourd'hui.

**Pistes pour la reprise en phase MVP :**
- Environnement Docker dédié, avec Python 3.10 et torch 2.1.1 figés, isolé de Colab et de son évolution continue
- Recherche d'un fork communautaire maintenu de `resemble_enhance` avec dépendances déverrouillées
- Évaluation d'une alternative de débruitage plus récente et mieux intégrée à l'écosystème Hugging Face (`transformers`)

**Usage prévu, pour mémoire :** faciliter le travail des transcripteurs humains en préparation/enrichissement de corpus terrain — **pas** une brique du pipeline de production temps réel (celui-ci reçoit l'audio brut, Whisper le traite directement). Le report n'est donc pas bloquant pour le prototype français (S1) ni pour la phase baseline.

---
