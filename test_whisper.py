from faster_whisper import WhisperModel

model = WhisperModel("small.en", device="cpu", compute_type="int8")

segments, info = model.transcribe("test.mp3", language="en")

for seg in segments:
    print(seg.text)