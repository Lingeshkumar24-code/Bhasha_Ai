# Architecture

USER VOICE → MICROPHONE → AUDIO CAPTURE (browser) → AUDIO PREPROCESSING (client-side VAD/volume
check) → BROWSER ASR (Web Speech API) → TEXT → BACKEND: NLP → INTENT (IndicBERT fine-tuned or
keyword fallback) → ENTITIES (NER fine-tuned or regex fallback) → DIALOGUE MANAGER (bounded
context) → GROQ LLM → TRANSLATION (IndicTrans2 pluggable / Google Translate fallback) → TTS
(Indic TTS pluggable / gTTS fallback / browser SpeechSynthesis final fallback) → VOICE RESPONSE.

See frontend/src/pages/Architecture.jsx for the same content rendered in the UI, and
backend/main.py `full_pipeline` for the exact orchestration code.
