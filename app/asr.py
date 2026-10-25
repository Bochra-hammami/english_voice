"""Reconnaissance vocale : micro -> Phrase (direct) et fichier simulé en direct -> Phrase."""
import time
from typing import Callable
from moonshine_voice import (MicTranscriber, Transcriber, TranscriptEventListener,
                             get_model_for_language)
from faster_whisper.audio import decode_audio   # sert seulement à lire mp3/wav/mp4
from app import config
from app.types import Phrase, SR


def _vers_phrase(ligne):
    """Convertit une ligne Moonshine en Phrase (ou None si vide)."""
    texte = ligne.text.strip()
    if not texte:
        return None
    debut = getattr(ligne, "start_time", 0.0)
    return Phrase(texte=texte, debut=debut, fin=debut + getattr(ligne, "duration", 0.0))


# ---------- Mode direct : le micro ----------
class EcouteMicro:
    """Écoute le micro et appelle sur_phrase(Phrase) à chaque phrase terminée."""

    def __init__(self, sur_phrase: Callable[[Phrase], None]):
        self._sur_phrase = sur_phrase
        mic = MicTranscriber().language(config.LANGUE).update_interval(config.INTERVALLE_MAJ)
        if config.MICRO is not None:
            mic = mic.device(config.MICRO)
        self._mic = mic.on_line(self._ligne_terminee)

    def _ligne_terminee(self, ligne) -> None:
        phrase = _vers_phrase(ligne)
        if phrase:
            self._sur_phrase(phrase)

    def demarrer(self) -> None:
        self._mic.load()
        self._mic.start()

    def arreter(self) -> None:
        arret = getattr(self._mic, "stop", None)
        if arret:
            arret()


# ---------- Mode fichier, simulé comme si quelqu'un parlait ----------
class _Collecteur(TranscriptEventListener):
    def __init__(self):
        self.phrases = []

    def on_line_completed(self, event):
        phrase = _vers_phrase(event.line)
        if phrase:
            self.phrases.append(phrase)


_transcriber = None


def _charger_transcriber():
    """Charge le modèle une seule fois (le premier appel est plus lent)."""
    global _transcriber
    if _transcriber is None:
        chemin, arch = get_model_for_language(config.LANGUE)
        _transcriber = Transcriber(model_path=chemin, model_arch=arch)
    return _transcriber


def simuler_direct(chemin: str):
    """Envoie le fichier au rythme réel, comme une personne qui parle.
    Génère (phrase, instant_d_apparition, duree_audio) à chaque phrase terminée."""
    audio = decode_audio(str(chemin), sampling_rate=SR)
    duree_audio = len(audio) / SR
    stream = _charger_transcriber().create_stream(update_interval=config.INTERVALLE_MAJ)
    collecteur = _Collecteur()
    stream.add_listener(collecteur)
    stream.start()

    t0, vues, pas = time.time(), 0, int(0.1 * SR)
    for i in range(0, len(audio), pas):
        avance = i / SR - (time.time() - t0)
        if avance > 0:
            time.sleep(avance)            # jamais plus vite qu'une vraie personne
        stream.add_audio(audio[i:i + pas].tolist(), SR)
        while vues < len(collecteur.phrases):
            yield collecteur.phrases[vues], time.time() - t0, duree_audio
            vues += 1

    stream.stop()                         # termine la dernière phrase
    stream.close()
    while vues < len(collecteur.phrases):
        yield collecteur.phrases[vues], time.time() - t0, duree_audio
        vues += 1