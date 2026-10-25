"""Contrats de données échangés entre les modules."""
from dataclasses import dataclass

SR = 16000   # tous les modules travaillent à 16 kHz, mono


@dataclass
class Phrase:      # ASR -> TTS
    texte: str
    debut: float   # début dans l'audio (s)
    fin: float     # fin dans l'audio (s)