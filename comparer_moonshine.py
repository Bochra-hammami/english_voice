import time
from pathlib import Path
import torch
import jiwer
from transformers import MoonshineStreamingForConditionalGeneration, AutoProcessor
from faster_whisper.audio import decode_audio   # on réutilise juste le lecteur audio

MODELES = ["UsefulSensors/moonshine-streaming-medium"]
SR = 16000
DOSSIER = Path("audios")
torch.set_num_threads(8)   # calcul réparti sur 8 threads du processeur

reference = (DOSSIER / "reference.txt").read_text(encoding="utf-8", errors="ignore")
nettoyer = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
                          jiwer.SubstituteWords({"6": "six", "5": "five", "3": "three"}),
                          jiwer.RemoveMultipleSpaces(), jiwer.Strip()])
ref = nettoyer(" ".join(reference.split()))

for nom in MODELES:
    print(f"\n===== {nom} =====")
    processor = AutoProcessor.from_pretrained(nom)
    model = MoonshineStreamingForConditionalGeneration.from_pretrained(nom)
    model.eval()

    for fichier in sorted(DOSSIER.glob("*.mp3")):
        audio = decode_audio(str(fichier), sampling_rate=SR)
        inputs = processor(audio, return_tensors="pt", sampling_rate=SR)
        # Limite la longueur du texte produit (évite les boucles de répétition)
        limite = int(inputs.attention_mask.sum().item() * 10 / SR)   # plus large : ne coupe plus les locuteurs lents
        t0 = time.time()
        with torch.no_grad():
            ids = model.generate(**inputs, max_length=limite)
        texte = processor.decode(ids[0], skip_special_tokens=True)
        duree = time.time() - t0

        wer = jiwer.wer(ref, nettoyer(texte))
        print(f"{fichier.name:28} WER = {wer:6.1%}   RTF = {duree / (len(audio) / SR):.2f}")
        print(f"      → {texte.strip()}")