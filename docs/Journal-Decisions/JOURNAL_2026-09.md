# Journal de décisions — Ñoo Far · septembre 2026

> **Fichier de période (septembre 2026, S3).** Deux parties.
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

## 2 septembre 2026 (suite) — Diagnostic retrieval : cause du biais identifiée

**Contexte.** Suite à l'arbitrage D1, diagnostic du biais `reproduction.md` (via
Claude Code : lecture `indexer.py`/`retriever.py` + test empirique semantic seul
vs BM25 seul sur les 11 questions).

**Constats.**
- **Chunking** (`indexer.py`) non en cause — `chunk_size=400`, fiches 214-272 mots,
  1 fiche = 1 chunk sans découpage. `reproduction.md` (222 mots) n'est pas la plus
  longue.
- **Fusion hybride** (`retriever.py`) non en cause — alternance sémantique/BM25
  correcte, dédoublonnage correct.
- **BM25 seul** : correct en top-1 sur 6/10, aucun biais systématique.
- **Sémantique seul** : `reproduction.md` domine (top-1 sur 7/11 questions,
  y compris hors-sujet) — le biais est concentré sur le signal sémantique.
- **Cause racine : effet « hub » en espace d'embedding.** `paraphrase-multilingual-MiniLM-L12-v2`
  mal adapté au wolof (langue hors distribution pour lui) ; similarité cosinus
  moyenne de `reproduction.md` aux 11 questions = 0,5825 (max de toutes les
  fiches), y compris sur les questions hors-sujet.
- **Trouvé en passant** : `sante_animale.md` / `vaccination.md` quasi dupliquées
  (cosinus 0,959, ~90 % de texte identique) — problème de contenu distinct, à
  corriger séparément.

**Décision : remplacer le modèle d'embedding (candidat : `soynade-research/Oolel-Embed`,
wolof natif) plutôt que patcher le score.** Repondérer/plafonner le signal
sémantique traiterait le symptôme sur ce corpus précis, sans garantir la tenue
une fois le corpus élargi (fiche alimentation à ajouter, et au-delà).

**Non traité aujourd'hui :** test effectif d'Oolel-Embed ; dédoublonnage
`sante_animale.md`/`vaccination.md`.

## Correction — origine des fiches wolof

Le journal d'août (S2-J1) documentait un test NLLB-200 (`facebook/nllb-200-distilled-600M`)
avec des limites sérieuses (hallucination répétitive, confusion lexicale
« Bourgou »→« Bourgogne », mélange FR/WO). **Précision : ce test a été abandonné.**
Les 6 fiches wolof actuellement indexées (`rag/fiches/wo/`) proviennent d'une
traduction **Google Translate suivie d'une relecture manuelle**, fiche par fiche
— pas de NLLB. Ce pivot n'était pas documenté jusqu'ici ; les limites NLLB de
S2-J1 restent valables comme test, mais ne s'appliquent pas au corpus en
production.

## Réflexion pour la suite (MVP) — réentraîner le NLU pourrait remplacer une partie du retrieval

**Contexte.** NLU désactivé depuis S2 (`nlu.enabled: false`, modèle Rasa entraîné
en français, inutilisable sur du wolof). Question posée en repensant à
l'architecture globale, à la lumière du diagnostic retrieval du jour.

**Piste.** Avec le corpus actuel (6 fiches = 6 intentions, correspondance
1-pour-1), un NLU wolof correctement entraîné rendrait le retrieval sémantique
largement inutile pour le *routage* : l'effet « hub » identifié aujourd'hui
(modèle d'embedding généraliste mal adapté au wolof) devient sans objet si
l'intention de la question est déjà connue en amont — plus besoin de similarité
vectorielle pour choisir la fiche.

**Réserves posées avant d'en faire un plan :**
1. Nécessite un corpus wolof annoté question→intention construit spécifiquement.
   Les 10 questions de `rag/questions_test_wo.py` sont un point de départ, très
   insuffisantes pour entraîner (moins de 2 exemples/intention sur 6 classes).
2. Ne fonctionne proprement que tant qu'1 fiche = 1 domaine ; dès que le corpus
   grandit (plusieurs fiches par domaine), retombe sur le même besoin de bon
   retrieval à l'intérieur du « tiroir » trouvé par le NLU — repousse le
   problème plus qu'il ne l'élimine définitivement.
3. Doit intégrer **dès la conception** une classe de rejet explicite
   (« hors_corpus ») — sinon reproduit, une étape plus tôt dans la chaîne, le
   même problème de garde-fou identifié aujourd'hui avec Oolel sur la question
   prix/lait.

**Statut : piste MVP à instruire, non planifiée dans le sprint S3 en cours.**

## 3 septembre 2026 — D1 tranché définitivement + Bloc B Jeu 3

**Contexte.** Suite du diagnostic retrieval du 2 sept. Trois correctifs à appliquer
avant retest : contenu (dédup + trous), retrieval (déjà fait la veille), prompt
(`SYSTEM_WO`). Objectif : trancher D1 pour de bon, puis démarrer Bloc B (chaîne
séquentielle) avec le générateur retenu.

**Correctifs de contenu.**
- Dédup `sante_animale.md`/`vaccination.md` : paragraphe pneumopathies/strongyloses
  dupliqué retiré de `vaccination.md`, remplacé par un renvoi croisé.
- 3 sections ajoutées et sourcées, comblant les trous identifiés par l'audit
  intent↔contenu de la veille :
  - **Fréquence et régularité de la traite** (`production_laitiere.md`) — ISRA-BAME,
    *État des lieux de la filière lait et produits laitiers au Sénégal* (2005).
  - **Anoestrus post-partum / infertilité** (`reproduction.md`) — IRD (BEEP-IRD),
    *Contribution à l'étude de l'anoestrus post-partum chez la vache* ; Cirad, UR
    Systèmes d'élevage (races tropicales).
  - **Besoins spécifiques en lactation** (`alimentation.md`) — IRA Mamadou,
    *Optimisation de la production laitière...* (IDR-UPB, 2015, Burkina Faso —
    contexte sahélien comparable, non spécifique au Sénégal, précisé dans la
    citation).
- Bug trouvé et corrigé dans `conduite_elevage.md` : deux sous-sections portaient
  le même titre « Jamonoy taw » (saison sèche) alors qu'elles distinguaient saison
  sèche et saison des pluies en FR — corrigé en **Noor** (saison sèche) / **Nawet**
  (saison des pluies).
- Renvois croisés inter-fiches uniformisés sur les titres FR canoniques (plusieurs
  incohérences trouvées : noms wolof non-canoniques, casse, fiche inexistante
  « Nutrition » au lieu d'« Alimentation »).
- Les 4 fiches touchées retraduites en wolof par l'utilisateur (Google Translate +
  relecture manuelle), vérifiées avant intégration.

**`SYSTEM_WO` renforcé.** Ajout d'une étape de vérification explicite avant
réponse (« le xibaar traite-t-il vraiment du sujet de la question ? »), en plus de
la règle de refus déjà présente. Version finale :

> *Yaa ngi jàppale sàmmkat yi. Tontu leen ci wolof rekk, jëfandikoo mbind mu yomb
> te leer. Laata ngay tontu, xool bu baax ndax leeral yi nga joxe dañuy wax ci laaj
> bi; sudee leeral yi wax ci laaj bi amul, wax rek ni amoo xibaar boobu—bul defar
> dara.*

Un essai d'ajout d'une contrainte de brièveté (« 2-3 phrases, pas de liste ») a été
**testé et abandonné** : sur le retest, a cassé deux réponses (boucle répétitive de
40s sur la question la plus dense — infertilité — et perte de fidélité sur une
autre, réponse tronquée sur la mauvaise phrase de la fiche). Reporté en optimisation
phase MVP, à reformuler en intention (« reste concis ») plutôt qu'en contrainte
stricte de longueur.

**Retest complet (11 questions, `eval_set_v2.json` régénéré après tous les
correctifs).**

| Critère | 2 sept. (avant) | 3 sept. (après) |
|---|---|---|
| `wolof_ok` | 11/11 (100%) | 11/11 (100%) |
| `fidele` | 3/11 (27%) | **10/11 (91%)** |
| `oral` | 9/11 (82%) | 9/11 (82%) |
| `mieux_que_extraction` | 5 gagné/5 nul/1 perdu | **11/11 gagné, 0 perdu** |

**Cas hors-corpus (prix/lait), le test le plus critique.** Le 2 sept., Oolel
détournait un passage hors-sujet en réponse assurée et dangereuse (invente un mode
de vente par race bovine). Le 3 sept. : refus explicite et propre (« amul benn
xibaar ci njëg wi... »), sans invention. Le garde-fou renforcé tient à l'échelle
des 11 questions, pas seulement sur un sous-ensemble restreint testé plus tôt dans
la journée.

**Retrieval — robustesse confirmée malgré un corpus modifié.** La régénération de
`eval_set_v2.json` a d'abord montré une inquiétude : sémantique seul passe de
10/10 à 6/10 sur le nouveau corpus (chunking modifié : 6→8 chunks après les ajouts
de contenu). Mais le mode **hybride** (0,2/0,8, correctif de la veille) reste solide
à 91% de hit top-3 — le faible poids accordé au signal sémantique absorbe sa
dégradation sans se répercuter sur le résultat final. Validation *a posteriori* du
choix de repondération plutôt que d'un patch plus étroit.

**Décision D1 — TRANCHÉE DÉFINITIVEMENT : Oolel-v0.1 retenu comme générateur de la
baseline.** Extraction directe abandonnée comme repli — plus nécessaire, Oolel ne
perd sur aucune question du retest complet.

**Point faible résiduel, non bloquant.** Une question (âge de mise à la
reproduction) répond encore à côté du sujet — décalage de compréhension isolé, pas
une invention factuelle dangereuse. Densité/répétition sur quelques réponses :
artefact de formatage déjà identifié (`\n` littéraux, listes numérotées), non
traité aujourd'hui — nettoyage post-traitement avant TTS reporté.

---

## 3 septembre 2026 (suite) — Bloc B, Jeu 3 : câblage séquentiel

**Contexte.** D1 tranché, passage à l'intégration dans le pipeline réel. Objectif
du jour : `process()` tourne de bout en bout, mémoire GPU gérée par
charge/décharge séquentielle — pas d'optimisation de latence (cible matérielle de
déploiement encore inconnue, différée post-baseline).

**`rag/generator.py` réécrit.**
- Chemin dédié pour le wolof : `get_oolel()` (chargement `AutoModelForCausalLM`,
  fp16, `device_map="auto"`, avec cache) + `generate_wo()` (chat template,
  gabarit `Xibaar bi:`/`Laaj bi:` validé par le retest, `do_sample=False`,
  `max_new_tokens=384`). Branché dans `generate()` via `if lang == "wo"`.
- `PROMPTS["wo"]` (version antérieure au `SYSTEM_WO` validé) retiré — aucun autre
  appelant trouvé dans le repo, confirmé avant suppression.
- `SYSTEM_WO` externalisé dans `rag/prompts/system_wo.txt` (permet d'itérer sans
  toucher au code — utile pour la piste brièveté reportée en MVP).
- `config.yaml` : `models.llm.wo` → `soynade-research/Oolel-v0.1` (Llama 3.2 3B
  retiré, éliminé depuis le 2 sept).
- Chemin français (`pipeline()` générique) non touché.

**Validation isolée sur Kaggle — pas en notebook autonome, via le vrai code.**
Repo cloné, `from rag.generator import generate` exécuté tel quel sur 2 questions
du retest (dont la hors-corpus). Un bug de format trouvé et corrigé en route :
`generate_wo()` attend des passages en tuples `(doc, meta)` (format natif de
`retriever.py`), le premier test utilisait des passages aplatis en strings
(format `eval_set_v2.json`) — corrigé côté notebook de test, pas côté
`generator.py` (le format tuple est le bon pour l'usage réel en production).
Une fois corrigé : `generate_wo()` reproduit fidèlement le comportement du
retest — refus propre confirmé sur la question hors-corpus.

**`process()` (`app/pipeline.py`) — séquence charge/décharge implémentée.**
- `unload_llm()` étendu pour vider aussi le cache Oolel (un seul point d'entrée,
  plutôt qu'une fonction séparée).
- `unload_asr()`/`unload_tts()` créés sur le même patron.
- Décharge après chaque maillon (ASR → décharge → retrieval → génération →
  décharge → TTS → décharge), **y compris Kiriku en fin d'appel** — décision
  prudente : la cible matérielle de déploiement est inconnue, donc l'hypothèse
  par défaut est la plus prudente (accepter un rechargement à chaque requête
  plutôt que risquer un OOM en usage réel non anticipé). Réversible facilement
  une fois la cible connue.
- Instrumentation de latence existante préservée (mêmes clés), coût de décharge
  absorbé dans le segment adjacent plutôt qu'une nouvelle clé dédiée.

**Vérification de l'état du dépôt (avant Ven 4).** `app/gradio_app.py` déjà
correct — appelle `process(..., lang=config["lang"])`, pas de `"fr"` en dur
(friction anticipée qui n'existait finalement pas). Deux points cosmétiques
trouvés et corrigés en passant : titre de l'interface Gradio toujours en
français, sortie figée obsolète dans `11_pipeline_wolof_e2e.ipynb` référençant
encore Llama pour le wolof.

**Livrable du jour.** `process()` séquentiel fonctionnel avec Oolel-v0.1 comme
générateur. `generator.py` validé isolément en conditions réelles (repo cloné,
pas de reconstruction manuelle).

**Reporté à demain (Ven 4).** Démo bout-en-bout via Gradio : vérifier
`gradio_app.py` en usage réel, frictions d'encodage (`ë ñ ó à ŋ`), longueur de
réponse pour le TTS, notebook e2e à jour comme livrable.
