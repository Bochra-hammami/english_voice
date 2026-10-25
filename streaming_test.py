import time
from faster_whisper import WhisperModel
from faster_whisper.audio import decode_audio
from validation import mots_valides

# ---------- Réglages ----------
FICHIER = "test3.mp3"     # audio ou vidéo à tester
MODELE = "small.en"      # "base.en" = plus rapide mais moins précis
SR = 16000               # 16 000 échantillons = 1 seconde
MIN_DEBUT = 3.0          # secondes d'audio avant la toute première validation
MAX_TAMPON = 10.0        # au-delà, on force la validation pour éviter l'emballement
# ------------------------------

model = WhisperModel(MODELE, device="cpu", compute_type="int8")
audio = decode_audio(FICHIER, sampling_rate=SR)

decalage = 0.0    # où commence le tampon dans le fichier (en secondes)
precedent = []    # mots provisoires du tour d'avant : [(mot, fin_en_s)]
valides = []      # tous les mots validés
t0 = time.time()

while True:
    # 1. Simule le micro : l'audio "arrive" au rythme réel
    lu = min(len(audio), int((time.time() - t0) * SR))
    fini = lu >= len(audio)

    if lu / SR < MIN_DEBUT:
        time.sleep(0.1)
        continue

    # 2. Le tampon = seulement l'audio pas encore validé
    tampon = audio[int(decalage * SR):lu]

    prompt = " ".join(valides[-30:]) or None   # contexte : les derniers mots validés
    t_calc = time.time()
    segments, _ = model.transcribe(tampon, language="en", beam_size=1,
                                   word_timestamps=True, initial_prompt=prompt)
    # Les temps de Whisper sont relatifs au tampon : on ajoute le décalage
    actuel = [(w.word.strip(), w.end + decalage) for seg in segments for w in seg.words]
    t_calc = time.time() - t_calc
    print(f"      … proposition ({t_calc:.1f}s de calcul) : {' '.join(m for m, _ in actuel)}")

    # 3. Validation (à la fin du fichier, on valide tout ce qui reste)
    if fini:
        communs = [m for m, _ in actuel]
    else:
        communs = mots_valides([m for m, _ in precedent], [m for m, _ in actuel])
        # Garde-fou : tampon trop long sans validation -> on valide tout sauf les 3 derniers mots
        if not communs and len(tampon) / SR > MAX_TAMPON:
            communs = [m for m, _ in actuel[:-3]]

    if communs:
        maintenant = time.time() - t0
        fin_dernier = actuel[len(communs) - 1][1]
        print(f"[{maintenant:5.1f}s] ✅ {' '.join(communs):60} latence {maintenant - fin_dernier:.1f}s")
        valides += communs
        decalage = fin_dernier             # 4. on coupe le tampon après le dernier mot validé
        precedent = actuel[len(communs):]  # le reste reste provisoire
    else:
        precedent = actuel

    if fini:
        break