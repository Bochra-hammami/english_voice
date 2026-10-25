import time
from pathlib import Path
import jiwer
from faster_whisper.audio import decode_audio   # juste pour lire les mp3
from moonshine_voice import Transcriber, TranscriptEventListener, get_model_for_language

SR = 16000
CHUNK = 0.1                                  # on envoie 0,1 s d'audio à la fois, comme un micro
FICHIERS = sorted(Path("audios").glob("*.mp3"))

model_path, model_arch = get_model_for_language("en")
print("Modèle utilisé :", model_arch)
transcriber = Transcriber(model_path=model_path, model_arch=model_arch)

reference = (Path("audios") / "reference.txt").read_text(encoding="utf-8", errors="ignore")
nettoyer = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
                          jiwer.SubstituteWords({"6": "six", "5": "five", "3": "three"}),
                          jiwer.RemoveMultipleSpaces(), jiwer.Strip()])
ref = nettoyer(" ".join(reference.split()))


class Ecouteur(TranscriptEventListener):
    """Reçoit les lignes terminées et mesure quand elles arrivent."""
    def __init__(self, t0):
        self.t0 = t0
        self.lignes = []
        self.latences = []

    def on_line_completed(self, event):
        maintenant = time.time() - self.t0
        ligne = event.line
        self.lignes.append(ligne.text)
        duree = getattr(ligne, "duration", None)   # fin de la ligne dans l'audio, si disponible
        if duree is not None:
            self.latences.append(maintenant - (ligne.start_time + duree))
        print(f"   [{maintenant:5.1f}s] ✅ {ligne.text}")


for fichier in FICHIERS:
    print(f"\n===== {fichier.name} =====")
    audio = decode_audio(str(fichier), sampling_rate=SR)

    stream = transcriber.create_stream(update_interval=0.5)
    ecouteur = Ecouteur(time.time())
    stream.add_listener(ecouteur)
    stream.start()

    pas = int(CHUNK * SR)
    t_calc = time.time()
    for i in range(0, len(audio), pas):
        stream.add_audio(audio[i:i + pas].tolist(), SR)   # sans attente : on mesure la vitesse pure
    t_calc = time.time() - t_calc
    print(f"   ⏱ audio {len(audio)/SR:.1f}s  |  calcul {t_calc:.1f}s  |  RTF {t_calc/(len(audio)/SR):.2f}")            # rythme réel

    stream.stop()                            # termine la dernière ligne
    stream.close()

    texte = " ".join(ecouteur.lignes)
    wer = jiwer.wer(ref, nettoyer(texte))
    resume = f"WER = {wer:6.1%}"
    if ecouteur.latences:
        resume += f"   latence moy {sum(ecouteur.latences)/len(ecouteur.latences):.1f}s   max {max(ecouteur.latences):.1f}s"
    print(f"   → {resume}")