"""
nlu/client.py — Client HTTP vers le service Rasa.
"""

import requests
import yaml
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_intent(texte):
    """Interroge le service Rasa pour extraire intent et entités."""
    config = load_config()
    rasa_url = config["services"]["rasa_url"]

    response = requests.post(
        f"{rasa_url}/model/parse",
        json={"text": texte},
        timeout=10
    )
    response.raise_for_status()
    data = response.json()

    return {
        "intent": data.get("intent", {}).get("name"),
        "confidence": data.get("intent", {}).get("confidence"),
        "entities": data.get("entities", []),
    }