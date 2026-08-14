# BhashaVoice AI — Multilingual Deep Learning Voice Assistant

**"From Voice to Intelligence — Built for India."**

An MCA Deep Learning project: a real, working voice-assistant pipeline —
speech → preprocessing → ASR → NLP → intent classification → entity
recognition → dialogue management → Groq LLM → translation → text-to-speech —
for English, Tamil, Telugu, Kannada, Malayalam, Hindi and more, with support
for code-mixed Indian speech ("Fan on karo", "Light off pannunga").

## Honesty notice (read this first)

Per the project's own core requirement — **never fake AI** — here's exactly
what's real out of the box vs. what needs an extra step from you:

| Component | Out-of-the-box | To get the "real" trained version |
|---|---|---|
| ASR | ✅ Real (browser Web Speech API) | Add server Whisper — see `docs/models.md` |
| Groq LLM | ✅ Real (once you add `GROQ_API_KEY`) | — |
| Intent classifier | ⚠️ Honest keyword-rule fallback, clearly labelled | Run `training/train_intent.py` |
| NER | ⚠️ Honest regex/gazetteer fallback, clearly labelled | Run `training/train_ner.py` |
| Translation | ✅ Real (Google Translate via `deep-translator`) | Swap in IndicTrans2 — see `docs/models.md` |
| TTS | ✅ Real (gTTS), browser SpeechSynthesis as final fallback | Swap in Indic Parler-TTS |
| Evaluation metrics | Shows **"Not evaluated yet"** until you actually train | Run `training/evaluate.py` |

The frontend always displays which of these is active (Model Lab page,
System Status panel) — it never claims a trained model is running when it
isn't.

## Quick start

```bash
# 1. Backend
cd backend
cp .env.example .env        # paste your real GROQ_API_KEY in here
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

Open http://localhost:5173, allow microphone access, pick input/output
languages, and press the mic button — or use Demo Mode on the Voice
Assistant page to run real sample commands without a microphone.

## Deploy to Render

See `docs/deployment.md`. TL;DR: push to GitHub, then Render Dashboard →
New → Blueprint → select this repo (`render.yaml` configures both services).
Add your `GROQ_API_KEY` in the Render dashboard — never commit it.

## Train the real intent/NER models

```bash
pip install -r training/requirements.txt
python training/train_intent.py
python training/train_ner.py
python training/evaluate.py
```

This needs internet access to the HuggingFace Hub and ideally a GPU —
it was **not** run as part of generating this codebase (this sandbox has
neither), so there are no invented accuracy numbers anywhere in this repo.
Run it yourself, then restart the backend — it auto-detects the new
checkpoints in `models/`.

## Project structure

See `docs/architecture.md` for the full pipeline diagram and
`docs/models.md` for how each model is wired, plus instructions for
swapping in IndicTrans2 / Indic Parler-TTS / server-side Whisper.

## What's real vs. still a stub

- **Real & working**: full React frontend (12 pages, 3D orb, live pipeline
  viz), FastAPI backend with all endpoints from the spec, browser-based
  ASR/TTS, Groq integration, Google-Translate-backed translation, gTTS
  audio, dialogue state with slot filling, honest fallback labelling,
  training/evaluation scripts, Render deployment config.
- **Stubbed with clear TODOs** (by necessity — these need GPUs / large
  model downloads / a live network this build environment didn't have):
  server-side Whisper, IndicTrans2, Indic Parler-TTS, and the actual
  execution of the training scripts. Each stub raises a clear error or
  `NotImplementedError` rather than pretending to work.
