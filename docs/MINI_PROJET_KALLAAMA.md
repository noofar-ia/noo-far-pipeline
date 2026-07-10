# Mini-projet KALLAAMA — Dossier de travail

> **Objectif :** au terme de ce mini-projet, tu auras un notebook Jupyter propre qui analyse 3 audios KALLAAMA (chargement, parsing des transcriptions `.trs`, visualisations, écoute, synthèse). C'est l'exercice intégrateur du sprint fondations : tout ce que tu apprends (NumPy, Pandas, Librosa, Unité 1 HF) se rencontre ici sur les vraies données du projet.
>
> **Budget temps :** ~6h répartis sur jeudi soir, vendredi et samedi matin.
> **Livrable :** `notebooks/01_kallaama_exploration.ipynb` commité dans le dépôt.

---

## Sommaire

1. [Préparation — à faire avant tout code](#1-préparation)
2. [Étape 1 — Récupérer et organiser les données](#étape-1)
3. [Étape 2 — Exploration globale du corpus](#étape-2)
4. [Étape 3 — Écrire le parseur `.trs`](#étape-3)
5. [Étape 4 — Analyse détaillée des 3 audios](#étape-4)
6. [Étape 5 — Synthèse comparative](#étape-5)
7. [Étape 6 — Finition et commit](#étape-6)
8. [Points de vigilance](#vigilance)
9. [Annexe — Structure attendue du notebook](#annexe)

---

<a name="1-préparation"></a>
## 1. Préparation — à faire AVANT tout code (~1h)

C'est la phase la plus importante et la plus négligée. Prends le temps de la faire proprement — tu récupèreras chaque minute investie ici en évitant des heures de frustration ensuite.

### 1.1 — Fiche d'identité du corpus KALLAAMA

**Informations collectées lors de la préparation (à insérer en tête du notebook) :**

```
Corpus : KALLAAMA
Titre complet : "A Transcribed Speech Dataset about Agriculture
                 in the Three Most Widely Spoken Languages in Senegal"
Année : 2023 (production) / 2024 (publication)
Thématique : AGRICULTURE — alignement direct avec Ñoo Far

Porteur : Jokalante (Dakar, Sénégal)
Partenaires : Orange Innovation (Lannion, France),
              École Polytechnique de Thiès (Sénégal)
Financement : Lacuna Fund

Langues : wolof (wol), pulaar (fuc), sereer (srr)
Format audio : WAV, 16 kHz, 16 bits, mono
Format transcription : .stm (NIST — priorité pour ce projet)
                       .trs (Transcriber XML — également disponible)

Licence : Creative Commons Attribution 4.0 International (CC-BY 4.0)
          → autorise usage commercial, modification, redistribution
          → obligation : attribution (auteurs, licence, lien)
```

**Volumes (wolof, langue prioritaire) :**

| Set | Fichiers | Audio total | Parole annotée |
|-----|----------|-------------|----------------|
| Whole (complet) | 153 | 55h11 | 51h08 |
| **Checked (vérifié)** | **36** | **12h49** | **11h47** |

> **Décision méthodologique :** utiliser le **checked set** pour toute évaluation
> (mini-projet + WER baseline S2), le whole set pour l'entraînement en phase MVP.
> Comparer Whisper à des transcriptions non vérifiées mesure autant les erreurs
> du corpus que celles du modèle — le checked set est le seul honnête pour un WER.

**Typologie et complexité (échelle 1-5 fournie par les auteurs) :**

| Type ID | Type | Wolof | Pulaar | Sereer |
|---------|------|-------|--------|--------|
| 1 | push message | 9 | 1 | 0 |
| 2 | voice message | 0 | 0 | 14 |
| 3 | interview | 22 | 10 | 15 |
| 4 | radio show | **120** | 72 | 67 |
| 5 | focus group | 2 | 0 | 9 |

> **À noter** : 78% du wolof est du radio show. Ces radio shows sont
> **agricoles** (thématique du corpus) — le vocabulaire est déjà proche
> du domaine Ñoo Far. Écart corpus/production plus faible qu'un corpus généraliste.

**Distribution de genre (biais à documenter) :**

- Parole masculine : **88.78%** (wolof)
- Parole féminine : **11.22%** (wolof)

> **Enjeu de biais** : Whisper zéro-shot risque d'être plus performant sur les
> voix masculines. Ton public cible (éleveuses ET éleveurs) exige une évaluation
> **séparée par genre** dans le rapport baseline S4. Le label `<o,f0,female>` /
> `<o,f0,male>` dans les `.stm` permet ce diagnostic.

**Convention de nommage des fichiers :**

Format : `<ISO 639-2>_<type_id>_<dirname_id>_<file_id>_<subpart>`

Exemple : `wol_43612` = wolof, type 4 (radio show), dossier 36, fichier 1, sous-partie 2

> **Utilité pratique** : filtrer intelligemment les 3 audios du mini-projet en
> décodant le nom (choisir un `type_id=1` pour audio "facile", un long radio
> show pour audio "complexe").

**Citation bibliographique (BibTeX pour dossier et README) :**

```bibtex
@inproceedings{kallaama2024dataset,
  title={Kallaama: A Transcribed Speech Dataset about Agriculture
         in the Three Most Widely Spoken Languages in Senegal},
  author={Gauthier, Elodie and Ndiaye, Aminata and Guissé, Abdoulaye},
  booktitle={Proceedings of the Fifth workshop on Resources for
             African Indigenous Languages (RAIL 2024)},
  year={2024}
}
```

> **Ancrage écosystème** : RAIL est LE workshop des langues africaines en NLP,
> Lacuna Fund est le fonds de référence pour combler les lacunes de données IA
> en Afrique. Deux ancrages qui s'inscrivent visiblement dans l'écosystème
> Masakhane — à mentionner dans ton dossier de bourse.

### 1.2 — Conventions d'annotation KALLAAMA (à connaître avant tout code)

Le corpus a **deux conventions d'annotation** clairement définies. C'est un atout majeur — tu peux les exploiter pour des analyses différenciées.

**Convention 1 — Disfluences (préfixe `%`)**

Un token commençant par `%` marque une hésitation ou un marqueur discursif :
- Exemples : `%e`, `%hum`
- Exemple en corpus : `wol_43611.trs: %e prévision : fra météo :fra yi xibaar yi si jaww ji`

**Convention 2 — Emprunts / code-switching (suffixe `:lang`)**

Un token suivi de `:<code_langue>` marque un emprunt à une autre langue :
- Exemples : `météo :fra`, `microphone :fra`, `bisimilah :ar`, `marketing :en`
- Un exemple particulièrement riche : `wol_43112.trs: bisimilah :ar donc :fra looy yok`
  → wolof + mot arabe + mot français dans la même phrase (réalité linguistique sénégalaise)

**Variantes à gérer dans le parsing** (annotateurs pas toujours cohérents) :
- ISO 639-2 (`:fra`) OU ISO 639-1 (`:fr`) — les deux existent
- Espace parfois ajouté avant les deux-points (`accompagnement : fra`)
- La fonction de nettoyage doit être **tolérante** à ces variations

**Implications stratégiques :**

- **Le code-switching est BALISÉ** → tu peux calculer un WER différencié :
  - WER sur segments 100% wolof (aucun `:lang`)
  - WER sur segments avec code-switching (par langue empruntée)
  - Le vrai chiffre à donner dans le rapport baseline n'est pas un WER moyen mais ces sous-mesures

- **Les disfluences `%` peuvent gonfler artificiellement le WER** si non traitées.
  Deux WER à calculer : avec disfluences (test dur) et sans (test standard).

**Encodage des fichiers texte :**
À vérifier en ouvrant un `.stm` ou `.trs` dans VS Code (indicateur en bas à droite).
Probablement UTF-8 pour `.stm` (format récent) ; possiblement ISO-8859-1 pour `.trs`.
Point critique pour les caractères wolof `ë`, `ñ`, `à`.

### 1.3 — Préparer l'environnement technique (15 min)

**Vérifications :**

Ouvre PowerShell et confirme que ton environnement est prêt :

```powershell
cd C:\dev\noo-far-pipeline
conda activate noofar
python -c "import librosa, numpy, pandas, matplotlib; print('OK')"
```

Si ça affiche `OK`, tu es prêt. Sinon, tu sauras ce qui manque avant de commencer.

**Structure des dossiers :**

Vérifie/crée l'arborescence :

```
C:\dev\noo-far-pipeline\
├── notebooks\                    ← existe déjà
└── data\                         ← à créer si pas là (dans .gitignore)
    └── kallaama\                 ← à créer, y placer les audios + .trs
```

Depuis PowerShell dans le dépôt :

```powershell
mkdir data\kallaama -Force
```

Rappel important : `data/` est dans ton `.gitignore` — les audios ne seront jamais commités, seuls les notebooks les référencent.

### 1.4 — Vérifier le kernel Jupyter dans VS Code (5 min)

Ouvre VS Code sur le dépôt, crée un notebook de test rapide `notebooks/test_kernel.ipynb`, tape :

```python
import sys
print(sys.executable)
```

Le chemin affiché doit contenir `noofar` (par exemple `...\conda\envs\noofar\python.exe`). Si ce n'est pas le cas, clique en haut à droite du notebook sur le kernel et sélectionne `noofar`. **Fais ce test avant d'écrire quoi que ce soit d'autre** — c'est le piège classique qui fait perdre 30 min si négligé.

Une fois vérifié, supprime `test_kernel.ipynb`.

---

<a name="étape-1"></a>
## 2. Étape 1 — Récupérer et organiser les données (~30 min)

### 2.1 — Télécharger KALLAAMA

Selon la source identifiée en 1.1 :

**Si sur Hugging Face** (le plus probable) :

```python
from datasets import load_dataset
ds = load_dataset("nom_utilisateur/kallaama")
```

Puis explorer la structure du dataset, itérer sur les échantillons, sauvegarder les WAV et les `.trs` dans `data/kallaama/`.

**Si téléchargement direct** (archive `.zip` ou `.tar.gz`) :
- Télécharger avec un navigateur ou `curl`.
- Extraire dans `data/kallaama/`.
- Vérifier que les paires `.wav`/`.trs` sont bien présentes.

### 2.2 — Choisir 3 audios représentatifs

Ne prends pas les 3 premiers alphabétiquement — choisis-les avec un peu d'intention pour que ton analyse soit riche :

- **Audio 1 — "propre"** : bon rapport signal/bruit, un seul locuteur, durée moyenne. Ta baseline "facile".
- **Audio 2 — "bruité ou dégradé"** : bruit de fond, ou enregistrement téléphonique, ou parole rapide. Ta baseline "difficile".
- **Audio 3 — "varié"** : plusieurs locuteurs, ou code-switching visible dans la transcription, ou registre différent. Ta baseline "réaliste".

Cette diversité rendra la synthèse comparative beaucoup plus intéressante qu'avec 3 audios similaires.

### 2.3 — Vérifier les paires

Pour chaque audio choisi, confirmer :
- Le `.wav` est lisible (double-clic → il joue dans un lecteur).
- Le `.trs` associé existe (même nom, extension différente).
- Le `.trs` s'ouvre dans VS Code (c'est du texte XML lisible).

Note les 3 chemins dans un fichier ou un post-it — tu les réutiliseras.

---

<a name="étape-2"></a>
## 3. Étape 2 — Exploration globale du corpus (~30 min)

Avant de zoomer sur 3 audios, une vue d'ensemble. C'est l'occasion d'exercer Pandas sur des données réelles.

### 3.1 — Inventorier tous les fichiers

```python
from pathlib import Path
import pandas as pd

corpus_dir = Path("../data/kallaama")   # depuis notebooks/
wav_files = list(corpus_dir.glob("**/*.wav"))
trs_files = list(corpus_dir.glob("**/*.trs"))

print(f"Nombre de .wav : {len(wav_files)}")
print(f"Nombre de .trs : {len(trs_files)}")
```

**À observer :**
- Y a-t-il autant de `.wav` que de `.trs` ? Sinon, il y a des orphelins — à noter.
- La convention de nommage est-elle cohérente (même nom, extension différente) ?

### 3.2 — Statistiques de taille

```python
df = pd.DataFrame({"path": wav_files})
df["name"] = df["path"].apply(lambda p: p.stem)
df["size_mb"] = df["path"].apply(lambda p: p.stat().st_size / 1e6)
df.describe()
df["size_mb"].hist(bins=30)
```

**À observer et documenter :**
- Distribution des tailles : uniforme ou très variable ?
- Taille totale du corpus.
- Nombre médian, minimum, maximum.

### 3.3 — Estimer la durée totale (bonus)

Si tu as le temps, itérer sur les fichiers pour récupérer les durées via `librosa.get_duration(path=str(p))`. Attention, c'est long sur un gros corpus — limite à un échantillon si nécessaire.

---

<a name="étape-3"></a>
## 4. Étape 3 — Écrire le parseur `.stm` (~45 min)

**Choix de format : `.stm` plutôt que `.trs`.** KALLAAMA fournit les deux formats. Le `.stm` (NIST Segment Time Mark) est **le standard international d'évaluation ASR**, plus simple à parser, aligné sur les conventions du domaine. C'est ce que tu utiliseras pour ce mini-projet ET pour le WER baseline en S2.

### 4.1 — Structure d'un fichier `.stm`

Format texte plat, ligne par ligne :

```
<nom_fichier> <canal> <locuteur> <debut> <fin> <label> <transcription>
```

Exemple concret :

```
wol_43611 1 spk1 0.00 5.24 <o,f0,female> texte transcrit du segment
```

Le label `<o,f0,female>` (ou `<o,f0,male>`) est précieux — il donne le **genre du locuteur**, utile pour l'analyse par genre du WER.

### 4.2 — Coder la fonction

```python
def parse_stm(stm_path, encoding='utf-8'):
    """
    Parse un fichier NIST STM et retourne la liste des segments.
    
    Retourne : liste de dicts {file, channel, speaker, start, end, label, text}
    """
    segments = []
    with open(stm_path, encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';;'):  # commentaires STM
                continue
            parts = line.split(maxsplit=6)
            if len(parts) < 7:
                continue
            segments.append({
                "file": parts[0],
                "channel": parts[1],
                "speaker": parts[2],
                "start": float(parts[3]),
                "end": float(parts[4]),
                "label": parts[5],
                "text": parts[6],
            })
    return segments
```

### 4.3 — Fonction de nettoyage pour le WER

Le texte brut contient les conventions KALLAAMA (`%` disfluences, `:lang` emprunts). Pour comparer à Whisper, il faut nettoyer :

```python
import re

def clean_text_for_wer(text, strip_disfluencies=True, strip_lang_tags=True):
    """
    Nettoie une transcription KALLAAMA pour le calcul du WER.
    
    - Disfluences (%e, %hum) : optionnellement retirées
    - Tags de langue (:fra, :en, :ar, :fr...) : optionnellement retirés
      (on garde le mot emprunté, on retire juste le tag)
    """
    if strip_lang_tags:
        # Gère :fra, :fr, : fra, : fr — tolérant aux variations d'annotateurs
        text = re.sub(r'\s*:\s*[a-z]{2,3}\b', '', text)
    
    if strip_disfluencies:
        # Retire les tokens commençant par %
        text = re.sub(r'\s*%\S+\s*', ' ', text)
    
    # Normaliser les espaces multiples
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text
```

**Stratégie recommandée** : dans ton DataFrame de segments, garder les deux versions :
- `text_raw` : brut (avec `%` et `:lang`) — utile pour analyse fine
- `text_clean` : nettoyé — utilisé pour le WER

### 4.4 — Tester les fonctions

```python
segments = parse_stm("../data/kallaama/wol_XXX.stm")
print(f"Nombre de segments : {len(segments)}")

# Décompte par genre (utile pour l'analyse de biais)
from collections import Counter
genres = Counter("female" if "female" in s["label"] else "male" for s in segments)
print(f"Genres : {dict(genres)}")

# Aperçu de segments avec nettoyage
for seg in segments[:5]:
    clean = clean_text_for_wer(seg["text"])
    print(f"[{seg['start']:.1f}s → {seg['end']:.1f}s | {seg['speaker']}]")
    print(f"  Brut    : {seg['text']}")
    print(f"  Nettoyé : {clean}")
```

**Points à vérifier :**
- Les caractères wolof (`ë`, `ñ`) s'affichent correctement — sinon, l'encodage est faux (essayer `encoding='iso-8859-1'`)
- Les timestamps sont croissants et cohérents
- Le nettoyage retire bien `:fra`, `%e`, etc.

### 4.5 — Fonction utilitaire : extraction de segment audio

```python
def extract_segment(audio, sr, start, end):
    """Retourne l'array audio correspondant au segment [start, end] en secondes."""
    return audio[int(start * sr):int(end * sr)]
```

C'est court, mais c'est le geste fondamental — l'illustration parfaite qu'un audio est un array NumPy qu'on découpe par indices calculés à partir des temps.

### 4.6 — Note sur le `.trs` (optionnel, pour information)

Si tu veux comparer les deux formats à titre pédagogique, un parser `.trs` équivalent nécessite `xml.etree.ElementTree`, gérer la structure hiérarchique `Turn → Sync`, et attention au piège : **le texte est dans `sync.tail` (pas `sync.text`)**. C'est plus complexe et sujet à erreurs — d'où le choix du `.stm` pour ce projet.

---

<a name="étape-4"></a>
## 5. Étape 4 — Analyse détaillée des 3 audios (~2h30)

Pour chaque audio, refais la même structure. Ça rend le notebook lisible et comparatif.

### Template par audio (~50 min chacun)

**A. Chargement et métadonnées :**

```python
import librosa
import matplotlib.pyplot as plt

audio_path = "../data/kallaama/audio_001.wav"
trs_path = "../data/kallaama/audio_001.trs"

audio, sr = librosa.load(audio_path, sr=16000, mono=True)
duree = len(audio) / sr
print(f"Fichier : {Path(audio_path).name}")
print(f"Durée : {duree:.1f}s | Sample rate : {sr} Hz | Canaux : mono")
```

**B. Segments (parsing `.stm` + genre + nettoyage) :**

```python
segments = parse_stm(stm_path)
df_seg = pd.DataFrame(segments)
df_seg["duration"] = df_seg["end"] - df_seg["start"]
df_seg["text_clean"] = df_seg["text"].apply(clean_text_for_wer)
df_seg["gender"] = df_seg["label"].apply(
    lambda l: "female" if "female" in l else "male"
)

print(f"Nombre de segments : {len(df_seg)}")
print(f"Durée moyenne : {df_seg['duration'].mean():.1f}s")
print(f"Locuteurs : {df_seg['speaker'].unique().tolist()}")
print(f"Genres : {df_seg['gender'].value_counts().to_dict()}")

# Repérer segments avec code-switching (utile pour synthèse)
df_seg["has_codeswitch"] = df_seg["text"].str.contains(r':\s*[a-z]{2,3}\b', regex=True)
print(f"Segments avec code-switching : {df_seg['has_codeswitch'].sum()}/{len(df_seg)}")

df_seg.head()
```

**C. Forme d'onde complète :**

```python
plt.figure(figsize=(14, 3))
librosa.display.waveshow(audio, sr=sr)
plt.title(f"Forme d'onde — {Path(audio_path).name}")
# Bonus : superposer les frontières de segments
for start in df_seg["start"]:
    plt.axvline(start, color='red', alpha=0.2, linewidth=0.5)
plt.tight_layout()
plt.show()
```

**D. Spectrogramme complet :**

```python
import numpy as np

D = librosa.stft(audio)
S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)

plt.figure(figsize=(14, 4))
librosa.display.specshow(S_db, sr=sr, x_axis="time", y_axis="hz")
plt.colorbar(format="%+2.0f dB")
plt.title(f"Spectrogramme — {Path(audio_path).name}")
plt.tight_layout()
plt.show()
```

**E. Zoom sur un segment :**

Choisir un segment (par exemple le premier, ou un mot clair) :

```python
seg = segments[0]
clip = extract_segment(audio, sr, seg["start"], seg["end"])

fig, axes = plt.subplots(2, 1, figsize=(12, 5))
librosa.display.waveshow(clip, sr=sr, ax=axes[0])
axes[0].set_title(f"Segment : « {seg['text']} »")

D_clip = librosa.stft(clip)
S_clip_db = librosa.amplitude_to_db(np.abs(D_clip), ref=np.max)
librosa.display.specshow(S_clip_db, sr=sr, x_axis="time", y_axis="hz", ax=axes[1])
plt.tight_layout()
plt.show()
```

**F. Écoute du segment (dans le notebook) :**

```python
from IPython.display import Audio, display
display(Audio(clip, rate=sr))
```

**Ce que tu observes pour chaque audio, à noter en markdown après les visualisations :**
- Rapport signal/bruit apparent
- Rythme de parole (rapide/lent)
- Silences (nombreux/rares)
- Structure spectrale (voix claire ? étouffée ?)
- Correspondance visible entre le texte et le signal

---

<a name="étape-5"></a>
## 6. Étape 5 — Synthèse comparative (~30 min)

Cellule markdown finale du notebook. Pas un rapport formel — quelques observations qui rendent l'exercice utile pour la suite.

**Structure suggérée :**

```markdown
## Synthèse

### Comparaison des 3 audios (checked set)

| Fichier | Type | Rating | Durée | Segments | Genres | Code-switching | Complexité audio |
|---------|------|--------|-------|----------|--------|----------------|------------------|
| wol_XXX | push message | 1 | 2min | 15 | 1 M | non | claire |
| wol_YYY | radio show | 4 | 30min | 200 | 3 M / 1 F | oui (fra) | radio, propre |
| wol_ZZZ | radio show | 5 | 45min | 350 | 4 M / 2 F | oui (fra+ar) | radio, bruit ambiant |

### Ce que j'ai observé sur le corpus

**Sur la parole :**
- ...

**Sur les conventions d'annotation :**
- Disfluences `%e`, `%hum` présentes dans X% des segments
- Code-switching avec le français : Y% des segments
- Emprunts arabes (bisimilah) présents dans les émissions religieuses/culturelles
- ...

**Sur le biais de genre observé dans mes 3 audios :**
- Répartition : ... (à comparer au 88.8% masculin global du corpus)
- ...

### Difficultés anticipées pour Whisper zéro-shot

- Vocabulaire technique agricole/élevage wolof probablement peu représenté
  dans le pré-entraînement Whisper
- Code-switching wolof-français fréquent → risque de bascule de langue par Whisper
- Variabilité des conditions d'enregistrement (studio radio vs terrain)
- Voix féminines sous-représentées → performance probablement dégradée
- ...

### Décisions méthodologiques pour la S2 (WER baseline)

- **Set d'évaluation** : checked set (12h49 wolof, 36 fichiers) — seul honnête
- **Nettoyage avant WER** : retirer `%<disfluence>` et `:<lang>` (fonction déjà écrite)
- **WER à calculer** :
  - Global (sur checked set complet)
  - Par genre (masculin vs féminin) — pour révéler le biais
  - Par présence de code-switching (segments purs vs mixtes)
- **Sample de test** : viser 30-50 énoncés variés, échantillonnés dans les 3 catégories
  de complexité (rating 1-2, 3, 4-5)
- **Encodage** : ... (documenté ici après vérification)

### Points ouverts pour l'analyse d'erreurs S4

- Les disfluences non transcrites par Whisper vont-elles gonfler artificiellement
  le WER ? (comparer WER avec/sans disfluences)
- Le code-switching wolof-français est-il mieux géré que le wolof pur ?
  (Whisper connaît le français, donc peut-être...)
- La proximité thématique agricole du corpus se traduit-elle par une bonne
  performance sur ces mots-clés ?
```

Cette synthèse est ton livrable **intellectuel** — elle prépare ton travail des semaines suivantes, particulièrement le rapport baseline de S4.

---

<a name="étape-6"></a>
## 7. Étape 6 — Finition et commit (~30 min)

### 7.1 — Nettoyer le notebook

- Réordonner les cellules pour une lecture logique
- Supprimer les cellules de tâtonnement, les tests abandonnés
- Ajouter une cellule markdown d'introduction en haut :

```markdown
# Mini-projet KALLAAMA — Exploration de 3 audios

**Objectif :** premier contact avec le corpus KALLAAMA, valider les gestes
Librosa/Pandas/parsing XML, préparer le WER baseline de la S2.

**Méthode :** analyse de 3 audios choisis pour leur diversité
(propre / bruité / multi-locuteurs), parsing des `.trs`, visualisations
(forme d'onde, spectrogramme), écoute, synthèse comparative.

**Auteur :** Serigne-Dan, [date]
```

### 7.2 — Test de reproductibilité

Kernel → Restart & Run All. Le notebook doit tourner de bout en bout sans erreur. Si ça plante, corrige. C'est le test qui garantit qu'un autre (ou toi dans 3 semaines) pourra le rejouer.

### 7.3 — Commit

```powershell
cd C:\dev\noo-far-pipeline
git add notebooks/01_kallaama_exploration.ipynb
git commit -m "Mini-projet KALLAAMA : exploration de 3 audios"
git push
```

Vérifie que **seul le notebook** est ajouté (les audios dans `data/` doivent rester ignorés par Git). Un `git status` avant commit le confirmera.

---

<a name="vigilance"></a>
## 8. Points de vigilance

Quatre choses qui peuvent te faire perdre du temps ou dégrader la qualité de l'évaluation si tu ne les anticipes pas.

### 8.1 — Puiser dans le CHECKED set (36 fichiers wolof), pas le whole set

Le corpus contient 153 fichiers wolof, mais seulement 36 ont des transcriptions **vérifiées humainement**. Pour ce mini-projet et le WER baseline S2, **utiliser exclusivement le checked set** — sinon tu compares Whisper à des transcriptions potentiellement fautives.

Le checked set se trouve dans un sous-dossier dédié du corpus (à confirmer lors du téléchargement, souvent `checked/` ou similaire).

### 8.2 — Choisir 3 audios avec gradation intentionnelle de complexité

Le corpus fournit une **échelle de complexité 1-5** par type de programme. Utilise-la :

- **Audio 1 (facile)** — `type_id=1` (push message) ou `type_id=3` court (interview), rating 1-2
- **Audio 2 (difficile)** — `type_id=4` (radio show), rating 4-5, idéalement multi-locuteurs
- **Audio 3 (varié)** — `type_id=3` ou `4`, code-switching wolof-français visible dans le `.stm`

Cette gradation intentionnelle rendra ta synthèse comparative bien plus riche qu'un choix aléatoire.

### 8.3 — L'encodage des fichiers texte

Symptôme : les caractères wolof (`ë`, `ñ`, `à`) apparaissent mangés (`Ã«`, `Ã±`).

**Test rapide, à faire une seule fois** : ouvre un `.stm` dans VS Code — en bas à droite, l'indicateur affiche l'encodage détecté. Note-le, tu sauras une fois pour toutes.

- Si UTF-8 : `parse_stm(path)` (paramètre par défaut)
- Si ISO-8859-1 : `parse_stm(path, encoding='iso-8859-1')`

### 8.4 — Documenter le biais de genre dans la synthèse

88.8% de la parole wolof est masculine. Ce n'est pas ton problème, c'est un fait du corpus — **à documenter, pas à cacher**. Dans ta synthèse :

- Compter les segments féminins vs masculins dans tes 3 audios (via le label `<o,f0,female>` / `<o,f0,male>` des `.stm`)
- Noter que le rapport baseline S4 devra calculer un **WER séparé par genre** pour révéler ou infirmer ce biais dans les performances de Whisper

C'est le type de rigueur méthodologique qu'un évaluateur Masakhane cherche.

### 8.5 — Ne pas viser la perfection

L'objectif est de **te confronter au corpus**, pas de produire une analyse exhaustive. Trois audios suffisent largement pour l'intuition. Si un audio te résiste (fichier corrompu, encodage bizarre, `.stm` mal formé), **passe au suivant**. Ne t'entête pas.

Si tu bloques plus de 30 min sur un problème technique unique, c'est un signal — pose la question, mets une note dans le notebook, avance.

---

<a name="annexe"></a>
## 9. Annexe — Structure attendue du notebook

Récapitulatif de l'organisation cible :

```
01_kallaama_exploration.ipynb
├── [markdown] Titre + objectif + méthode
├── [code] Imports (librosa, numpy, pandas, matplotlib, ET)
├── [markdown] ## 1. Exploration globale du corpus
├── [code] Inventaire des fichiers, stats
├── [markdown] ## 2. Fonction de parsing .trs
├── [code] Définition parse_trs + test
├── [markdown] ## 3. Audio 1 — [nom]
├── [code] Chargement + segments + waveform + spectrogramme + zoom + écoute
├── [markdown] Observations audio 1
├── [markdown] ## 4. Audio 2 — [nom]
├── [code] ... (même structure)
├── [markdown] Observations audio 2
├── [markdown] ## 5. Audio 3 — [nom]
├── [code] ... (même structure)
├── [markdown] Observations audio 3
├── [markdown] ## 6. Synthèse comparative
└── [markdown] Tableau + observations + difficultés anticipées
```

---

## Le fruit du mini-projet

À la fin de samedi matin, tu ressortiras avec :

- ✅ Un **notebook livré** dans `notebooks/`, commité et reproductible
- ✅ Une **fonction `parse_trs` réutilisable** — tu la reprendras en S2 pour le WER
- ✅ Une **intuition sensorielle** du corpus KALLAAMA (à quoi ça sonne, où sont les difficultés)
- ✅ Des **compétences intégrées** (Librosa + XML + Pandas + matplotlib) plus jamais isolées
- ✅ Une **synthèse écrite** qui préparera l'analyse du WER en S2

Bonne exploration.