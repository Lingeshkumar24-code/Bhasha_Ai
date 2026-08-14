"""
BhashaVoice AI — Backend entrypoint.

Wires together the deep-learning-style voice pipeline:
  audio (client-side) -> transcript -> NLP -> intent -> entities
  -> dialogue manager -> Groq LLM -> translation -> TTS

IMPORTANT (per project spec, section 42 — "Do not fake AI"):
Every service module below is honest about whether it is running a
real trained/pretrained model or a clearly-labelled fallback. Nothing
returns fabricated confidence scores or invented metrics.
"""
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.api.schemas import (
    ChatRequest, ChatResponse,
    NLPRequest, NLPResponse,
    IntentRequest, IntentResponse,
    EntityRequest, EntityResponse,
    TranslateRequest, TranslateResponse,
    TTSRequest, TTSResponse,
    FullPipelineRequest, FullPipelineResponse, PipelineStageStatus,
)
from app.services.groq_service import GroqService
from app.services.intent_service import IntentService
from app.services.ner_service import NERService
from app.services.translation_service import TranslationService
from app.services.tts_service import TTSService
from app.dialogue.manager import DialogueManager

load_dotenv()

app = FastAPI(
    title="BhashaVoice AI API",
    description="Multilingual Deep Learning Voice Assistant — backend pipeline",
    version="1.0.0",
)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "audio"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

groq_service = GroqService()
intent_service = IntentService()
ner_service = NERService()
translation_service = TranslationService()
tts_service = TTSService()
dialogue_manager = DialogueManager()


@app.get("/")
def root():
    return {
        "message": "BhashaVoice AI Backend API is running.",
        "docs": "/docs",
        "health": "/health",
        "status": "online"
    }


@app.get("/health")
def health():
    """Real component health checks — never fake 'Connected'."""
    return {
        "status": "ok",
        "components": {
            "groq": groq_service.status(),
            "intent_model": intent_service.status(),
            "ner_model": ner_service.status(),
            "translation": translation_service.status(),
            "tts": tts_service.status(),
        },
        "timestamp": time.time(),
    }


@app.get("/api/models")
def get_models():
    """Model registry — clearly separates pretrained vs our fine-tuned models."""
    return {
        "pretrained_foundation_models": [
            {"name": "Whisper (browser Web Speech API in this build)", "task": "ASR", "source": "OpenAI / browser vendor"},
            {"name": "Groq Llama (model set via GROQ_MODEL env var)", "task": "LLM response generation", "source": "Groq"},
            {"name": "Google Translate (fallback) / IndicTrans2 (pluggable)", "task": "Translation", "source": "AI4Bharat / Google"},
            {"name": "gTTS (fallback) / Indic Parler-TTS (pluggable)", "task": "TTS", "source": "Google / AI4Bharat"},
        ],
        "our_trained_models": [
            {"name": "Intent Classifier", "task": "Intent classification", "status": intent_service.status()},
            {"name": "NER Model", "task": "Entity extraction", "status": ner_service.status()},
        ],
    }


@app.get("/api/metrics")
def get_metrics():
    """Real evaluation metrics if present, otherwise honestly 'Not evaluated yet'."""
    import json
    metrics_path = os.path.join(os.path.dirname(__file__), "..", "models", "metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            return json.load(f)
    return {
        "intent": "Not evaluated yet",
        "ner": "Not evaluated yet",
        "asr_wer": "Not evaluated yet",
        "translation_bleu": "Not evaluated yet",
        "avg_latency_ms": "Not evaluated yet",
        "note": "Run training/train_intent.py and training/evaluate.py to populate real metrics.",
    }


@app.post("/api/nlp/analyze", response_model=NLPResponse)
def nlp_analyze(req: NLPRequest):
    intent = intent_service.predict(req.text, req.language)
    entities = ner_service.extract(req.text, req.language)
    return NLPResponse(
        language=req.language,
        intent=intent,
        entities=entities,
        sentiment="neutral",  # sentiment head not trained in this build — placeholder, not fabricated confidence
    )


@app.post("/api/intent/predict", response_model=IntentResponse)
def intent_predict(req: IntentRequest):
    return intent_service.predict(req.text, req.language)


@app.post("/api/entities/extract", response_model=EntityResponse)
def entities_extract(req: EntityRequest):
    return EntityResponse(entities=ner_service.extract(req.text, req.language))


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        reply = groq_service.chat(req.session_id, req.message, req.output_language, dialogue_manager)
        return ChatResponse(response=reply, model=groq_service.model_name)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq temporarily unavailable: {e}")


@app.post("/api/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    text = translation_service.translate(req.text, req.source_language, req.target_language)
    return TranslateResponse(translated_text=text, engine=translation_service.engine_name)


@app.post("/api/tts", response_model=TTSResponse)
def tts(req: TTSRequest):
    audio_url = tts_service.synthesize(req.text, req.language)
    return TTSResponse(audio_url=audio_url, engine=tts_service.engine_name)


@app.post("/api/voice/transcribe")
def transcribe_stub():
    """
    Real speech capture + ASR happens client-side via the browser's
    Web Speech API in this build (see frontend/src/hooks/useSpeechRecognition.js).
    This endpoint exists for API-completeness / future server-side Whisper.
    """
    raise HTTPException(
        status_code=501,
        detail="Server-side ASR not wired in this build. ASR runs in-browser (Web Speech API). "
               "To add real server Whisper, install `openai-whisper`/`faster-whisper` and implement "
               "app/asr/whisper_service.py, then call it here.",
    )


@app.post("/api/voice/full-pipeline", response_model=FullPipelineResponse)
def full_pipeline(req: FullPipelineRequest):
    """
    Runs transcript -> NLP -> intent -> entities -> dialogue -> Groq -> translation -> TTS.
    Transcript itself is produced client-side (browser ASR); this endpoint takes it as input.
    """
    stages = {}

    stages["preprocessing"] = "completed"  # done client-side (VAD / normalization in useAudioVisualizer.js)

    transcript = req.transcript
    stages["asr"] = "completed"

    intent = intent_service.predict(transcript, req.input_language)
    stages["intent"] = "completed"

    entities = ner_service.extract(transcript, req.input_language)
    stages["ner"] = "completed"
    stages["nlp"] = "completed"

    dialogue_manager.update(req.session_id, intent, entities, req.input_language)
    stages["dialogue"] = "completed"

    try:
        response_text = groq_service.chat(req.session_id, transcript, req.output_language, dialogue_manager)
        stages["llm"] = "completed"
    except Exception as e:
        stages["llm"] = f"failed: {e}"
        response_text = "Sorry, the AI service is temporarily unavailable. Your transcript was still understood."

    if req.input_language != req.output_language:
        translated = translation_service.translate(response_text, "en", req.output_language)
        stages["translation"] = "completed"
    else:
        translated = response_text
        stages["translation"] = "skipped (same language)"

    try:
        audio_url = tts_service.synthesize(translated, req.output_language)
        stages["tts"] = "completed"
    except Exception as e:
        audio_url = None
        stages["tts"] = f"failed: {e}"

    return FullPipelineResponse(
        language=req.input_language,
        transcript=transcript,
        intent=intent,
        entities=entities,
        response=response_text,
        translated_response=translated,
        audio_url=audio_url,
        pipeline=PipelineStageStatus(**stages),
    )
