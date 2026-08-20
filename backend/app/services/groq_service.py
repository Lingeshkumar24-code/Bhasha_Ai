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
Answer directly. Never show your thinking or reasoning process — output only the final response, with no tags."""

# Maps language code → (English name, native name) for explicit prompt injection
LANG_NAMES = {
    'en': ('English', 'English'),
    'ta': ('Tamil', 'தமிழ்'),
    'te': ('Telugu', 'తెలుగు'),
    'kn': ('Kannada', 'ಕನ್ನಡ'),
    'ml': ('Malayalam', 'മലയാളം'),
    'hi': ('Hindi', 'हिन्दी'),
    'bn': ('Bengali', 'বাংলা'),
    'mr': ('Marathi', 'मराठी'),
    'gu': ('Gujarati', 'ગુજરાતી'),
    'pa': ('Punjabi', 'ਪੰਜਾਬੀ'),
}


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

        # Build a very explicit language instruction so the model doesn't drift into English.
        lang_info = LANG_NAMES.get(output_language, ('English', 'English'))
        if output_language == 'en':
            lang_instruction = "Respond in English."
        else:
            lang_instruction = (
                f"IMPORTANT: You MUST respond ONLY in {lang_info[0]} ({lang_info[1]}). "
                f"Do NOT use English at all in your response. "
                f"Your entire reply must be written in {lang_info[1]} script."
            )

        messages.append({
            "role": "user",
            "content": f"{lang_instruction}\n\n{message}",
        })

        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.5,
            max_tokens=512,
        )
        reply = completion.choices[0].message.content
        reply = self._clean_reply(reply)
        dialogue_manager.add_turn(session_id, "user", message)
        dialogue_manager.add_turn(session_id, "assistant", reply)
        return reply

    @staticmethod
    def _clean_reply(reply: str) -> str:
        if not reply:
            return ""
        # 1) Strip <think>…</think> and <thinking>…</thinking> blocks.
        #    The model (qwen3.x) emits <think>, not <thinking> — cover both.
        reply = re.sub(r'<think(?:ing)?>.*?</think(?:ing)?>', '', reply, flags=re.DOTALL)
        # 2) Strip ### Thinking / ### Reasoning CoT blocks (Llama style)
        reply = re.sub(
            r'###?\s*(thinking|thought|reasoning)[\s\S]*?(?=###?\s*response|$)',
            '', reply, flags=re.DOTALL | re.IGNORECASE,
        )
        # 3) Models that append "[Output]: <answer>" — take the LAST one.
        outputs = re.findall(r'\[Output\](?::)?\s*(.+)', reply, flags=re.DOTALL | re.IGNORECASE)
        if outputs:
            return outputs[-1].strip()
        # 4) Llama-style " thinking …  response <answer>"
        if re.match(r'\s* thinking', reply, flags=re.IGNORECASE) and ' response' in reply:
            return reply.split(' response')[-1].strip()
        return reply.strip()
