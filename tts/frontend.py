"""
tts/frontend.py — Normalisation du texte avant synthèse.
Ce que le TTS ne sait pas prononcer doit être transformé en amont.
"""

import re

# Termes que le modèle rend mal — à compléter à l'écoute.
# Note : sur Kiriku, tout finit en minuscules (voir .lower() plus bas),
# donc les prononciations sont écrites en minuscules.
LEXIQUE = {
    # "ISRA": "i-s-r-a",
    # "PAM":  "pam",
}


def verbaliser_nombres(texte, lang):
    """Un TTS entraîné sur graphèmes ne lit pas « 63 % » ni « 2021 »."""
    # À caler sur ce que l'écoute révèle : formes wolof et françaises
    # coexistent dans l'usage réel (cf. corpus TTS, catégorie phrases_nombres)
    return texte


def appliquer_lexique(texte):
    for terme, prononciation in LEXIQUE.items():
        texte = re.sub(rf"\b{re.escape(terme)}\b", prononciation, texte)
    return texte


def preparer_pour_tts(texte, lang="fr", modele="kiriku"):
    """Normalise le texte avant synthèse.

    `modele` peut être un nom court ("kiriku") ou un identifiant HF complet
    ("AIHubSN/Kiriku-Wolof-TTS") — le test par appartenance gère les deux,
    pour que la sonde Oolel de J6 n'hérite pas du .lower() de Kiriku.
    """
    texte = verbaliser_nombres(texte, lang)
    texte = appliquer_lexique(texte)

    # Spécifique Kiriku : son vocabulaire ne contient aucune majuscule.
    # Sans .lower(), elles sont supprimées SILENCIEUSEMENT — noms propres mutilés,
    # aucune erreur levée. Règle de production, pas prétraitement de test.
    if "kiriku" in modele.lower():
        texte = texte.lower()

    return texte