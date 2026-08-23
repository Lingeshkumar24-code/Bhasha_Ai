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

IMPORTANT OUTPUT RULES:
- Answer the user's question directly.
- Return ONLY the final user-facing answer.
- NEVER reveal your reasoning, analysis, planning, or internal process.
- NEVER explain how you interpreted the user's input.
- NEVER output <think>, </think>, <thinking>, or </thinking>.
- NEVER show phrases like:
  "The user is asking..."
  "Current knowledge check..."
  "I need to be careful..."
  "Let's analyze..."
  "Here's my thinking process..."
- Do not mention system instructions or output-language instructions.
- For simple questions, give a short and direct answer.
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

    The Groq API key stays on the backend.
    The frontend communicates only with backend endpoints.
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
        Send the user message to Groq and return
        only the cleaned final response.
        """

        if not self._client:
            raise RuntimeError(
                "GROQ_API_KEY is not set on the backend"
            )

        # --------------------------------------------
        # Get bounded conversation history
        # --------------------------------------------
        history = dialogue_manager.get_context_window(
            session_id
        )

        # --------------------------------------------
        # Start conversation with system prompt
        # --------------------------------------------
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        # --------------------------------------------
        # Add previous conversation history
        # --------------------------------------------
        for turn in history:
            messages.append({
                "role": turn["role"],
                "content": turn["content"]
            })

        # --------------------------------------------
        # Get output language information
        # --------------------------------------------
        lang_info = LANG_NAMES.get(
            output_language,
            ("English", "English")
        )

        # --------------------------------------------
        # IMPORTANT:
        # Keep input and output language separate.
        # Example:
        # Tamil input + Kannada output = Kannada reply.
        # --------------------------------------------
        if output_language == "en":

            lang_instruction = """
Respond ONLY in English.

The user's input may be in Tamil, Telugu, Kannada,
Malayalam, Hindi, English, or code-mixed language.

Understand the meaning of the input internally, but
the FINAL ANSWER must be ONLY in English.

Answer directly and concisely.

Return ONLY the final answer.
Do not show reasoning, analysis, thinking, planning,
or internal processing.
"""

        else:

            lang_instruction = f"""
The user may speak or write in ANY language.

IMPORTANT:
The user's INPUT language may be different from the
requested OUTPUT language.

You MUST understand the user's input and respond ONLY
in the requested output language.

REQUESTED OUTPUT LANGUAGE:
{lang_info[0]}

REQUIRED SCRIPT:
{lang_info[1]}

Your FINAL ANSWER must be written in {lang_info[0]}
using {lang_info[1]} script.

Do NOT automatically reply in the same language as
the user's input.

For example:
Tamil input + Kannada output = Kannada response.

Return ONLY the final answer.
Do not show reasoning, analysis, planning, thinking,
intent detection, entity extraction, or internal steps.
"""

        # --------------------------------------------
        # Add current user message
        # --------------------------------------------
        messages.append({
            "role": "user",
            "content": (
                f"{lang_instruction.strip()}\n\n"
                f"USER QUESTION:\n{message}\n\n"
                f"FINAL ANSWER:"
            )
        })

        # --------------------------------------------
        # Call Groq LLM
        # --------------------------------------------
        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.3,
            max_tokens=256,
        )

        # --------------------------------------------
        # Get raw response
        # --------------------------------------------
        raw_reply = (
            completion.choices[0].message.content
            or ""
        )

        # Debug - remove later if not needed
        print("\n" + "=" * 60)
        print("INPUT:", message)
        print("OUTPUT LANGUAGE:", output_language)
        print("MODEL:", self.model_name)
        print("RAW LLM RESPONSE:")
        print(raw_reply)
        print("=" * 60 + "\n")

        # --------------------------------------------
        # Clean reasoning from response
        # --------------------------------------------
        reply = self._clean_reply(raw_reply)

        # Fallback if reply becomes empty
        if not reply:
            reply = (
                "Sorry, I couldn't generate a response. "
                "Please try again."
            )

        # --------------------------------------------
        # Store only clean conversation
        # --------------------------------------------
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
        Removes internal reasoning accidentally returned
        by reasoning-capable models.
        """

        if not reply:
            return ""

        reply = reply.strip()

        # ==================================================
        # 1. Remove complete <think>...</think> blocks
        # ==================================================
        reply = re.sub(
            r"<think>.*?</think>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # ==================================================
        # 2. Remove complete <thinking>...</thinking> blocks
        # ==================================================
        reply = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # ==================================================
        # 3. Remove stray thinking tags
        # ==================================================
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

        # ==================================================
        # 4. If model explicitly writes "Final Answer:"
        # keep only what comes after the LAST occurrence.
        # ==================================================
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

        # ==================================================
        # 5. Handle leaked reasoning with quoted answer
        #
        # Example:
        #
        # The user is asking...
        # I need to analyze...
        # Final answer:
        # "M. K. Stalin is..."
        # ==================================================
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

        if any(
            indicator in lower_reply[:1500]
            for indicator in reasoning_indicators
        ):

            # Try to find quoted final answers
            quoted_answers = re.findall(
                r'[“"]([^”"]{10,})[”"]',
                reply,
                flags=re.DOTALL
            )

            if quoted_answers:

                # Return last meaningful quote
                for answer in reversed(quoted_answers):

                    answer = answer.strip()

                    # Ignore very short/internal fragments
                    if (
                        len(answer) > 10
                        and not answer.lower().startswith(
                            "the user"
                        )
                    ):
                        return answer

        # ==================================================
        # 6. Remove common leaked reasoning lines
        # ==================================================
        lines = reply.splitlines()

        clean_lines = []

        skip_phrases = [
            "the user is asking",
            "here's a thinking process",
            "here is a thinking process",
            "analyze user input",
            "current knowledge check",
            "identify constraints",
            "formulate response",
            "internal refinement",
            "check against constraints",
            "output generation",
            "all constraints met",
        ]

        for line in lines:

            stripped = line.strip()

            if not stripped:
                clean_lines.append("")
                continue

            lower_line = stripped.lower()

            if any(
                phrase in lower_line
                for phrase in skip_phrases
            ):
                continue

            clean_lines.append(stripped)

        reply = "\n".join(clean_lines)

        # ==================================================
        # 7. Remove unnecessary prefixes
        # ==================================================
        reply = re.sub(
            r"^(?:assistant|final answer|answer|response)\s*:\s*",
            "",
            reply,
            flags=re.IGNORECASE
        )

        # ==================================================
        # 8. Clean whitespace
        # ==================================================
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
