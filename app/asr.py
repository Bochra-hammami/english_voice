"""Reconnaissance vocale en direct : micro -> Phrase."""
from typing import Callable
from moonshine_voice import MicTranscriber
from app import config
from app.types import Phrase


class EcouteMicro:
    """Écoute le micro et appelle sur_phrase(Phrase) à chaque phrase terminée."""

    def __init__(self, sur_phrase: Callable[[Phrase], None]):
        self._sur_phrase = sur_phrase
        mic = MicTranscriber().language(config.LANGUE).update_interval(config.INTERVALLE_MAJ)
        if config.MICRO is not None:
            mic = mic.device(config.MICRO)
        self._mic = mic.on_line(self._ligne_terminee)

    def _ligne_terminee(self, ligne) -> None:
        texte = ligne.text.strip()
        if not texte:
            return
        debut = getattr(ligne, "start_time", 0.0)
        fin = debut + getattr(ligne, "duration", 0.0)
        self._sur_phrase(Phrase(texte=texte, debut=debut, fin=fin))

    def demarrer(self) -> None:
        self._mic.load()     # télécharge le modèle au premier lancement
        self._mic.start()

    def arreter(self) -> None:
        arret = getattr(self._mic, "stop", None)
        if arret:
            arret()