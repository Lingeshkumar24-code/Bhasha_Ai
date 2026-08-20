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
import logging
import os
import re
import time
import traceback
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("bhasha")

app = FastAPI(
    title="BhashaVoice AI API",
    description="Multilingual Deep Learning Voice Assistant — backend pipeline",
    version="1.0.0",
)

# Global exception handler — logs the FULL Python traceback to console for
# every unhandled error so debugging is easy (no more blank 500s).
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exc()
    logger.error("Unhandled exception on %s:\n%s", request.url.path, tb)
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}", "traceback": tb.splitlines()[-5:]},
    )

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "audio"), exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

def get_frontend_dist() -> Optional[str]:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "dist")),
        os.path.abspath(os.path.join(os.getcwd(), "frontend", "dist")),
        os.path.abspath(os.path.join(os.getcwd(), "dist")),
    ]
    for p in candidates:
        if os.path.isdir(p) and os.path.isfile(os.path.join(p, "index.html")):
            return p
    return None

frontend_dist = get_frontend_dist()
if frontend_dist and os.path.isdir(os.path.join(frontend_dist, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="frontend-assets")

groq_service = GroqService()
intent_service = IntentService()
ner_service = NERService()
translation_service = TranslationService()
tts_service = TTSService()
dialogue_manager = DialogueManager()


@app.get("/")
def root():
    dist = get_frontend_dist()
    if dist:
        index_file = os.path.join(dist, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)
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

    if req.output_language != 'en':
        # Detect what language the LLM actually replied in.
        # LLMs often reply in English even when instructed otherwise — always
        # translate if the detected language is not the target output language.
        try:
            from langdetect import detect as _detect
            detected_lang = _detect(response_text)
        except Exception:
            detected_lang = 'en'  # assume English if detection fails

        # Map langdetect codes to our app codes (langdetect uses ISO 639-1 mostly)
        _LANGDETECT_TO_APP = {
            'ta': 'ta', 'te': 'te', 'kn': 'kn', 'ml': 'ml',
            'hi': 'hi', 'bn': 'bn', 'mr': 'mr', 'gu': 'gu', 'pa': 'pa',
        }
        detected_app = _LANGDETECT_TO_APP.get(detected_lang, detected_lang)

        if detected_app == req.output_language:
            # LLM already replied in the target language — no translation needed.
            translated = response_text
            stages["translation"] = f"skipped (LLM already replied in {req.output_language})"
        else:
            try:
                # Translate from detected source language (usually 'en') to target
                src = detected_app if detected_app in ('en', 'ta', 'te', 'kn', 'ml', 'hi', 'bn', 'mr', 'gu', 'pa') else 'en'
                translated = translation_service.translate(response_text, src, req.output_language)
                stages["translation"] = "completed"
            except Exception as e:
                translated = response_text
                stages["translation"] = f"failed: {e}"
    else:
        translated = response_text
        stages["translation"] = "skipped (output language is English)"

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


@app.get("/{full_path:path}")
async def serve_frontend_spa(full_path: str):
    """
    Catch-all route for Single Page Application (SPA) client-side routing.
    Serves static files directly if found, otherwise returns index.html.
    """
    if full_path.startswith("api/") or full_path.startswith("static/") or full_path in ["docs", "openapi.json", "redoc", "health"]:
        raise HTTPException(status_code=404, detail="Endpoint not found")

    dist = get_frontend_dist()
    if dist:
        file_path = os.path.join(dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        index_file = os.path.join(dist, "index.html")
        if os.path.isfile(index_file):
            return FileResponse(index_file)

    raise HTTPException(status_code=404, detail="Page not found")

