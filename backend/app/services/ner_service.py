import os
import re
from typing import List
from app.api.schemas import Entity

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "models", "ner_model")

# Small city/location gazetteer for the honest rule-based fallback.
_CITIES = [
    "chennai", "bengaluru", "bangalore", "hyderabad", "coimbatore", "madurai",
    "kochi", "thiruvananthapuram", "mysuru", "mysore", "mangaluru", "vijayawada",
    "delhi", "mumbai", "pune", "kolkata", "airport",
]

_TIME_RE = re.compile(r"\b(\d{1,2}(:\d{2})?\s?(am|pm|mani))\b", re.I)
_DATE_RE = re.compile(r"\b(today|tomorrow|yesterday|naalaikku|inru|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b", re.I)


class NERService:
    """Same real-vs-fallback honesty pattern as IntentService (see section 41/42)."""

    def __init__(self):
        self.model = None
        self.model_name = "Development Fallback (regex + gazetteer)"
        self._try_load_trained_model()

    def _try_load_trained_model(self):
        if os.path.isdir(MODEL_DIR) and os.listdir(MODEL_DIR):
            try:
                from transformers import AutoTokenizer, AutoModelForTokenClassification
                import torch  # noqa: F401

                self._tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
                self.model = AutoModelForTokenClassification.from_pretrained(MODEL_DIR)
                self.model_name = "IndicBERT NER Model (fine-tuned, models/ner_model)"
            except Exception:
                self.model = None
                self.model_name = "Development Fallback (regex + gazetteer) — trained checkpoint found but failed to load"

    def status(self) -> str:
        return "READY (trained model loaded)" if self.model else "READY (fallback baseline — not yet trained)"

    def extract(self, text: str, language: str = "en") -> List[Entity]:
        if self.model:
            return self._extract_with_model(text)
        return self._extract_with_rules(text)

    def _extract_with_model(self, text: str) -> List[Entity]:
        import torch
        tokens = self._tokenizer(text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = self.model(**tokens).logits[0]
        preds = torch.argmax(logits, dim=-1).tolist()
        id2label = self.model.config.id2label
        word_ids = tokens.word_ids()
        results, seen = [], set()
        for i, wid in enumerate(word_ids):
            if wid is None or wid in seen:
                continue
            label = id2label.get(preds[i], "O")
            if label != "O":
                span = tokens.token_to_chars(i)
                results.append(Entity(text=text[span.start:span.end], label=label.replace("B-", "").replace("I-", ""),
                                       start=span.start, end=span.end))
            seen.add(wid)
        return results

    def _extract_with_rules(self, text: str) -> List[Entity]:
        entities: List[Entity] = []
        low = text.lower()

        for city in _CITIES:
            for m in re.finditer(rf"\b{re.escape(city)}\b", low):
                entities.append(Entity(text=text[m.start():m.end()], label="LOCATION", start=m.start(), end=m.end()))

        for m in _TIME_RE.finditer(text):
            entities.append(Entity(text=m.group(0), label="TIME", start=m.start(), end=m.end()))

        for m in _DATE_RE.finditer(text):
            entities.append(Entity(text=m.group(0), label="DATE", start=m.start(), end=m.end()))

        return entities
