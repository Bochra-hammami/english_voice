import time
from pathlib import Path
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from validation import mots_valides
import jiwer

# ---------- Réglages (identiques à la version C de micro_live.py) ----------
MODELE = "base.en"
SR = 16000
PAS = 0.5
MAX_TAMPON = 4.0
FICHIERS = sorted(Path("audios").glob("*.mp3")) + [Path("test.mp3"), Path("test2.mp3"), Path("test3.mp3")]
# ---------------------------------------------------------------------------

model = WhisperModel(MODELE, device="cpu", compute_type="int8")

reference = (Path("audios") / "reference.txt").read_text(encoding="utf-8", errors="ignore")
nettoyer = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
                          jiwer.SubstituteWords({"6": "six", "5": "five", "3": "three"}),
                          jiwer.RemoveMultipleSpaces(), jiwer.Strip()])
ref = nettoyer(" ".join(reference.split()))


def streaming(chemin):
    """Simule le direct sur un fichier avec la logique de la version C.
    Renvoie le texte validé et la liste des latences."""
    audio = decode_audio(str(chemin), sampling_rate=SR)
    decalage = 0.0
    precedent, valides, latences = [], [], []
    t0 = time.time()

    while True:
        time.sleep(PAS)
        lu = min(len(audio), int((time.time() - t0) * SR))   # audio "arrivé" jusqu'ici
        fini = lu >= len(audio)
        tampon = audio[int(decalage * SR):lu]

        if len(tampon) < 0.1 * SR and fini:
            break
        if len(tampon) < SR and not fini:
            continue

        prompt = " ".join(valides[-30:]) or None
        segments, _ = model.transcribe(tampon, language="en", beam_size=1,
                                       word_timestamps=True, initial_prompt=prompt,
                                       vad_filter=True, no_repeat_ngram_size=3)
        actuel = [(w.word.strip(), w.end + decalage) for seg in segments for w in seg.words]

        # Silence prolongé : on avance le tampon (on garde la dernière seconde)
        if not actuel:
            if len(tampon) > 3 * SR:
                decalage = lu / SR - 1.0
            precedent = []
            if fini:
                break
            continue

        if fini:
            communs = [m for m, _ in actuel]
        else:
            communs = mots_valides([m for m, _ in precedent], [m for m, _ in actuel])
            if not communs and len(tampon) / SR > MAX_TAMPON:
                communs = [m for m, _ in actuel[:-3]]

        if communs:
            fin_dernier = actuel[len(communs) - 1][1]
            latences.append((time.time() - t0) - fin_dernier)
            valides += communs
            decalage = fin_dernier
            precedent = actuel[len(communs):]
        else:
            precedent = actuel

        if fini:
            break

    return " ".join(valides), latences


for fichier in FICHIERS:
    if not fichier.exists():
        continue
    texte, lat = streaming(fichier)
    moy = sum(lat) / len(lat) if lat else 0
    ligne = f"{fichier.name:28} latence moy {moy:4.1f}s   max {max(lat, default=0):4.1f}s"
    if fichier.parent.name == "audios":           # on a la référence -> WER
        ligne += f"   WER {jiwer.wer(ref, nettoyer(texte)):6.1%}"
    print(ligne)
    print(f"      → {texte}\n")