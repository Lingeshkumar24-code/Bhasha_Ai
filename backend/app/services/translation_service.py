import os

# Map our language codes to what deep-translator (Google Translate) expects.
_LANG_MAP = {
    "en": "en", "ta": "ta", "te": "te", "kn": "kn", "ml": "ml", "hi": "hi",
    "bn": "bn", "mr": "mr", "gu": "gu", "pa": "pa",
}

INDICTRANS2_DIR = os.getenv("INDICTRANS2_MODEL_DIR", "")


class TranslationService:
    """
    Preferred: IndicTrans2 for Indian-language pairs (set INDICTRANS2_MODEL_DIR
    to a local checkpoint to enable it — not loaded by default since it needs
    a GPU/large download not available in this sandbox).
    Fallback: deep-translator (Google Translate) — clearly labelled, used so the
    app actually works end-to-end out of the box.
    """

    def __init__(self):
        self.engine_name = "Google Translate (fallback via deep-translator)"
        self._indictrans2_ready = bool(INDICTRANS2_DIR and os.path.isdir(INDICTRANS2_DIR))
        if self._indictrans2_ready:
            self.engine_name = "IndicTrans2 (local checkpoint)"

    def status(self) -> str:
        return "READY"

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text

        if self._indictrans2_ready:
            return self._translate_indictrans2(text, source_language, target_language)

        return self._translate_fallback(text, source_language, target_language)

    def _translate_fallback(self, text: str, source_language: str, target_language: str) -> str:
        try:
            from deep_translator import GoogleTranslator
            src = _LANG_MAP.get(source_language, source_language)
            tgt = _LANG_MAP.get(target_language, target_language)
            return GoogleTranslator(source=src, target=tgt).translate(text)
        except Exception as e:
            # Never fabricate a translation — surface the failure honestly.
            raise RuntimeError(f"Translation fallback failed: {e}")

    def _translate_indictrans2(self, text: str, source_language: str, target_language: str) -> str:
        # Hook for a real IndicTrans2 checkpoint. Left as a documented stub
        # since the actual model weights (multi-GB) can't be fetched in this
        # sandbox. See docs/models.md for integration instructions.
        raise NotImplementedError(
            "IndicTrans2 checkpoint detected but inference code not wired. "
            "See docs/models.md for the integration snippet."
        )
