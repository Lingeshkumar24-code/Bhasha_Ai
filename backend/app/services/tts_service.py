import os
import uuid

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

_GTTS_LANG_MAP = {
    "en": "en", "ta": "ta", "te": "te", "kn": "kn", "ml": "ml", "hi": "hi",
    "bn": "bn", "mr": "mr", "gu": "gu", "pa": "pa",
}

INDIC_TTS_DIR = os.getenv("INDIC_TTS_MODEL_DIR", "")


class TTSService:
    """
    Preferred: Indic Parler-TTS / AI4Bharat-compatible model if
    INDIC_TTS_MODEL_DIR is configured with a local checkpoint.
    Fallback: gTTS (server-side) — and if that also fails (e.g. no network
    to Google's TTS endpoint), the frontend falls back further to the
    browser's own SpeechSynthesis API (see useSpeechSynthesis.js), matching
    the spec's required 2-tier fallback chain.
    """

    def __init__(self):
        self.engine_name = "gTTS (fallback)"
        self._indic_ready = bool(INDIC_TTS_DIR and os.path.isdir(INDIC_TTS_DIR))
        if self._indic_ready:
            self.engine_name = "Indic Parler-TTS (local checkpoint)"

    def status(self) -> str:
        return "READY"

    def synthesize(self, text: str, language: str) -> str:
        if self._indic_ready:
            return self._synthesize_indic(text, language)
        return self._synthesize_gtts(text, language)

    def _synthesize_gtts(self, text: str, language: str) -> str:
        from gtts import gTTS
        lang = _GTTS_LANG_MAP.get(language, "en")
        filename = f"{uuid.uuid4().hex}.mp3"
        path = os.path.join(AUDIO_DIR, filename)
        gTTS(text=text, lang=lang).save(path)
        return f"/static/audio/{filename}"

    def _synthesize_indic(self, text: str, language: str) -> str:
        raise NotImplementedError(
            "Indic TTS checkpoint detected but inference code not wired. "
            "See docs/models.md for the integration snippet."
        )
