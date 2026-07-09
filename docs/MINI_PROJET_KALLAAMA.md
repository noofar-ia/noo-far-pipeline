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

### 1.1 — Localiser et comprendre le corpus KALLAAMA

**À trouver :**
- La **source officielle** du corpus KALLAAMA — probablement sur Hugging Face (`https://huggingface.co/datasets/...`) ou sur un site académique (ISRA, UGB, GitHub d'un chercheur).
- La **licence** — indispensable pour ton dossier de projet et pour savoir si tu peux redistribuer.
- La **taille totale** (Go) — pour anticiper le téléchargement.
- Le **format audio** (WAV, MP3, FLAC ?), la **fréquence d'échantillonnage** (8 kHz, 16 kHz, 44.1 kHz ?), le **nombre de canaux** (mono/stéréo).
- La **structure des fichiers de transcription** — confirmer que ce sont bien des `.trs` (Transcriber XML) et pas un autre format.
- Le **nombre total d'heures** de parole annotée.

**Actions :**
- Google : `KALLAAMA dataset wolof` — trouver la source officielle.
- Lire l'article scientifique ou le README associé (souvent un papier court accompagne le corpus).
- Noter la citation bibliographique (auteurs, année, titre, DOI si présent) — tu la réutiliseras dans ton rapport baseline (S4).

**À documenter dans ta note de préparation** (peut être un simple bloc markdown en début de notebook plus tard) :

```
Corpus : KALLAAMA
Source : [URL]
Auteurs : [noms]
Licence : [MIT / CC-BY / autre]
Taille : [X Go, Y heures]
Format audio : [WAV 16 kHz mono ? ou autre]
Format transcription : Transcriber .trs (XML)
```

### 1.2 — Lire la documentation du corpus (15 min)

Avant de manipuler un seul fichier, lis le README / la doc / le papier. Cherche spécifiquement :

- Les **conventions d'annotation** : que signifient les crochets (`[rire]`, `[bruit]`), les parenthèses, les tags spéciaux ? Y a-t-il des marqueurs de code-switching wolof-français ?
- Les **codes des locuteurs** (`spk1`, `spk2`, ou autres conventions).
- Les **variantes orthographiques du wolof** utilisées (le wolof a plusieurs orthographes en usage : orthographe académique avec `ë`, `ñ`, ou orthographe francisée).
- L'**encodage** des fichiers `.trs` — souvent ISO-8859-1 pour les vieux Transcriber, parfois UTF-8. **Point critique** pour les caractères wolof.
- Les **conditions d'enregistrement** : studio ? terrain ? téléphone ? Ça explique la variabilité audio que tu vas observer.

Note ce que tu apprends — ça alimentera ta cellule de synthèse à la fin.

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
## 4. Étape 3 — Écrire le parseur `.trs` (~1h)

C'est le cœur technique du mini-projet. Une fonction propre et réutilisable — tu la reprendras en S2 pour le WER baseline.

### 4.1 — Comprendre la structure d'un `.trs`

Ouvre un `.trs` dans VS Code et observe. Structure XML type :

```xml
<?xml version="1.0" encoding="ISO-8859-1"?>
<Trans scribe="..." audio_filename="..." version="...">
  <Speakers>
    <Speaker id="spk1" name="..." />
  </Speakers>
  <Episode>
    <Section type="report" startTime="0" endTime="245.3">
      <Turn speaker="spk1" startTime="0.0" endTime="12.4">
        <Sync time="0.0"/>
        texte du premier segment
        <Sync time="5.2"/>
        texte du segment suivant
      </Turn>
    </Section>
  </Episode>
</Trans>
```

**Point crucial :** le texte n'est PAS dans la balise `<Sync>`, il est **après** — dans son attribut `.tail` en `xml.etree`.

### 4.2 — Coder la fonction

```python
import xml.etree.ElementTree as ET

def parse_trs(trs_path, encoding="ISO-8859-1"):
    """
    Parse un fichier Transcriber .trs et retourne la liste des segments.

    Retourne : liste de dicts {start, end, text, speaker}
    """
    with open(trs_path, encoding=encoding) as f:
        tree = ET.parse(f)
    root = tree.getroot()
    segments = []

    for turn in root.iter("Turn"):
        speaker = turn.get("speaker", "?")
        turn_end = float(turn.get("endTime"))
        syncs = turn.findall("Sync")

        for i, sync in enumerate(syncs):
            start = float(sync.get("time"))
            end = float(syncs[i + 1].get("time")) if i + 1 < len(syncs) else turn_end
            text = (sync.tail or "").strip()
            if text:
                segments.append({
                    "start": start,
                    "end": end,
                    "text": text,
                    "speaker": speaker,
                })

    return segments
```

### 4.3 — Tester la fonction

```python
segments = parse_trs("../data/kallaama/audio_001.trs")
print(f"Nombre de segments : {len(segments)}")
for seg in segments[:5]:
    print(f"[{seg['start']:.1f}s → {seg['end']:.1f}s | {seg['speaker']}] {seg['text']}")
```

**Points à vérifier :**
- Les caractères wolof (`ë`, `ñ`) s'affichent correctement — sinon, l'encodage est faux.
- Les timestamps sont croissants et cohérents.
- Le texte n'est pas vide (sinon, tu utilises `.text` au lieu de `.tail`).

### 4.4 — Fonction utilitaire : segment audio

Fonction qui découpe un segment temporel de l'audio :

```python
def extract_segment(audio, sr, start, end):
    """Retourne l'array audio correspondant au segment [start, end] en secondes."""
    return audio[int(start * sr):int(end * sr)]
```

C'est court, mais c'est le geste fondamental — l'illustration parfaite qu'un audio est un array NumPy qu'on découpe par indices calculés à partir des temps.

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

**B. Segments (parsing) :**

```python
segments = parse_trs(trs_path)
df_seg = pd.DataFrame(segments)
df_seg["duration"] = df_seg["end"] - df_seg["start"]

print(f"Nombre de segments : {len(df_seg)}")
print(f"Durée moyenne : {df_seg['duration'].mean():.1f}s")
print(f"Locuteurs : {df_seg['speaker'].unique().tolist()}")
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

### Comparaison des 3 audios
| Fichier | Durée | Segments | Locuteurs | Observations |
|---------|-------|----------|-----------|--------------|
| audio_001 | 2min | 15 | 1 | Voix claire, studio |
| audio_002 | 3min | 22 | 1 | Bruit de fond, terrain |
| audio_003 | 1min30 | 12 | 2 | Code-switching wo/fr visible |

### Ce que j'ai observé sur le corpus
- ...

### Difficultés anticipées pour Whisper zéro-shot
- Vocabulaire technique wolof (élevage) probablement pas dans le pré-entraînement
- Code-switching wolof-français fréquent
- Variabilité des conditions d'enregistrement
- ...

### Conventions d'annotation détectées
- `[rire]`, `[bruit]` : événements non-verbaux
- `(mot)` : mot incertain pour le transcripteur
- ...

### Pour la S2 (WER baseline wolof)
- Nettoyer les annotations avant comparaison
- Attention à l'encodage
- ...
```

Cette synthèse est ton livrable **intellectuel** — elle prépare ton travail des semaines suivantes.

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

Trois choses qui peuvent te faire perdre du temps si tu ne les anticipes pas.

### 8.1 — L'encodage des `.trs`

Symptôme : les caractères wolof (`ë`, `ñ`, `à`) apparaissent mangés (`Ã«`, `Ã±`) dans les résultats.

Cause : le fichier est en ISO-8859-1 mais Python le lit en UTF-8 par défaut.

Solution : toujours ouvrir avec l'encodage explicite (voir la fonction `parse_trs` — paramètre `encoding="ISO-8859-1"`). Si le fichier est en UTF-8, essaie sans le paramètre ou avec `encoding="utf-8"`.

**Test rapide :** ouvrir un `.trs` dans VS Code — en bas à droite, VS Code affiche l'encodage détecté.

### 8.2 — Les segments multi-locuteurs

Certains `Turn` ont plusieurs locuteurs (attribut `speaker="spk1 spk2"` avec des balises `<Who>` à l'intérieur). Le parseur ci-dessus les traite comme un locuteur unique — c'est OK pour ce mini-projet.

Si un audio est majoritairement multi-locuteurs, note-le dans ta synthèse mais ne bloque pas dessus.

### 8.3 — Ne pas viser la perfection

L'objectif est de **te confronter au corpus**, pas de produire une analyse exhaustive. Trois audios suffisent largement pour l'intuition. Si un audio te résiste (fichier corrompu, encodage bizarre, `.trs` mal formé), **passe au suivant**. Ne t'entête pas.

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
