from typing import List, Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
    text: str
    label: str
    start: int = 0
    end: int = 0


class IntentResponse(BaseModel):
    label: str
    confidence: float
    model: str  # names the actual model/method used — never faked


class NLPRequest(BaseModel):
    text: str
    language: str = "en"


class NLPResponse(BaseModel):
    language: str
    intent: IntentResponse
    entities: List[Entity]
    sentiment: str


class IntentRequest(BaseModel):
    text: str
    language: str = "en"


class EntityRequest(BaseModel):
    text: str
    language: str = "en"


class EntityResponse(BaseModel):
    entities: List[Entity]


class ChatRequest(BaseModel):
    session_id: str
    message: str
    output_language: str = "en"


class ChatResponse(BaseModel):
    response: str
    model: str


class TranslateRequest(BaseModel):
    text: str
    source_language: str = "en"
    target_language: str = "en"


class TranslateResponse(BaseModel):
    translated_text: str
    engine: str


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class TTSResponse(BaseModel):
    audio_url: Optional[str]
    engine: str


class PipelineStageStatus(BaseModel):
    preprocessing: str = "pending"
    asr: str = "pending"
    nlp: str = "pending"
    intent: str = "pending"
    ner: str = "pending"
    dialogue: str = "pending"
    llm: str = "pending"
    translation: str = "pending"
    tts: str = "pending"


class FullPipelineRequest(BaseModel):
    session_id: str
    transcript: str
    input_language: str = "en"
    output_language: str = "en"


class FullPipelineResponse(BaseModel):
    language: str
    transcript: str
    intent: IntentResponse
    entities: List[Entity]
    response: str
    translated_response: str
    audio_url: Optional[str]
    pipeline: PipelineStageStatus
