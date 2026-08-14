import os
import re
from app.api.schemas import IntentResponse

INTENT_LABELS = [
    "GREETING", "WEATHER", "PLAY_MUSIC", "SET_ALARM", "REMINDER",
    "TRANSLATION", "GENERAL_QUERY", "NAVIGATION", "SMART_HOME",
    "EDUCATION", "HEALTHCARE", "NEWS", "CALCULATOR", "TIME", "DATE",
    "FAREWELL", "BOOK_CAB",
]

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "intent_classifier")

# Keyword rules used ONLY as a clearly-labelled development fallback when no
# fine-tuned model checkpoint is present. This is intentionally simple and
# is NEVER reported to the frontend as "IndicBERT Intent Classifier".
_RULES = {
    "GREETING": [r"\bhi\b", r"\bhello\b", r"\bvanakkam\b", r"\bnamaste\b", r"\bnamaskara\b"],
    "FAREWELL": [r"\bbye\b", r"\bsee you\b", r"\bpogiren\b"],
    "WEATHER": [r"weather", r"vaanilai", r"havaman", r"climate"],
    "PLAY_MUSIC": [r"play music", r"song", r"paatu", r"isai"],
    "SET_ALARM": [r"alarm", r"mani.?ku"],
    "REMINDER": [r"remind", r"reminder"],
    "TRANSLATION": [r"translate", r"meaning of"],
    "NAVIGATION": [r"directions?", r"navigate", r"route to"],
    "SMART_HOME": [r"\bfan\b", r"\blight\b", r"\bpannunga\b", r"\bkaro\b", r"switch (on|off)"],
    "BOOK_CAB": [r"book a cab", r"book.*taxi", r"cab\b"],
    "EDUCATION": [r"college", r"exam", r"study", r"school"],
    "HEALTHCARE": [r"doctor", r"fever", r"health", r"hospital"],
    "NEWS": [r"\bnews\b"],
    "CALCULATOR": [r"calculate", r"[0-9]+\s*[\+\-\*/]\s*[0-9]+"],
    "TIME": [r"\bwhat time\b", r"\btime is it\b"],
    "DATE": [r"\bwhat.*date\b", r"\btoday.*date\b"],
}


class IntentService:
    """
    Real distinction (spec section 12 & 41):
      - If a fine-tuned checkpoint exists at models/intent_classifier
        (produced by training/train_intent.py), load and use it — this is
        our real trained model.
      - Otherwise, fall back to a transparent keyword baseline and label
        every response 'Development Fallback (keyword baseline)' so the
        frontend never claims a trained model that doesn't exist.
    """

    def __init__(self):
        self.model = None
        self.model_name = "Development Fallback (keyword baseline)"
        self._try_load_trained_model()

    def _try_load_trained_model(self):
        if os.path.isdir(MODEL_DIR) and os.listdir(MODEL_DIR):
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch  # noqa: F401

                self._tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
                self.model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
                self.model_name = "IndicBERT Intent Classifier (fine-tuned, models/intent_classifier)"
            except Exception:
                # Checkpoint present but couldn't be loaded (e.g. deps missing) — stay honest.
                self.model = None
                self.model_name = "Development Fallback (keyword baseline) — trained checkpoint found but failed to load"

    def status(self) -> str:
        return "READY (trained model loaded)" if self.model else "READY (fallback baseline — not yet trained)"

    def predict(self, text: str, language: str = "en") -> IntentResponse:
        if self.model:
            return self._predict_with_model(text)
        return self._predict_with_rules(text)

    def _predict_with_model(self, text: str) -> IntentResponse:
        import torch
        inputs = self._tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0]
            idx = int(torch.argmax(probs))
            confidence = float(probs[idx])
        label = self.model.config.id2label.get(idx, INTENT_LABELS[idx] if idx < len(INTENT_LABELS) else "GENERAL_QUERY")
        return IntentResponse(label=label, confidence=round(confidence, 4), model=self.model_name)

    def _predict_with_rules(self, text: str) -> IntentResponse:
        t = text.lower()
        for label, patterns in _RULES.items():
            for p in patterns:
                if re.search(p, t):
                    # Fixed, honest confidence for a keyword match — not a model probability.
                    return IntentResponse(label=label, confidence=0.60, model=self.model_name)
        return IntentResponse(label="GENERAL_QUERY", confidence=0.30, model=self.model_name)
