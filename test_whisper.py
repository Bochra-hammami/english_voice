import time
from faster_whisper import WhisperModel

model = WhisperModel("small.en", device="cpu", compute_type="int8")

t0 = time.time()
segments, info = model.transcribe("test.mp3", language="en", word_timestamps=True)

for seg in segments:
    for w in seg.words:
        ecrit = time.time() - t0
        print(f"{w.word:15} dit à {w.end:5.1f}s  |  écrit à {ecrit:5.1f}s")

duree = time.time() - t0
print(f"\nDurée audio : {info.duration:.1f}s  |  calcul : {duree:.1f}s  |  RTF = {duree/info.duration:.2f}")