"""
PII Redaction Middleware
Provides regex-based PII redaction to Sanitize prompts before sending to LLM.
"""

import re


class PIIRedactor:
    """
    Simple PII Redaction utility using regex patterns.
    Can be used as a pre-processor for AIRequests.
    """

    # Common PII Patterns
    PATTERNS = {
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "PHONE": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    }

    @classmethod
    def redact(cls, text: str) -> str:
        """
        Redacts PII from the given text.
        """
        redacted_text = text
        for label, pattern in cls.PATTERNS.items():
            redacted_text = re.sub(pattern, f"[{label}_REDACTED]", redacted_text)
        return redacted_text

    @classmethod
    def redact_query(cls, query: str) -> str:
        """Helper to redact specific query strings"""
        return cls.redact(query)
