import time
import queue
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from validation import mots_valides

# ---------- Réglages ----------
MODELE = "base.en"       # "small.en" = plus précis mais plus lent
SR = 16000               # 16 000 échantillons = 1 seconde
PAS = 0.5                # on relance la reconnaissance toutes les 0,5 s
MAX_TAMPON = 4.0         # en direct : on force la validation après 4 s d'hésitation
# ------------------------------

file_audio = queue.Queue()

def micro_callback(indata, frames, time_info, status):
    # Appelée automatiquement par le thread du micro : on dépose l'audio dans la file
    file_audio.put(indata[:, 0].copy())

model = WhisperModel(MODELE, device="cpu", compute_type="int8")

tampon = np.zeros(0, dtype=np.float32)   # audio pas encore validé
debut_tampon = 0.0                        # position du tampon depuis le début (en s)
total = 0.0                               # secondes d'audio reçues au total
precedent, valides = [], []

with sd.InputStream(samplerate=SR, channels=1, dtype="float32", callback=micro_callback):
    t0 = time.time()
    print("🎤 Parle en anglais... (Ctrl+C pour arrêter)\n")
    try:
        while True:
            time.sleep(PAS)

            # 1. Récupère tout l'audio arrivé depuis le dernier tour
            while not file_audio.empty():
                morceau = file_audio.get()
                tampon = np.concatenate([tampon, morceau])
                total += len(morceau) / SR

            if len(tampon) < SR:          # moins d'1 s d'audio en attente
                continue

            # 2. Reconnaissance
            prompt = " ".join(valides[-30:]) or None
            t_calc = time.time()
            segments, _ = model.transcribe(tampon, language="en", beam_size=1,
                                           word_timestamps=True, initial_prompt=prompt,
                                           vad_filter=True,             # ignore les silences
                                           no_repeat_ngram_size=3)      # anti-boucles
            actuel = [(w.word.strip(), w.end + debut_tampon) for seg in segments for w in seg.words]
            t_calc = time.time() - t_calc
            print(f"      … ({t_calc:.1f}s calcul, tampon {len(tampon)/SR:.1f}s) {' '.join(m for m, _ in actuel)}")

            # Silence prolongé : on vide le tampon (on garde la dernière seconde)
            if not actuel:
                if len(tampon) > 3 * SR:
                    tampon = tampon[-SR:]
                    debut_tampon = total - 1.0
                precedent = []
                continue

            # 3. Validation (+ garde-fou si Whisper hésite trop longtemps)
            communs = mots_valides([m for m, _ in precedent], [m for m, _ in actuel])
            if not communs and len(tampon) / SR > MAX_TAMPON:
                communs = [m for m, _ in actuel[:-3]]

            if communs:
                fin_dernier = actuel[len(communs) - 1][1]
                latence = (time.time() - t0) - fin_dernier
                print(f"✅ {' '.join(communs):60} latence {latence:.1f}s")
                valides += communs
                # 4. Coupe le tampon après le dernier mot validé
                coupe = int((fin_dernier - debut_tampon) * SR)
                tampon = tampon[coupe:]
                debut_tampon = fin_dernier
                precedent = actuel[len(communs):]
            else:
                precedent = actuel

    except KeyboardInterrupt:
        print("\nArrêt.")