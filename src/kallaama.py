# src/kallaama.py
"""Parsing, nettoyage et chargement du corpus KALLAAMA (wolof)."""

import re
from collections import Counter
from pathlib import Path

import pandas as pd

# ── Constantes ────────────────────────────────────────────
CODES = r"fra|fre|fr|fa|ra|frs|en|eng|ang|an|ar|poul"
CS = rf":\s*(?:{CODES})\b"


CORRECTIONS = {
    ":fr abi":     ":fra bi",              # wol_4112 — espace décalé
    "c' :est":     "c'est :fra",            # wol_43512, wol_4410 — tag mangé # PROVISOIRE — revoir avec la règle apostrophe (nb2)
    "code :barre": "code-barre",           # wol_41012 — deux-points au lieu du tiret
    ")ndoon":      "doon",                 # wol_4112 — parenthèse orpheline
    "p)ar":        "par",                  # wol_4510 — faute de frappe
    ":fran":       ":fra",                  # wol_41012 — troncature du tag (n en trop)
    ":!fra":        ":fra",                # wol_4510 — faute de frappe ajout !
    ":;fra":        ":fra"                # wol_4510 — faute de frappe ajout ;

}


SPEAKER_CORRECTIONS = {
    "2_EMISSION_FAPAL_2021_2_corrige_locuteur_2": "locuteur_2",
}


# ── Parsing ───────────────────────────────────────────────
def parse_stm (stm_path, encoding = "utf-8") :
    '''Parse le fichier stm et renvoie une liste de segments 
    ainsi que des statistiques sur le fichier'''

    segments = []
    statistiques = {
    "lignes_lues": 0,
    "segments_retenus": 0,
    "rejet_sans_texte": 0,
    "rejet_exclus": 0,
    "rejet_bornes": 0,
}

    with open(stm_path, encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(';;'): 
                continue
            statistiques["lignes_lues"]+=1
            
            parts = line.split(maxsplit=6)

            # --- REJET 1 : ligne sans texte (6 champs) ---
            if len(parts) < 7 :
                statistiques["rejet_sans_texte"]+=1
                continue

            # --- REJET 2 : zone exclue du scoring ---
            if parts [2] == "excluded_region":
                statistiques["rejet_exclus"]+=1
                continue

            # --- REJET 3 : bornes dégénérées ---
            a = float(parts[3])
            b = float(parts[4])
            if b <= a :
                statistiques["rejet_bornes"]+=1
                continue 

            #--- La ligne est un segment de parole ---
            segments.append({
                "file": parts[0],
                "channel": parts[1],
                "speaker": parts[2],
                "start": float(parts[3]),
                "end": float(parts[4]),
                "label": parts[5],
                "text": parts[6],
            })
            statistiques["segments_retenus"]+=1

    return (segments,statistiques)


def parse_label(label):
    # label a toujours la forme <canal,condition,genre>
    parts = label[1:-1].split(',')
    return {
        "condition": parts[1], 
        "genre": parts[2],
    }


# ── Nettoyage ─────────────────────────────────────────────
def clean_stm_annotations(text):
    #0. corrections
    for faux, correct in CORRECTIONS.items():
        text = text.replace(faux, correct)

    #1. collages
    text = re.sub(r":fra(?=\w)", ":fra ", text)

    #2. tags de langue              — liste blanche ; le tag part, le MOT RESTE
    text = re.sub(rf"\s*:\s*(?:{CODES})\b", "", text, flags=re.IGNORECASE)

    #3. disfluences    %...         — le token entier disparaît
    text = re.sub(r"%\S+", "", text)

    #4. crochets       [...]        — événements acoustiques
    text = re.sub(r"\[[^\]]*\]", "", text)

    # 5. faux départs  mot()  → disfluence, le mot part avec les parenthèses
    text = re.sub(r"\w+\s*\(\)", "", text)

    return text


def is_usable(text_brut,text_propre) : 
    if "*" in text_brut :
        return "inintelligible"
    
    elif  re.search(r"\d", text_brut) :
        return "chiffres"

    elif  not text_propre.strip() :
        return 'vide'
     
    return "ok"


def normalize_for_wer(text, lower=True, strip_punct=True,
                       collapse_spaces=True, split_hyphen=False,
                       strip_apostrophe=False):
    if lower:
        text = text.lower()

    if split_hyphen:
        text = text.replace("-", " ")

    if strip_apostrophe:
        text = text.replace("'", " ")

    if strip_punct:
        garder = ""
        if not split_hyphen:
            garder += "-"
        if not strip_apostrophe:
            garder += "'"
        text = re.sub(rf"[^\w\s{re.escape(garder)}]", " ", text)

    if collapse_spaces:
        text = " ".join(text.split())

    return text


def nettoyer_speaker(s):
    if s in SPEAKER_CORRECTIONS:
        return SPEAKER_CORRECTIONS[s]
    if s == "inter_segment_gap":
        return "non_etiquete"   # texte réel mais locuteur non déterminé
    return s

# ── Chargement ────────────────────────────────────────────
def extract_segment(audio, sr, start, end):
    """Retourne l'array audio correspondant au segment [start, end] en secondes."""
    return audio[int(start * sr):int(end * sr)]


def load_corpus(checked_dir):
    segments_tous = []
    stats_tous = Counter()

    for file in checked_dir.rglob("*.stm"):
        segs, stats = parse_stm(file)
        segments_tous.extend(segs)
        stats_tous.update(stats)

    df = pd.DataFrame(segments_tous)

    # colonnes dérivées
    df ["duration"] = df ["end"] - df ["start"]
    labels = df["label"].apply(parse_label).apply(pd.Series)
    df[["condition", "genre"]] = labels
    df["text_clean"] = df["text"].apply(clean_stm_annotations)
    df["raison"] = [is_usable(b, c) for b, c in zip(df["text"], df["text_clean"])]
    df["usable"] = df["raison"] == "ok"
    df["has_codeswitch"] = df["text"].str.contains(CS, case=False, regex=True)
    df["n_tags"] = df["text"].str.count(CS)
    df["speaker_brut"] = df["speaker"]
    df["speaker"] = df["speaker"].apply(nettoyer_speaker)

    
    return df,stats_tous