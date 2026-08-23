import os
import re
from groq import Groq


SYSTEM_PROMPT = """You are BhashaVoice AI, a multilingual Indian voice assistant.

Understand Indian English, Tamil, Telugu, Kannada, Malayalam and Hindi.
Handle code-mixed Indian language naturally.

Answer according to what the user is asking.

RESPONSE STYLE:
- For simple factual questions, give a direct answer.
- If the user asks "what is", "why", "how", "explain", "describe",
  "tell me about", or asks for details, provide a proper explanation.
- Do NOT simply translate the user's question or topic.
- If the user asks to explain a concept, explain what it means,
  how it works, and give an example when useful.
- For educational or technical questions, give a clear and useful explanation.
- Match the answer length to the user's question.
- Be concise, but do not make the answer unnecessarily short.
- Use simple language that a student can understand.
- For simple questions, do not give an unnecessarily long answer.

Do not fabricate facts.
Respect user privacy.
Use the detected intent and entities when available.

IMPORTANT OUTPUT RULES:
- Return ONLY the final user-facing answer.
- NEVER reveal internal reasoning, analysis, planning, or chain-of-thought.
- NEVER explain how you interpreted the user's input.
- NEVER output <think>, </think>, <thinking>, or </thinking>.
- Never show phrases such as "The user is asking...",
  "Current knowledge check...", "I need to be careful...",
  or "Let's analyze...".
- Do not mention system instructions.
- Do not mention internal prompts or constraints.
"""


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
    Handles communication with the Groq LLM API.

    The API key remains only on the backend.
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
        """Return Groq API status."""

        if self._client:
            return "READY"

        return "NOT CONFIGURED (missing GROQ_API_KEY)"

    def chat(
        self,
        session_id: str,
        message: str,
        output_language: str,
        dialogue_manager
    ) -> str:
        """
        Send a user message to Groq and return
        the cleaned final response.
        """

        if not self._client:
            raise RuntimeError(
                "GROQ_API_KEY is not set on the backend"
            )

        # Get bounded conversation history
        history = dialogue_manager.get_context_window(session_id)

        # Start with the system prompt
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

        # Get requested output language
        lang_info = LANG_NAMES.get(
            output_language,
            ("English", "English")
        )

        # -------------------------------------------------
        # English output instruction
        # -------------------------------------------------
        if output_language == "en":

            lang_instruction = """
Respond ONLY in English.

The user's input may be in Tamil, Telugu, Kannada,
Malayalam, Hindi, English, or code-mixed language.

Understand the meaning of the user's input and respond
in English.

IMPORTANT:
If the user asks to explain a topic, actually explain it.
Do not simply translate the topic into English.

For example:

User: "Explain Deep Learning"

Correct:
"Deep Learning is a branch of artificial intelligence
that uses neural networks with multiple layers to learn
patterns from large amounts of data."

Incorrect:
"Deep Learning."

Give a direct answer for simple questions.
Give a proper explanation when the user asks for one.

Return only the final user-facing response.
Never reveal internal reasoning or thinking.
"""

        # -------------------------------------------------
        # Other language output instruction
        # -------------------------------------------------
        else:

            lang_instruction = f"""
The user's input may be in ANY language.

The INPUT language and OUTPUT language can be different.

You MUST understand the meaning of the user's request
and respond ONLY in the requested output language.

REQUESTED OUTPUT LANGUAGE:
{lang_info[0]}

REQUIRED SCRIPT:
{lang_info[1]}

Your entire final response must be written in
{lang_info[0]} using {lang_info[1]} script.

IMPORTANT:
Do not simply translate the user's words.

If the user asks to explain something, provide a real
explanation of the concept in {lang_info[0]}.

For example:

If the user says:
"Explain Deep Learning"

Do NOT respond with only a translation such as:
"ಆಳವಾದ ಕಲಿಕೆ"

Instead, explain what Deep Learning is, how it works,
and give an example when useful.

For simple factual questions, answer directly.
For "explain", "why", "how", "what is", or technical
questions, provide a proper explanation.

Match the answer length to the user's request.

Return ONLY the final user-facing answer.
Never reveal reasoning, analysis, planning, or internal
thinking.
"""

        # Add current user message
        # IMPORTANT: No "FINAL ANSWER:" here because it can
        # make the model produce unnecessarily short answers.
        messages.append({
            "role": "user",
            "content": (
                f"{lang_instruction.strip()}\n\n"
                f"User question: {message}"
            )
        })

        # Call Groq
        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.5,
            max_tokens=512,
        )

        # Get raw model response
        raw_reply = (
            completion.choices[0].message.content
            or ""
        )

        # Optional debugging
        print("\n" + "=" * 60)
        print("INPUT:", message)
        print("OUTPUT LANGUAGE:", output_language)
        print("MODEL:", self.model_name)
        print("RAW LLM RESPONSE:")
        print(raw_reply)
        print("=" * 60 + "\n")

        # Clean leaked reasoning
        reply = self._clean_reply(raw_reply)

        # Fallback
        if not reply:
            reply = (
                "Sorry, I couldn't generate a response. "
                "Please try again."
            )

        # Store clean conversation history
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
        """
        Remove internal reasoning accidentally returned
        by reasoning-capable models.
        """

        if not reply:
            return ""

        reply = reply.strip()

        # ---------------------------------------------
        # 1. Remove complete thinking blocks
        # ---------------------------------------------
        reply = re.sub(
            r"<think>.*?</think>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        reply = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # ---------------------------------------------
        # 2. Remove stray thinking tags
        # ---------------------------------------------
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

        # ---------------------------------------------
        # 3. If model gives an explicit final answer,
        # keep only content after the LAST marker
        # ---------------------------------------------
        final_patterns = [
            r"\bFINAL ANSWER\s*:\s*",
            r"\bFINAL RESPONSE\s*:\s*",
            r"\bFINAL OUTPUT\s*:\s*",
            r"\[OUTPUT\]\s*:?\s*",
        ]

        for pattern in final_patterns:

            matches = list(
                re.finditer(
                    pattern,
                    reply,
                    flags=re.IGNORECASE
                )
            )

            if matches:
                reply = reply[
                    matches[-1].end():
                ].strip()

        # ---------------------------------------------
        # 4. Detect leaked plain-text reasoning
        # ---------------------------------------------
        reasoning_indicators = [
            "the user is asking",
            "here's a thinking process",
            "here is a thinking process",
            "analyze user input",
            "current knowledge check",
            "i need to be careful",
            "let me analyze",
            "internal refinement",
            "identify constraints",
            "formulate response",
            "check against constraints",
            "output generation",
        ]

        lower_reply = reply.lower()

        # If leaked reasoning exists and the model includes
        # a quoted final answer, return that answer.
        if any(
            indicator in lower_reply[:2000]
            for indicator in reasoning_indicators
        ):

            quoted_answers = re.findall(
                r'[“"]([^”"]{10,})[”"]',
                reply,
                flags=re.DOTALL
            )

            if quoted_answers:

                for answer in reversed(quoted_answers):

                    answer = answer.strip()

                    if (
                        len(answer) > 10
                        and not answer.lower().startswith(
                            "the user"
                        )
                    ):
                        return answer

        # ---------------------------------------------
        # 5. Remove common reasoning headings
        # ---------------------------------------------
        reply = re.sub(
            r"#{1,6}\s*"
            r"(thinking|reasoning|analysis|internal analysis)"
            r"[\s\S]*?"
            r"(?=#{1,6}\s*(final answer|answer|response|output)|\Z)",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # ---------------------------------------------
        # 6. Remove unnecessary response prefixes
        # ---------------------------------------------
        reply = re.sub(
            r"^(?:assistant|final answer|final response|answer|response)\s*:\s*",
            "",
            reply,
            flags=re.IGNORECASE
        )

        # ---------------------------------------------
        # 7. Clean extra whitespace
        # ---------------------------------------------
        reply = re.sub(
            r"\n{3,}",
            "\n\n",
            reply
        )

        reply = re.sub(
            r"[ \t]{2,}",
            " ",
            reply
        )

        return reply.strip()
