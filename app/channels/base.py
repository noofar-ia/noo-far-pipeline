# app/channels/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IncomingMessage:
    """Format commun, indépendant du canal d'origine."""
    from_id: str
    text: str | None
    audio_path: str | None  # chemin local du fichier audio déjà téléchargé, ou None


class MessagingChannel(ABC):
    @abstractmethod
    async def parse_webhook(self, request) -> IncomingMessage:
        """Convertit la requête brute du canal en IncomingMessage."""
        ...

    @abstractmethod
    async def send_message(self, to: str, text: str = None, audio_path: str = None):
        """Envoie une réponse (texte et/ou audio) via ce canal."""
        ...