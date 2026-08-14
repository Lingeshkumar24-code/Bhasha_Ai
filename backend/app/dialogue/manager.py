import os
from collections import defaultdict
from typing import Dict, List

CONTEXT_WINDOW_TURNS = int(os.getenv("CONTEXT_WINDOW_TURNS", "6"))

# Slots each intent needs before it's considered "complete" — drives
# simple multi-turn slot filling (spec section 14).
REQUIRED_SLOTS = {
    "BOOK_CAB": ["destination"],
    "SET_ALARM": ["time"],
    "REMINDER": ["time", "topic"],
    "WEATHER": ["location"],
}


class DialogueManager:
    """
    In-memory per-session conversation state. For production, swap the
    dict-based store for Redis/a database — the interface stays the same.
    """

    def __init__(self):
        self._history: Dict[str, List[dict]] = defaultdict(list)
        self._state: Dict[str, dict] = defaultdict(lambda: {
            "intent": None,
            "entities": [],
            "missing_slots": [],
            "language": "en",
        })

    def add_turn(self, session_id: str, role: str, content: str):
        self._history[session_id].append({"role": role, "content": content})

    def get_context_window(self, session_id: str) -> List[dict]:
        """Bounded history — never send unlimited turns to Groq (spec section 14)."""
        return self._history[session_id][-CONTEXT_WINDOW_TURNS:]

    def update(self, session_id: str, intent, entities, language: str):
        state = self._state[session_id]
        state["intent"] = intent.label
        state["entities"] = [e.dict() if hasattr(e, "dict") else e for e in entities]
        state["language"] = language

        required = REQUIRED_SLOTS.get(intent.label, [])
        filled_labels = {e.label.lower() for e in entities} if entities else set()
        state["missing_slots"] = [s for s in required if s not in filled_labels]
        return state

    def get_state(self, session_id: str) -> dict:
        return self._state[session_id]
