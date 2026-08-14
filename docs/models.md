# Models

## Pretrained (used as-is)
- **ASR**: Browser Web Speech API in this build. To add real server-side Whisper:
  `pip install faster-whisper`, then implement `backend/app/asr/whisper_service.py`
  and wire it into `/api/voice/transcribe`.
- **Groq LLM**: set `GROQ_API_KEY` / `GROQ_MODEL` env vars. See `app/services/groq_service.py`.
- **Translation**: `deep-translator` (Google Translate) by default. For IndicTrans2, set
  `INDICTRANS2_MODEL_DIR` to a local checkpoint and implement `_translate_indictrans2` in
  `app/services/translation_service.py` (load with `IndicTransToolkit` / AI4Bharat's inference
  script — see https://github.com/AI4Bharat/IndicTrans2).
- **TTS**: `gTTS` by default. For Indic Parler-TTS, set `INDIC_TTS_MODEL_DIR` and implement
  `_synthesize_indic` in `app/services/tts_service.py`.

## Our fine-tuned models
- **Intent Classifier**: `training/train_intent.py` fine-tunes `ai4bharat/indic-bert` (or any
  HF sequence-classification base) on `data/intents.csv`.
- **NER Model**: `training/train_ner.py` fine-tunes a token-classification head on
  `data/ner_*.json`.

Both auto-load from `models/intent_classifier` and `models/ner_model` if present; otherwise
the backend uses clearly-labelled rule-based fallbacks (never silently pretends to be the
trained model — see `status()` methods on each service).
