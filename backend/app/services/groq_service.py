import os
import re
from groq import Groq


SYSTEM_PROMPT = """You are BhashaVoice AI, a multilingual Indian voice assistant.

Understand Indian English, Tamil, Telugu, Kannada, Malayalam and Hindi.
Handle code-mixed Indian language naturally.
Be concise and conversational.
Do not fabricate facts.
Respect user privacy.
Use the detected intent and entities when available.

Answer directly.

IMPORTANT:
Return only the final user-facing response.
Never reveal internal reasoning, analysis, planning, or chain-of-thought.
Never output <think>, </think>, <thinking>, or </thinking> tags.
Do not show internal processing, constraints, or step-by-step analysis.
"""


# Maps language code → (English name, native name)
LANG_NAMES = {
    "en": ("English", "English"),
    "ta": ("Tamil", "தமிழ்"),
    "te": ("Telugu", "తెలుగు"),
    "kn": ("Kannada", "ಕನ್ನಡ"),
    "ml": ("Malayalam", "മലയാളം"),
    "hi": ("Hindi", "हिन्दी"),
    "bn": ("Bengali", "বাংলা"),
    "mr": ("Marathi", "मराठी"),
    "gu": ("Gujarati", "ગુજરાતી"),
    "pa": ("Punjabi", "ਪੰਜਾਬੀ"),
}


class GroqService:
    """
    Talks to Groq's LLM API.
    The API key never leaves the backend.
    """

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model_name = os.getenv(
            "GROQ_MODEL",
            "qwen/qwen3.6-27b"
        )

        self._client = (
            Groq(api_key=self.api_key)
            if self.api_key
            else None
        )

    def status(self) -> str:
        return (
            "READY"
            if self._client
            else "NOT CONFIGURED (missing GROQ_API_KEY)"
        )

    def chat(
        self,
        session_id: str,
        message: str,
        output_language: str,
        dialogue_manager
    ) -> str:

        if not self._client:
            raise RuntimeError(
                "GROQ_API_KEY is not set on the backend"
            )

        # Get bounded conversation history
        history = dialogue_manager.get_context_window(session_id)

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        # Add previous conversation
        for turn in history:
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })

        # -------------------------------
        # OUTPUT LANGUAGE INSTRUCTION
        # Keep this close to your original
        # -------------------------------
        lang_info = LANG_NAMES.get(
            output_language,
            ("English", "English")
        )

        if output_language == "en":

            lang_instruction = (
                "Respond in English. "
                "The user's input may be in any language, "
                "but the final answer must be in English."
            )

        else:

            lang_instruction = (
                f"IMPORTANT: You MUST respond ONLY in "
                f"{lang_info[0]} ({lang_info[1]}). "
                f"The user's input language may be different "
                f"from the requested output language. "
                f"Do NOT respond in the input language unless "
                f"it is also the requested output language. "
                f"Your entire reply must be written in "
                f"{lang_info[1]} script. "
                f"Return only the final answer. "
                f"Never show thinking, reasoning, analysis, "
                f"or <think> tags."
            )

        # Add current user message
        messages.append({
            "role": "user",
            "content": (
                f"{lang_instruction}\n\n"
                f"{message}"
            )
        })

        # Call Groq
        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.5,
            max_tokens=512,
        )

        # Get raw reply
        reply = completion.choices[0].message.content or ""

        # Clean ONLY reasoning output.
        # Do not change or translate the actual answer.
        reply = self._clean_reply(reply)

        # Store conversation
        dialogue_manager.add_turn(
            session_id,
            "user",
            message
        )

        dialogue_manager.add_turn(
            session_id,
            "assistant",
            reply
        )

        return reply


    @staticmethod
    def _clean_reply(reply: str) -> str:

        if not reply:
            return ""

        # Remove complete <think>...</think>
        reply = re.sub(
            r"<think>.*?</think>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Remove complete <thinking>...</thinking>
        reply = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Remove remaining standalone tags
        reply = re.sub(
            r"</?think>",
            "",
            reply,
            flags=re.IGNORECASE
        )

        reply = re.sub(
            r"</?thinking>",
            "",
            reply,
            flags=re.IGNORECASE
        )

        # Clean extra whitespace
        reply = re.sub(
            r"\n{3,}",
            "\n\n",
            reply
        ).strip()

        return reply
