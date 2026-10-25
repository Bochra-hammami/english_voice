## English Voice
Imagine two people speaking English, yet constantly asking *"sorry, can you repeat?"*: strong
accents can make simple calls hard. **English Voice** listens to you, understands your
words, and repeats them in a **clear, neutral voice** in your Google Meet call.

- **Code:** https://github.com/Bochra-hammami/english_voice
- **Prototype demo (videos):** https://drive.google.com/drive/folders/1h79l8VcuUkRoUQr6QqgY-fg8VGALOBh0?usp=sharing

## How it works

```
Your voice → mic → speech recognition (Moonshine) → text → neutral voice (TTS)
          → virtual microphone (VB-CABLE) → Google Meet → the other person
```

- Runs **locally on CPU**: no GPU, no cloud, the audio never leaves the PC.
- Each person who wants their voice converted runs the app on their own computer.
  The listener installs nothing.
- Works with any call app where you choose a microphone (Meet, Zoom, Teams).

## Project structure

```
app/            core, shared by both interfaces
  config.py     all settings (language, voice, mic, audio output)
  types.py      data contracts (Phrase)
  asr.py        speech recognition: mic -> Phrase, file -> Phrase
  tts.py        neutral voice: Phrase -> sound
  metriques.py  WER (word error rate)
interfaces/
  meet.py       live mode: your voice -> neutral voice -> Meet
  fichier.py    web page: drop an audio file, see the text appear live + metrics
outils/         measurement scripts used to choose the model
```

## Installation (Windows)

1. Python 3.11+ and Git installed.
2. Clone and install:
   ```powershell
   git clone https://github.com/Bochra-hammami/english_voice.git
   cd english_voice
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
   The `venv` is a private environment for this project's packages, so they don't mix
   with other Python projects. Activate it every time you open a new terminal: you'll see
   `(venv)` at the start of the line. If PowerShell blocks the activation, run
   `Set-ExecutionPolicy -Scope Process Bypass` first.

   Models download automatically on first launch (internet needed once).

## Interface 1: file test (web page)

```powershell
python -m interfaces.fichier
```
Open the address shown (http://127.0.0.1:7860), drop an mp3/wav, optionally paste the
reference text, and click **Lancer**. The audio plays and the text appears phrase by
phrase, with latency per phrase and the WER at the end.

## Interface 2: Google Meet

1. Install **VB-CABLE** from the official site (vb-audio.com/Cable), run the setup as
   administrator, reboot.
2. In Windows sound settings, check that **output = your speakers** and
   **input = your real microphone**.
3. Find the cable number:
   ```powershell
   python -c "import sounddevice as sd; print(sd.query_devices())"
   ```
   Note the number of the line `CABLE Input (...), MME`.
4. In `app/config.py`, set `SORTIE_AUDIO = <that number>`. The value in the repository
   (`5`) is the author's PC: change it to yours. Use `None` to hear the voice on your
   own speakers instead.
5. Run the app:
   ```powershell
   python -m interfaces.meet
   ```
6. In Meet: **Settings → Audio → Microphone → CABLE Output (VB-Audio Virtual Cable)**.

**Use headphones**, or keep the other device away from your PC: otherwise your mic picks
up the other person (or the neutral voice) and repeats it.

## Results (CPU, Speech Accent Archive, live streaming)

| Accent | Whisper base.en (streaming) | **Moonshine (streaming)** |
|---|---|---|
| Indian (strong, gujarati1) | 44.9 % WER | **8.7 %** |
| Indian (strong, gujarati4) | 34.8 % | **17.4 %** |
| Indian (hindi4) | 2.9 % | **1.4 – 5.8 %** |
| UK (english11) | 0.0 % | **0.0 %** |

Moonshine was chosen: 2–4× fewer errors on strong accents in live mode, runs on CPU,
MIT licence, and the same library provides the neutral voice.

## Known limits

- Very strong / regional accents still reach 10–30 % word errors.
- Latency (≈ 2–8 s) depends on the CPU; on a busy or weak PC, it grows.
- Without headphones, an echo loop can occur.
- Muting in Meet right after speaking cuts the neutral voice (it arrives 1–2 s later).

## Next steps

- Fine-tuning (LoRA) on Indian and regional UK accents, with commercially licensed data.
- Choose a lighter model size for low-end PCs.
- Installer that sets up the virtual microphone automatically.
- Push-to-talk mode and an in-app mute button.
- **Browser extension for Google Meet:** turn English Voice into a Chrome extension that
  plugs directly into the Meet page, with no virtual cable and no Python install. Users
  would simply add the extension and turn it on during a call. This requires running the
  speech models inside the browser (or linking the extension to a small local app), which
  is the main technical challenge.
