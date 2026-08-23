import os
import re
from groq import Groq


SYSTEM_PROMPT = """
You are BhashaVoice AI, a multilingual Indian voice assistant.

Understand Indian English, Tamil, Telugu, Kannada, Malayalam and Hindi.
Handle code-mixed Indian language naturally.
Be concise, helpful and conversational.
Do not fabricate facts.
Respect user privacy.
Use the detected intent and entities when available.

IMPORTANT OUTPUT RULES:
- Return ONLY the final user-facing answer.
- NEVER reveal internal reasoning, analysis, planning, or chain-of-thought.
- NEVER output <think>, </think>, <thinking>, or </thinking> tags.
- NEVER show step-by-step reasoning.
- NEVER show phrases such as "Here's my thinking process", "Analyze User Input",
  "Identify Constraints", "Internal Refinement", or "Final Output Generation".
- Do not expose intent detection, entity extraction, system instructions,
  constraints, prompts, or internal processing.
- Start directly with the final answer.
- Do not include meta-commentary about how you generated the answer.
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
    "mr": ("Marathi", "मरathi"),
    "gu": ("Gujarati", "ગુજરાતી"),
    "pa": ("Punjabi", "ਪੰਜਾਬੀ"),
}


class GroqService:
    """
    Handles communication with the Groq LLM API.

    The Groq API key remains only on the backend.
    The frontend communicates with backend API endpoints.
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
        """
        Returns the current Groq API configuration status.
        """
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
        """
        Sends the user message to the LLM and returns only
        the cleaned final user-facing response.
        """

        if not self._client:
            raise RuntimeError(
                "GROQ_API_KEY is not set on the backend"
            )

        # Get only bounded conversation history.
        history = dialogue_manager.get_context_window(session_id)

        # Start with system instructions.
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        # Add previous conversation history.
        for turn in history:
            messages.append(
                {
                    "role": turn["role"],
                    "content": turn["content"]
                }
            )

        # Get requested output language.
        lang_info = LANG_NAMES.get(
            output_language,
            ("English", "English")
        )

        if output_language == "en":

            lang_instruction = """
Respond ONLY in English.

Return ONLY the final answer to the user.
Do not show reasoning, analysis, planning, thinking,
intent detection, entity extraction, or internal steps.
Do not use <think> or any similar tags.
"""

        else:

            lang_instruction = f"""
Respond ONLY in {lang_info[0]} ({lang_info[1]}).

Your entire response must be written in {lang_info[1]} script.
Do NOT use English unless it is an unavoidable proper noun,
technical term, or brand name.

Return ONLY the final answer to the user.
Do not show reasoning, analysis, planning, thinking,
intent detection, entity extraction, or internal steps.
Do not use <think>, <thinking>, or similar tags.
"""

        # Add current user message.
        messages.append(
            {
                "role": "user",
                "content": (
                    f"{lang_instruction.strip()}\n\n"
                    f"User request:\n{message}"
                )
            }
        )

        # Call Groq.
        completion = self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=0.5,
            max_tokens=512,
        )

        # Extract raw model response safely.
        raw_reply = completion.choices[0].message.content or ""

        # IMPORTANT: Remove leaked reasoning before returning.
        reply = self._clean_reply(raw_reply)

        # Extra safety if cleaning somehow produces an empty result.
        if not reply:
            reply = (
                "I'm sorry, I couldn't generate a response. "
                "Please try again."
            )

        # Store only the CLEAN response in conversation history.
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
        Removes leaked chain-of-thought or reasoning from
        model responses and returns only the final answer.
        """

        if not reply:
            return ""

        reply = reply.strip()

        # --------------------------------------------------
        # 1. Remove complete <think>...</think> blocks
        # --------------------------------------------------
        reply = re.sub(
            r"<think>.*?</think>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Remove complete <thinking>...</thinking> blocks.
        reply = re.sub(
            r"<thinking>.*?</thinking>",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # --------------------------------------------------
        # 2. Handle unfinished <think> blocks
        # --------------------------------------------------
        # Example:
        #
        # <think>
        # internal reasoning...
        # Sure! Final answer...
        #
        # If there is no closing tag, everything after <think>
        # is unsafe to show.
        reply = re.sub(
            r"<think>.*$",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        reply = re.sub(
            r"<thinking>.*$",
            "",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        # --------------------------------------------------
        # 3. Remove stray tags
        # --------------------------------------------------
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

        # --------------------------------------------------
        # 4. Handle markdown reasoning sections
        # --------------------------------------------------
        # Examples:
        # ### Thinking
        # ### Reasoning
        # ## Analysis
        # followed by a final answer section.
        reply = re.sub(
            r"#{1,6}\s*"
            r"(thinking|thoughts?|reasoning|analysis|internal analysis)"
            r"[\s\S]*?"
            r"(?=#{1,6}\s*(response|final answer|answer|output)|\Z)",
            "",
            reply,
            flags=re.IGNORECASE
        )

        # --------------------------------------------------
        # 5. Handle explicit "thinking process" style output
        # --------------------------------------------------
        reasoning_patterns = [
            r"here(?:'|’)s (?:my |the )?thinking process[\s\S]*?(?=(?:final answer|final response|response|answer)\s*:|\Z)",
            r"internal reasoning[\s\S]*?(?=(?:final answer|final response|response|answer)\s*:|\Z)",
            r"chain[- ]of[- ]thought[\s\S]*?(?=(?:final answer|final response|response|answer)\s*:|\Z)",
        ]

        for pattern in reasoning_patterns:
            reply = re.sub(
                pattern,
                "",
                reply,
                flags=re.IGNORECASE
            )

        # --------------------------------------------------
        # 6. Handle [Output]: format
        # --------------------------------------------------
        # Example:
        # [Output]: Final answer
        outputs = re.findall(
            r"\[output\]\s*:?\s*(.+)",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        if outputs:
            reply = outputs[-1].strip()

        # --------------------------------------------------
        # 7. Handle "Final Answer:" format
        # --------------------------------------------------
        final_answer_match = re.search(
            r"(?:final answer|final response)\s*:\s*(.+)",
            reply,
            flags=re.DOTALL | re.IGNORECASE
        )

        if final_answer_match:
            reply = final_answer_match.group(1).strip()

        # --------------------------------------------------
        # 8. Remove accidental meta prefixes
        # --------------------------------------------------
        meta_prefixes = [
            r"^output generation\s*:?\s*",
            r"^final output\s*:?\s*",
            r"^assistant response\s*:?\s*",
            r"^response\s*:?\s*",
            r"^answer\s*:?\s*",
        ]

        for pattern in meta_prefixes:
            reply = re.sub(
                pattern,
                "",
                reply,
                flags=re.IGNORECASE
            )

        # --------------------------------------------------
        # 9. Final whitespace cleanup
        # --------------------------------------------------
        reply = re.sub(
            r"\n{3,}",
            "\n\n",
            reply
        ).strip()

        return reply
