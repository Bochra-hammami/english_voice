"""Interface Meet : ta voix -> texte -> voix neutre."""
import time
from app.asr import EcouteMicro
from app.tts import Voix

MARGE_ECHO = 1.0   # secondes ignorées après que la voix neutre a fini de parler


def main():
    voix = Voix()
    derniere_parole = 0.0   # dernier moment où la voix neutre parlait

    def sur_phrase(phrase):
        # Anti-écho : on ignore ce que le micro entend pendant/juste après la voix neutre
        if voix.parle() or time.time() - derniere_parole < MARGE_ECHO:
            return
        print(f"🗣  {phrase.texte}")
        voix.dire(phrase)

    micro = EcouteMicro(sur_phrase)
    micro.demarrer()
    print("🎤 Parle en anglais... (Ctrl+C pour arrêter)\n")
    try:
        while True:
            if voix.parle():
                derniere_parole = time.time()
            time.sleep(0.1)
    except KeyboardInterrupt:
        micro.arreter()
        print("\nArrêt.")


if __name__ == "__main__":
    main()