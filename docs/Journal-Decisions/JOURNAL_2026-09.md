# Journal de décisions — Ñoo Far · septembre 2026

> **Fichier de période (septembre 2026, S3,S4 puis mvp).** Deux parties.
> **En tête, les arbitrages d'architecture — état au 2 septembre 2026** : reporté
> depuis `JOURNAL_2026-07_08.md` (clôture 31 août), mis à jour avec les décisions
> de S3. Complet (tous les arbitrages, même inchangés) pour que le fichier se lise
> seul. Une fois la période close, cet en-tête ne se réécrit plus.
> **En dessous, le journal chronologique** de la période : la trace datée, dans
> l'ordre, jamais réécrite.

---

# Arbitrages d'architecture — état au 2 septembre 2026

## Chaîne du pipeline wolof

`audio → ffmpeg → ASR → [NLU désactivé] → retrieval → génération → frontend texte → TTS → audio`

Routage par langue via `config.yaml` (`lang: wo`). Le wolof n'est pas une traduction
du français : ASR, retrieval, fiches, frontend et TTS diffèrent. *Inchangé depuis
août.*

## ASR — `CAYTU/whosper-large` (Apache 2.0)

Candidat primaire retenu (S2-J3), validé en conditions réelles (S2-J5) : transcrit
du vrai wolof, diacritiques préservés, sortie en minuscules. Reste le maillon faible
mesuré → premier dans l'ordre du fine-tuning. *Inchangé depuis août.*

## Retrieval — hybride pour le wolof, sémantique pour le français

Différencié par langue (S2-J2) : `fr → semantic`, `wo → hybrid`. Validé en
conditions réelles (S2-J5) : la bonne fiche remonte dans le top 3.

**Constat affiné (S3-D1, 2 sept.)** — voir journal chronologique. Le test D1 a
mesuré, sur 10 questions in-corpus : bonne fiche accessible en top-3 dans 9 cas
sur 10, mais fiable en **top-1 seulement 3 fois sur 10**. Le chunk `reproduction.md`
domine systématiquement le classement (top-3 sur 11/11 questions testées, top-1 sur
7/10), indépendamment du sujet — biais à investiguer (`rag/indexer.py`), distinct
du problème de fiche vide déjà noté en août (6 chunks / 7 fiches). **Statut : le
« top-3 correct » validé en août reste vrai, mais le top-1 — dont dépend l'extraction
directe — est nettement moins fiable qu'estimé. Chantier retrieval rouvert, non
traité à ce jour.**

## Génération (D1) — ARBITRAGE PROVISOIRE (2 sept.)

- **Llama 3.2 3B : éliminé** (S2-J5). Aucune représentation du wolof.
- **Recensement S3 (1 sept.)** : ratissage HF + web, ≈10 modèles/familles wolof et
  multilingues recensés. Oolel-v0.1 confirmé seul générateur wolof natif open
  sérieux (Apache 2.0, Qwen2.5, 7,6 B) ; Oolel-Small-v0.1 en réserve ; les gros
  multilingues (Aya-101, Lugha-Llama, AfroLlama, Cheetah) écartés (wolof absent
  ou marginal).
- **Test Oolel-v0.1 (2 sept.)** : fp16 sur Kaggle 2×T4 (checkpoint fp32 ~30 Go,
  4 bits abandonné — voir journal). 11 questions (10 in-corpus + 1 hors-corpus),
  notation manuelle sur 4 critères. Résultat : wolof solide (11/11), fidélité
  factuelle faible (3/11, et 3/9 même fiche accessible), jamais franchement battu
  par l'extraction (5 gagné/5 nul/1 perdu) sauf sur le cas hors-corpus, où il est
  **dangereux** (hallucination assurée) plutôt que simplement mauvais.
- **Décision : ni Oolel-v0.1 ni l'extraction directe retenus tels quels pour la
  baseline.** Extraction directe conservée comme repli immédiat (moins utile,
  jamais dangereuse). Oolel réévalué après correctifs (retrieval + garde-fous
  prompt — voir journal chronologique pour le détail).
- **Repli 14 sept. si le retest ne tranche pas à temps : extraction directe.**

## TTS — Kiriku en socle (`AIHubSN/Kiriku-Wolof-TTS`, Apache 2.0)

Retenu comme socle (S2-J4), validé intelligible en conditions réelles (S2-J5).
Sonde Oolel-Voices toujours prévue en S3/J6. *Inchangé depuis août.*

## NLU — désactivé en wolof

Flag `nlu.enabled: false`. *Inchangé depuis août.*

## Contrainte matérielle — les gros modèles ne cohabitent pas sur T4 (15 Go)

Confirmé S2-J5. **Mise à jour S3 (2 sept.)** : le plan prévoyait Oolel-v0.1 en
4 bits sur T4 unique ; le checkpoint s'est révélé stocké en fp32 (~30 Go), rendant
le 4-bit/T4-unique non prioritaire pour un premier test. Basculé sur **Kaggle
2×T4 (32 Go), fp16 shardé (`device_map=auto`)** — chargement réussi, confirme que
la contrainte se contourne avec un runtime dédié plus large. Le run mesure le
**plafond qualité** (pleine précision), pas la variante de déploiement cible
(T4 unique, 4 bits) — à mesurer séparément avant la vidéo démo.

## Gouvernance & licences

*Inchangé depuis août — voir `JOURNAL_2026-07_08.md` pour le détail complet
(portée du copyleft, licences soynade non uniformes, seuil de déclenchement).*

## Débruitage (Resemble Enhance) — reporté MVP

*Inchangé depuis août.*

## Déploiement serveur — différé après baseline

*Inchangé depuis août.*

---

# Journal chronologique — septembre 2026

## 1er septembre 2026 — Recensement LLM wolof (D1, matinée)

**Contexte.** Sprint S3, bloc D1 : trancher le générateur de la baseline. Recensement
borné à 2h avant de tester Oolel-v0.1, pour ne pas rater un modèle plus récent
apparu depuis janvier.

**Résultats.**
- **Génératifs wolof natifs** : Oolel-v0.1 (soynade, Qwen2.5, 7,6B, Apache 2.0) →
  retenu, favori confirmé. Oolel-Small-v0.1 (même famille, plus petit, Apache 2.0)
  → testable, gardé en réserve. Oolel-Corrector (~2B, annoncé UNICEF Venture Fund)
  → écarté, aucun repo public trouvé.
- **Multilingues / pan-africains** : Aya-101 (mT5, 13B) écarté (NLG africain
  faible, trop gros pour T4). Lugha-Llama / AfroLlama / Cheetah écartés (wolof
  absent ou marginal — couvrent swahili, yoruba, haoussa, zulu, xhosa).
- **Adjacents (hors génération RAG)** : Oolel-Embed (embeddings retrieval wolof/fr,
  qwen3), Wolof Speech LLM soynade (ASR + traduction, pas génération RAG),
  traduction seq2seq (NLLB, M2M100). GGUF de Oolel-v0.1 (mradermacher) noté pour
  déploiement futur (llama.cpp).
- **Bilan : ≈10 modèles/familles recensés, 1 retenu + 1 en réserve.** Conclusion :
  Oolel est le seul générateur wolof natif open sérieux sur le Hub aujourd'hui ;
  les gros multilingues n'adressent pas ou mal le wolof.

**Écart au plan — acté.** Le plan prévoyait 4 bits (`bitsandbytes`) sur T4 unique.
Constat : le checkpoint Oolel-v0.1 est stocké en **fp32** (~30 Go, 7 shards) — pas
bf16/fp16 comme supposé. Choix retenu : **Kaggle 2×T4 (32 Go), fp16 shardé**
(`device_map="auto"`) au lieu de 4 bits. Conséquence : le run à venir mesure le
plafond qualité d'Oolel, pas la variante déployée (T4 unique, 4 bits) — à mesurer
à part. La friction bitsandbytes/Qwen2 anticipée au plan est donc contournée, pas
rencontrée.

**Infra d'éval montée (avance sur le run du 2 sept.).**
- `eval_set.json` produit depuis le retrieval réel du projet (`08_indexation_wolof.ipynb`,
  mode hybrid, top-3) : 11 questions (10 issues de `rag/questions_test_wo.py`,
  intents variés + 1 hors-corpus ajoutée — prix/vente du lait, absente du corpus de
  6 fiches) ; champs `question`/`intent_attendu`/`passages`/`sources` ; figé, uploadé
  en dataset Kaggle privé (`noofar-eval-set`).
- Notebook d'éval Kaggle (`12_test_llm.ipynb`, 5 cellules) : config, chargement
  `eval_set.json`, `SYSTEM_WO` (consigne wolof : répondre en wolof, s'ancrer sur le
  xibaar fourni, dire l'absence d'info plutôt qu'inventer, registre simple),
  gabarit chat aligné (`Xibaar bi:` / `Laaj bi:`), harnais fp16/sharding, export CSV.

## 2 septembre 2026 — Test Oolel-v0.1 (D1) : arbitrage provisoire

**Contexte.** Suite du recensement du 1er sept. Charger Oolel-v0.1 et générer sur
les 11 questions figées, comparer à l'extraction directe, trancher D1.

**Protocole.** Kaggle 2×T4, fp16 shardé, décodage greedy (`do_sample=False`,
`max_new_tokens=384`). 11 questions (10 in-corpus + 1 hors-corpus : « Am naa ñaari
litir meew. Ñaata laa leen mëna jaay ? » — à combien vendre 2L de lait, sujet
absent des 6 fiches). Notation manuelle (locuteur wolof) sur grille binaire :
`wolof_ok`, `fidele`, `oral`, `mieux_que_extraction`, + `remarques`.

**Résultats chiffrés (11 questions).**

| Critère | Résultat |
|---|---|
| `wolof_ok` | 11/11 (100 %) — wolof solide, aucune bascule de langue |
| `fidele` | 3/11 (27 %) |
| `oral` | 9/11 (82 %) — 2 lignes pénalisées par un artefact `\n` littéral (chat template, corrigible en post-traitement) |
| `mieux_que_extraction` | 5 gagné / 5 nul (les deux méthodes mauvaises) / 1 perdu |

**Constat clé — fidélité indépendante de l'accès à l'info.** Sur les 10 questions
in-corpus, la bonne fiche (`intent_attendu`) est accessible dans le top-3 pour 9
d'entre elles (seule une, sur l'alimentation, n'a aucune fiche pertinente dans le
top-3 — trou de contenu ou échec de ranking à trancher au chantier retrieval).
**Mais même quand la bonne fiche est accessible, Oolel se trompe dans 6 cas sur 9**
— dont deux où elle était en **position 1** (la meilleure situation possible).
La fidélité factuelle est donc un point faible propre au modèle/prompt, pas
seulement une conséquence du retrieval.

**Cas hors-corpus — échec critique.** Sur la question prix/lait (aucune fiche
pertinente), Oolel n'a pas signalé l'absence d'info malgré la consigne explicite
(`SYSTEM_WO` : « sudee leeral yi nekkul ci xibaar bi, wax ko—bul sos dara »). Il a
détourné le passage extrait (fiche sur les races N'Dama/Gobra) en une réponse
assurée et absurde (« vends 2L par race », sans aucun fondement réel). Halluciné avec
une syntaxe de réponse plausible — plus dangereux qu'un refus maladroit ou qu'une
extraction visiblement hors-sujet.

**Cause racine retrieval identifiée.** Le chunk `reproduction.md` domine le
classement sur 11/11 questions (présent dans le top-3 à chaque fois, top-1 sur
7/10 in-corpus), indépendamment du sujet posé — explique la faible fiabilité du
top-1 (3/10) dont dépend structurellement l'extraction directe. Distinct du
problème de fiche vide déjà noté en août (6 chunks/7 fiches) : à investiguer côté
`rag/indexer.py`/embeddings.

**Décision D1 : ni Oolel-v0.1 ni l'extraction directe retenus tels quels pour la
baseline.**
- Oolel n'est jamais franchement moins bon que l'extraction sur les questions
  normales, mais son taux d'hallucination reste trop élevé pour être fiable en
  l'état — y compris quand l'information est disponible.
- L'extraction directe reste **structurellement bornée par un top-1 fiable
  seulement 3 fois sur 10** sur cet échantillon — moins robuste qu'estimé en août.
- **Extraction directe conservée comme repli immédiat** pour ne pas bloquer le
  reste du sprint (moins utile, mais jamais dangereuse — contrairement à Oolel non
  corrigé sur le cas hors-corpus).
- **Oolel réévalué après correctifs**, pas abandonné : le signal (`mieux_que_extraction`
  positif ou nul dans 10/11 cas) reste favorable une fois les causes connues
  corrigées.

**Pistes d'amélioration avant retest :**
- Corriger le biais de ranking `reproduction.md` (`rag/indexer.py`).
- Combler le trou de contenu identifié (question alimentation sans fiche pertinente
  dans le top-3).
- Renforcer `SYSTEM_WO` : étape explicite de vérification (« le xibaar traite-t-il
  vraiment du sujet de la question ? ») + exemple de formule de refus — l'absence
  d'exemple de refus est une piste plausible de l'échec sur le cas hors-corpus,
  non testée isolément à ce stade.
- Nettoyer l'artefact `\n` littéral avant TTS (post-traitement trivial,
  `preparer_pour_tts` ou juste avant).

**Repli si le retest ne tranche pas avant le 14 sept. : extraction directe.**

**Non traité aujourd'hui, reporté :** chantier retrieval (`rag/indexer.py`, biais
de ranking + fiche vide) ; retest Oolel avec correctifs ; mesure latence 4-bit/T4
unique (déploiement cible, distincte du plafond qualité mesuré aujourd'hui).
