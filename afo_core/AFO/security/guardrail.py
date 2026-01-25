# Trinity Score: 90.0 (Established by Chancellor)
import logging
import re

logger = logging.getLogger(__name__)


class PromptGuardrail:
    """Prompt Injection Guardrail for LLM Inputs"""

    def __init__(self) -> None:
        self.injection_patterns = [
            r"(ignore previous instructions)",
            r"(system prompt override)",
            r"(you are now)",
            r"(forget all rules)",
            r"(reveal your secret)",
        ]
        self.regex = re.compile("|".join(self.injection_patterns), re.IGNORECASE)

    def validate(self, input_text: str) -> bool:
        """Validates input text against injection patterns.
        Returns True if safe, False if unsafe.
        """
        if not input_text:
            return True

        if self.regex.search(input_text):
            logger.warning(f"🚨 Prompt Injection blocked: {input_text[:50]}...")
            return False

        return True


# Singleton instance
guardrail = PromptGuardrail()
