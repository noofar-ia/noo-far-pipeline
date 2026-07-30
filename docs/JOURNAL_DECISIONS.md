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

## 21 juillet 2026 — Test retrieval RAG (J2) : mécanisme validé, résultats mitigés sur ce corpus

**Contexte.** Premier test du RAG (S1-J2) : 6 fiches FR indexées dans ChromaDB (vaccination, santé animale,
alimentation, reproduction, production laitière, conduite d'élevage), testées sur 5 questions d'éleveur
réalistes, en comparant les trois modes de récupération (`semantic`, `bm25`, `hybrid`).

**Résultats bruts (top-1 correct / 5 questions) :**
- Semantic seul : 3/5 (Q1 vaccination, Q4 alimentation, Q5 reproduction)
- BM25 seul : 0/5
- Hybrid : 3/5 (identique à semantic seul)

**Diagnostic.** BM25 échoue systématiquement sur ce corpus : les 6 fiches partagent un vocabulaire commun
dense (vache, lait, jour, alimentation), ce qui produit du bruit lexical plutôt qu'un signal utile — BM25
n'a aucune notion de sens, seulement de fréquence de mots. Le sémantique s'en sort mieux car il capture le
sens au-delà des mots exacts. L'hybride n'apporte ici aucun gain par rapport au sémantique seul (hérite des
mêmes erreurs, sans les corriger).

**Échecs persistants même en sémantique pur (Q2 « fièvre », Q3 « traire »)** — probablement liés au contenu
des fiches plutôt qu'à la méthode de récupération : `sante_animale.md` et `production_laitiere.md` ne
mettent peut-être pas assez explicitement en avant les termes attendus (fièvre, traite) dans leurs premiers
chunks.

**Décision : basculer `retrieval: semantic` par défaut dans `config.yaml`** pour ce corpus restreint —
l'hybride ne se justifie pas ici. Réévaluer l'hybride en S2 sur le corpus wolof, plus large et au vocabulaire
technique potentiellement plus rare, contexte où BM25 pourrait mieux se justifier.

**Ajustements de contenu à faire avant la prochaine évaluation :**
- `sante_animale.md` : renforcer la présence explicite du mot « fièvre » dès le début de fiche (déjà présent
  mais peut-être noyé dans le chunk)
- `production_laitiere.md` : ajouter une mention explicite de la fréquence/rythme de traite (le mot
  « traire »/« traite » n'apparaît qu'une fois, en fin de fiche, dilué dans un chunk plus général)
- Plus largement : revoir le chunking pour que les mots-clés attendus par question type apparaissent tôt
  dans chaque chunk, pas seulement quelque part dans le texte

**Non bloquant pour la suite** — le mécanisme technique (indexation, requête, hybride, dédoublonnage) est
validé et fonctionnel. Les ajustements ci-dessus sont une amélioration de contenu, à faire à la mise au
propre plutôt que maintenant.

## 26 juillet 2026 — Pipeline J4 : câblage validé, limite d'infrastructure Codespace identifiée

**Contexte.** Assemblage du pipeline complet (ASR → NLU → RAG → LLM → TTS) exposé via FastAPI et connecté
à Telegram. Bug Rasa/Windows confirmé structurel (voir entrée précédente) : développement basculé sur
Codespace pour tout ce qui recharge un modèle Rasa.

**Résultat obtenu.** Le pipeline a réussi, au moins une fois, à traverser la chaîne complète sur Codespace
(4-core/16Go) : téléchargement audio Telegram → Whisper (ASR) → Rasa (NLU) → ChromaDB (retrieval) →
Llama 3.2 3B (génération) → MMS-TTS (synthèse), avec un "Audio généré" confirmé en sortie. Le câblage entre
toutes les briques développées J1-J3 est donc validé.

**Limite identifiée : charge simultanée trop lourde pour le tier Codespace testé.** Rasa (TensorFlow) +
Whisper + Llama 3.2 (6,4 Go) + MMS-TTS chargés ensemble dépassent régulièrement ce que Codespace peut
soutenir de façon fiable, même à 16 Go de RAM (`available` pourtant confortable au moment des crashs,
`Terminated`/`Killed` reproductibles autour de 50-80% du chargement de Llama 3.2 spécifiquement).
Diagnostics écartés : espace disque (cache complet et sain, scan confirmé), corruption de fichiers,
pic mémoire au chargement (`low_cpu_mem_usage=True` sans effet). Cause probable : limite de ressources
Codespace non visible dans `free -h`/`df -h` (quota CPU, cgroup, ou politique de l'infrastructure cloud).

**Bug secondaire corrigé au passage : retries Telegram.** Le webhook bloquait la réponse HTTP jusqu'à la
fin complète du pipeline (plusieurs minutes) — Telegram, n'obtenant pas de réponse rapide, retentait
l'envoi du même message, multipliant les exécutions concurrentes du pipeline et aggravant la pression sur
les ressources. Corrigé via `asyncio.create_task()` : réponse immédiate à Telegram, traitement en tâche
de fond.

**Décision : le câblage du pipeline est considéré comme validé** malgré l'échec de robustesse sur cette
infra précise. La vraie mesure de performance et de fiabilité se fera avec une infrastructure adaptée
(Colab avec GPU, ou serveur de production dédié en phase MVP) — non prioritaire à corriger sur Codespace
gratuit, qui n'a jamais eu vocation à faire tourner l'ensemble de la stack simultanément.

## 28-29 juillet 2026 — Évaluation comparative NLLB vs Google Translate (fr→wolof), bascule méthodologique

**Contexte.** Lors de la relecture des fiches wolof traduites via NLLB-200 (S2-J1), plusieurs erreurs
significatives détectées, dont une sur un terme de base : « vache » traduit par « gàtt » (signifie
« court » en wolof), au lieu de « nag ». Confirmé via dictionnaires wolof-français externes — vraie
erreur du modèle, pas une lacune de connaissance personnelle. 8 occurrences trouvées sur 5 fiches sur 6.

**Test comparatif effectué.** Le même segment (« Ma vache a de la fièvre, que faire ? ») testé sur :
- **NLLB-200 distilled-600M** : erreur sur « vache » (gàtt, faux-sens)
- **Google Translate (interface web `translate.google.com`)** : correct (« Sama nag dafa am yaram wu tàng »)

**Limite découverte sur Google Translate** : l'**API officielle Cloud Translation ne supporte pas le
wolof** (vérifié via `GET /language/translate/v2/languages`, `wolof_present: False`) — seule
l'interface web grand public propose le wolof, probablement en mode communautaire/expérimental non
exposé par l'API. Aucune automatisation par script n'est donc possible avec l'API officielle ; la
traduction via Google doit se faire manuellement, un texte à la fois, dans l'interface web.

**Décision : bascule vers traduction manuelle (Google Translate web + relecture systématique)** pour
les 6 fiches et les questions de test de S2, remplaçant NLLB pour cette étape. Objectif : que le test
critique du RAG wolof (S2-J2) évalue l'architecture de récupération, pas la qualité de traduction —
les deux causes d'échec ne doivent pas rester mélangées dans un même résultat.

**Évaluation comparative à formaliser en score, une fois la relecture terminée :**
- Construire un petit jeu de phrases de référence (les 6 fiches + 10 questions, ou un sous-ensemble),
  avec traduction validée par relecture humaine comme référence
- Noter séparément NLLB et Google Translate sur ce même jeu, avec une méthode simple (ex. % de segments
  jugés corrects sans retouche, ou nombre de corrections nécessaires par segment)
- Consigner le score de chaque outil dans `docs/S2_limites_nllb_wolof.md`, à réutiliser pour le rapport
  baseline (S4) et pour trancher si NLLB reste viable pour un futur passage à plus grande échelle
  (15+ fiches, où la traduction manuelle via interface web deviendrait trop coûteuse en temps)

**Non tranché à ce stade** : le score chiffré définitif — dépend de la relecture complète des 6 fiches,
en cours. Cette entrée sera complétée une fois les données disponibles.

---
---

------
---
