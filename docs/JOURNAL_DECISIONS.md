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

## 13 juillet 2026 — Déploiement serveur : différé après la phase baseline

**Contexte.** Question posée en préparant le test Twilio (réception de messages via webhook) : à quel moment déployer Ñoo Far sur un vrai serveur, plutôt que de tester en local avec un tunnel temporaire (ngrok) ?

**Décision : pas de déploiement serveur avant la fin de la phase baseline (après le 9 août).** Le développement et les tests (S1 à S4) continuent avec ngrok + Codespace comme environnements de test, sans serveur permanent.

**Raisons :**
- L'architecture n'est pas encore figée — l'arbitrage RAG hybride vs sémantique (S2) et l'arbitrage LLM génération vs extraction directe (S4) détermineront ce qu'il y a réellement à déployer. Déployer avant ces décisions reviendrait à figer une version probablement obsolète en quelques semaines.
- Un serveur a un coût récurrent, à justifier une fois l'architecture connue plutôt qu'anticipé sur des hypothèses.
- ngrok (tunnel temporaire) + Codespace suffisent largement aux besoins actuels : prouver que le mécanisme (webhook, réception, traitement, réponse) fonctionne, produire des démos ponctuelles (vidéos Loom), sans nécessiter une disponibilité 24/7.

**Le bon moment identifié : au cadrage de la phase MVP, rapport baseline en main.** À ce moment, trois éléments seront connus et guideront le choix d'infrastructure : l'architecture retenue (donc les ressources nécessaires — un LLM actif est plus lourd qu'une simple extraction), le besoin réel de disponibilité continue (tests par l'équipe, démos à ISRA/UGB/Banaan Food), et la stratégie de monétisation du projet (qui interagit avec la question de licence MMS/CC-BY-NC déjà notée).

**Exception possible avant cette échéance :** si des démos par des tiers externes (Banaan Food, ISRA) sont nécessaires avant le 9 août, un déploiement minimal et temporaire (type Render.com ou Railway.app, tier gratuit) pourrait se justifier ponctuellement, uniquement pour stabiliser une URL de démo — à évaluer au cas par cas, non planifié par défaut.

---
---
