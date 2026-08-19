import os
import re
from groq import Groq

SYSTEM_PROMPT = """You are BhashaVoice AI, a multilingual Indian voice assistant.

Understand Indian English, Tamil, Telugu, Kannada, Malayalam and Hindi.
Handle code-mixed Indian language naturally.
Be concise and conversational.
Do not fabricate facts.
Respect user privacy.
Respond in the requested output language.
Use the detected intent and entities when available."""


class GroqService:
    """
    Talks to Groq's LLM API. The API key NEVER leaves the backend —
    the frontend only ever calls our own /api/chat or /api/voice/full-pipeline.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv("GROQ_MODEL", "qwen/qwen3.6-27b")
        self._client = Groq(api_key=self.api_key) if self.api_key else None

    def status(self) -> str:
        return "READY" if self._client else "NOT CONFIGURED (missing GROQ_API_KEY)"

    def chat(self, session_id: str, message: str, output_language: str, dialogue_manager) -> str:
        if not self._client:
            raise RuntimeError("GROQ_API_KEY is not set on the backend")

        history = dialogue_manager.get_context_window(session_id)  # bounded, not unlimited history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({
            "role": "user",
            "content": f"[Respond in language code: {output_language}]\n{message}",
        })

        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.5,
            max_tokens=512,
        )
        reply = completion.choices[0].message.content
        reply = re.sub(r"<think>.*?</think>", "", reply, flags=re.DOTALL).strip()
        dialogue_manager.add_turn(session_id, "user", message)
        dialogue_manager.add_turn(session_id, "assistant", reply)
        return reply
