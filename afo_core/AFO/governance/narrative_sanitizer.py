import logging
import re

logger = logging.getLogger(__name__)


class NarrativeSanitizer:
    """
    Sanitizer for public narratives and results.
    美 (Beauty): Ensures public output is clean and professional.
    善 (Goodness): Filters potentially sensitive internal data patterns.
    """

    def __init__(self) -> None:
        # Basic patterns to sanitize (e.g., internal paths, dev-only notes)
        self.redact_patterns = [
            (r"/Users/[^/\s]+/", "/home/afo-worker/"),  # Sanitize developer paths
            (r"DEBUG:", "[LOG]"),
            (r"INTERNAL:", "[SECURE]"),
        ]

    def sanitize(self, text: str) -> str:
        """Sanitize a single narrative string."""
        if not isinstance(text, str):
            return str(text)

        sanitized = text
        for pattern, replacement in self.redact_patterns:
            sanitized = re.sub(pattern, replacement, sanitized)

        return sanitized.strip()


sanitizer = NarrativeSanitizer()
