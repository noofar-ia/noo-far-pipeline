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

> ⚠️ **Règle d'or : jamais `pip install --user` dans un environnement conda actif.**
> Ça installe le paquet dans `AppData\Roaming\Python\` (Windows) au lieu de
> l'environnement conda, ce qui crée des conflits silencieux difficiles à
> diagnostiquer (le même paquet existe à deux endroits, Python charge le mauvais).
> Toujours vérifier que le prompt affiche `(noofar)` ou `(noofar-rasa)` avant un
> `pip install`, et ne jamais ajouter `--user`.

---

## Prérequis (tous OS)

- **Miniconda** — pas Anaconda (voir encadré ci-dessous)
- **git**
- **Python 3.10** (imposé par Rasa 3.6.x ; utilisé partout pour la cohérence — fourni par Miniconda, ne pas installer Python séparément depuis python.org)
- Un éditeur (VS Code recommandé)

> ⚠️ **Miniconda, pas Anaconda.** Anaconda embarque ~250 paquets pré-installés
> (souvent des versions anciennes) qui entrent en conflit avec nos environnements
> pinnés. Miniconda n'installe que conda + Python, rien de plus — on installe
> nous-mêmes ce dont on a besoin, dans des environnements isolés et contrôlés.
> Télécharger sur [docs.conda.io/projects/miniconda](https://docs.conda.io/projects/miniconda/en/latest/).
>
> À l'installation (Windows) : cocher **"Add Miniconda3 to my PATH"** et
> **"Register Miniconda3 as my default Python"**, installer "Just Me" (pas
> "All Users" — évite d'avoir besoin des droits admin).

---

## 0. Configurer Git (identité)

Avant tout clone, configure ton identité — sinon tu ne pourras pas commiter :

```bash
git config --global user.name "Ton Nom"
git config --global user.email "TON_ID+ton_username@users.noreply.github.com"
```

> ⚠️ **N'utilise pas ton vrai mail.** Utilise le mail **no-reply** fourni par
> GitHub — il apparaît sur `https://github.com/settings/emails`, section
> "Keep my email addresses private" (à activer si pas déjà fait). Il a la forme
> `12345678+username@users.noreply.github.com`. Ça évite d'exposer ton vrai
> mail dans l'historique public des commits, tout en créditant correctement
> tes contributions sur ton profil GitHub.
>
> Bonus recommandé : sur la même page, coche **"Block command line pushes
> that expose my email"** — GitHub refusera tout commit qui exposerait ton
> vrai mail par erreur.

Vérifie :
```bash
git config --global user.name
git config --global user.email
```

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

Puis installe depuis `requirements.txt` (bornes minimales, mis à jour au fil des
imports réels du code) :

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

> C'est long (torch + écosystème Hugging Face). Normal.

> `requirements.lock.txt` n'est **pas** destiné à l'install : c'est un snapshot
> figé (versions exactes) d'un environnement Kaggle qui a fonctionné pour
> RAG/génération (D1). Sert de référence en cas de régression à isoler, pas de
> source d'install courante.

`peft` (fine-tuning LoRA) et `twilio`/`httpx` (canal WhatsApp) ne sont plus dans
`requirements.txt` : aucun code actuel ne les importe (`asr/train_lora.py` et
`app/channels/whatsapp.py` sont vides). À réintroduire avec leurs contraintes de
version quand ce code sera écrit.

### ⚠️ À anticiper — `datasets` et torchcodec sur Windows

`datasets` n'est pas dans `requirements.txt` aujourd'hui (aucun import dans le
code de production — seulement prévu pour un futur fine-tuning). Quand il sera
réintroduit, attention : les versions récentes (≥ 4.0) utilisent **torchcodec**
pour décoder l'audio, qui est **instable sur Windows** (DLL FFmpeg
introuvables/incompatibles → erreurs à l'import ou au chargement d'un dataset
audio). Forcer une version antérieure règle le problème sans rien perdre en
fonctionnalité pour ce projet :

```bash
pip install "datasets<4.0"
```

> Le lock Kaggle (`requirements.lock.txt`) a validé `datasets==5.0.0` — ça
> fonctionne là-bas (Linux) mais **pas** la contrainte à reprendre sous Windows.

Vérifie que le décodage audio automatique fonctionne :
```bash
python -c "from datasets import load_dataset; ds = load_dataset('PolyAI/minds14', name='en-AU', split='train'); s = ds[0]['audio']; print('OK:', s['array'].shape, s['sampling_rate'])"
```

Si ça affiche `OK: (N,) 8000` sans erreur, c'est bon. Si l'erreur `ASN1: NOT_ENOUGH_DATA`
apparaît à la place, ce n'est **pas** un problème `datasets` — voir l'encadré SSL
plus bas.

> Note connexe : `coqui-tts` (backend Kiriku, dans `requirements.txt`) requiert
> lui aussi `torchcodec` pour son IO audio (depuis torch 2.9), indépendamment de
> `datasets`. La même instabilité Windows peut donc resurgir par ce chemin TTS
> même sans jamais installer `datasets` — à surveiller au premier run TTS réel.

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

> ⚠️ **Si tu vois `ssl.SSLError: [ASN1: NOT_ENOUGH_DATA]`** à l'import de `datasets`,
> `requests`, ou tout paquet réseau : ce n'est **pas** un problème Python, c'est le
> **magasin de certificats Windows qui est corrompu ou obsolète**. Symptôme fréquent
> sur les machines dont les mises à jour de sécurité sont en retard.
>
> **Avant tout autre contournement** : `Win + I` → Windows Update → rechercher et
> installer **toutes** les mises à jour (y compris facultatives), puis redémarrer.
> Ça règle le problème dans la majorité des cas.
>
> Si Windows Update est bloqué et ne peut pas se faire (machine obsolète) : ne
> perds pas de temps à bricoler des contournements SSL fragiles. Utilise le
> **Codespace** (section ci-dessous) pour tout développement impliquant du réseau
> Python (`datasets`, `huggingface_hub`, `pip install`), en attendant une machine
> avec un Windows à jour.

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

> ⚠️ **Pas de conda dans le Codespace.** Le `.devcontainer` installe les
> dépendances directement dans le Python système du container (pas d'environnement
> `noofar` à activer). Utilise simplement `python`/`pip` sans `conda activate`.
> Le kernel Jupyter à sélectionner dans VS Code est **"Python 3.10"**, pas "noofar".

> ⚠️ **Toujours `git pull` en ouvrant un Codespace existant.** Un Codespace clone
> le dépôt au moment de sa création et ne se resynchronise **pas automatiquement**
> avec les commits poussés depuis une autre machine. Premier réflexe à chaque
> reprise d'un Codespace :
> ```bash
> git fetch && git status
> git pull    # si "behind" est annoncé
> ```
> Sans ça, tu risques de travailler sur une version obsolète du dépôt et de créer
> des conflits au moment de committer.
