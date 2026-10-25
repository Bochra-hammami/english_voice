import time
from pathlib import Path
from faster_whisper import WhisperModel
import jiwer

MODELES = ["base.en", "small.en"]
DOSSIER = Path("audios")

reference = (DOSSIER / "reference.txt").read_text(encoding="utf-8", errors="ignore")

# Nettoyage identique pour la référence et la transcription :
# minuscules, sans ponctuation, chiffres -> mots, espaces propres
nettoyer = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
                          jiwer.SubstituteWords({"6": "six", "5": "five", "3": "three"}),
                          jiwer.RemoveMultipleSpaces(), jiwer.Strip()])
ref = nettoyer(" ".join(reference.split()))   # tout sur une ligne, nettoyé

for nom_modele in MODELES:
    print(f"\n===== {nom_modele} =====")
    model = WhisperModel(nom_modele, device="cpu", compute_type="int8")

    for fichier in sorted(DOSSIER.glob("*.mp3")):
        t0 = time.time()
        segments, info = model.transcribe(str(fichier), language="en", beam_size=1)
        texte = " ".join(seg.text for seg in segments)
        duree = time.time() - t0

        wer = jiwer.wer(ref, nettoyer(texte))
        print(f"{fichier.name:28} WER = {wer:6.1%}   RTF = {duree / info.duration:.2f}")
        print(f"      → {texte.strip()}")