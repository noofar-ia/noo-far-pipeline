# Guide d'installation — Ñoo Far Pipeline

Ce guide t'amène d'un dépôt cloné à un environnement de développement
fonctionnel et vérifié. Il couvre **Windows**, **macOS** et **Linux/Codespace**,
avec les pièges spécifiques à chaque système.

Le projet utilise **deux environnements conda séparés** :
- `noofar` → le pipeline (ASR, RAG, TTS, app) — stack **PyTorch**
- `noofar-rasa` → le service NLU — stack **TensorFlow**, incompatible avec le premier

> ⚠️ Les deux environnements ne doivent **jamais** être fusionnés : Rasa (TensorFlow)
> et le pipeline (PyTorch) ont des dépendances incompatibles. C'est pour cela
> qu'ils sont isolés et communiquent par HTTP.

---

## Prérequis (tous OS)

- **conda** (Anaconda ou Miniconda)
- **git**
- **Python 3.10** (imposé par Rasa 3.6.x ; utilisé partout pour la cohérence)
- Un éditeur (VS Code recommandé)

---

## 1. Cloner le dépôt

```bash
git clone https://github.com/noofar-ia/noo-far-pipeline
cd noo-far-pipeline
```

> **Windows** : travaille dans un chemin court hors OneDrive (ex. `C:\dev\noo-far-pipeline`)
> pour éviter les conflits de synchronisation.

---

## 2. Environnement du pipeline (`noofar`)

```bash
conda create -n noofar python=3.10 -y
conda activate noofar
```

### ⚠️ Piège Windows / PowerShell

Si `conda activate` renvoie « Run 'conda init' before 'conda activate' » :

```powershell
conda init powershell
```

Puis **ferme complètement le terminal et rouvre-en un neuf** (l'init ne prend
effet que dans un terminal ouvert après la commande).

Si au redémarrage tu vois « l'exécution de scripts est désactivée sur ce système » :

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

(confirme avec `O`), puis referme et rouvre encore le terminal.
L'invite doit afficher `(noofar)` avant de continuer.

---

## 3. ffmpeg

Requis pour convertir l'audio (OGG WhatsApp → WAV). Installe-le **dans**
l'environnement, c'est portable sur tous les OS :

```bash
conda activate noofar
conda install -c conda-forge ffmpeg
```

> **Windows** : `sudo apt-get install ffmpeg` NE marche PAS (`apt` n'existe pas).
> Utilise la commande conda ci-dessus.
> Les avertissements `gdk-pixbuf` pendant l'install sont inoffensifs.

Vérifie :
```bash
ffmpeg -version
```

---

## 4. Dépendances du pipeline

Vérifie d'abord que tu es dans le bon environnement :

```bash
python --version          # doit afficher 3.10.x
pip --version             # le chemin doit contenir ...noofar...
```

Puis installe depuis le lock (versions exactes, reproduction à l'identique) :

```bash
pip install --upgrade pip
pip install -r requirements.lock.txt
```

> C'est long (torch + écosystème Hugging Face). Normal.

---

## 5. Environnement NLU (`noofar-rasa`)

Environnement **séparé** pour Rasa. Voir aussi [`nlu/README.md`](nlu/README.md).

```bash
conda create -n noofar-rasa python=3.10 -y
conda activate noofar-rasa
pip install --upgrade pip
pip install rasa==3.6.21
```

> Les avertissements de conflit avec `ipython` / `jupyter` sont **sans gravité** :
> ils concernent des outils notebook qu'on n'utilise pas dans cet environnement.

Vérifie :
```bash
rasa --version            # doit afficher Rasa 3.6.21
```

> ⚠️ **macOS Apple Silicon (M1/M2/M3)** : Rasa 3.6.x repose sur TensorFlow, dont le
> support sur puces Apple peut être capricieux. Si l'installation de Rasa échoue
> sur Mac, c'est un problème connu — noter et traiter séparément.

---

## 6. Configuration (secrets)

```bash
cp config/.env.example config/.env
```

Puis édite `config/.env` avec tes tokens :
- `HF_TOKEN` — https://huggingface.co/settings/tokens (pour télécharger les modèles)
- `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` — https://console.twilio.com (canal WhatsApp)

> ⚠️ Le vrai `config/.env` ne doit **JAMAIS** être commité (il est dans `.gitignore`).
> Vérifie avec `git status` qu'il n'apparaît pas. Seul `.env.example` est versionné.

---

## 7. Vérification finale

Dans l'environnement `noofar` :

```bash
python -c "import torch, transformers; print('torch', torch.__version__, '| transformers', transformers.__version__)"
```

Si ça affiche les versions sans erreur → le pipeline est prêt.
Dans `noofar-rasa`, `rasa --version` doit répondre → le NLU est prêt.

---

## Notes par système

**Windows** : shell PowerShell (pas Git Bash). Pièges principaux : `conda init` +
redémarrage du terminal, `Set-ExecutionPolicy`, ffmpeg via conda (pas apt).

**macOS (prévu août)** : Apple Silicon. Le pipeline (torch) fonctionne bien (MPS).
Rasa/TensorFlow peut nécessiter des ajustements. Le lock `requirements-rasa.txt`
contient des paquets Windows (`pywin32`, `pyreadline3`) — à régénérer sur Mac.

**Linux / Codespace** : le plus simple. `apt-get install ffmpeg` fonctionne
nativement. Le Codespace monte automatiquement l'environnement pipeline via
`.devcontainer/` (Rasa se lance à la main dans un second terminal).

---

## Alternative sans installation : Codespace

Pour développer sans rien installer (machine empruntée, voyage, ou en attendant
une nouvelle machine) : depuis GitHub, bouton **Code → Codespaces → Create
codespace**. L'environnement pipeline se monte tout seul. Idéal comme poste de
secours.
