"""Voix neutre : Phrase -> son."""
from moonshine_voice import TextToSpeech
from app import config
from app.types import Phrase


class Voix:
    def __init__(self):
        tts = TextToSpeech().language("en_us").voice(config.VOIX)
        if config.SORTIE_AUDIO is not None:
            tts = tts.output_device(config.SORTIE_AUDIO)
        self._tts = tts
        self._tts.load()     # télécharge la voix au premier lancement

    def dire(self, phrase: Phrase) -> None:
        self._tts.say(phrase.texte)   # ne bloque pas : la phrase est mise en file d'attente

    def parle(self) -> bool:
        """True tant que la voix neutre est en train de parler."""
        return self._tts.is_talking()