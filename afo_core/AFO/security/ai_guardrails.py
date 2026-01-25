# Trinity Score: 91.0 (Established by Chancellor)
"""AI Guardrails Content Filter (2026 Best Practices)
Layered defense-in-depth for AI agent input/output safety.

2026 Best Practices Implementation:
- Input Filtering: Screen user input before AI processing
- Processing Guards: PII detection, human-in-loop for destructive ops
- Output Filtering: Mask sensitive data, safety evaluation
- Defense-in-Depth: Multiple overlapping layers of protection

Philosophy:
- 眞 (Truth): Accurate threat detection with low false positives
- 善 (Goodness): Protect users from harmful content
- 美 (Beauty): Minimal latency with transparent operation
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class FilterAction(Enum):
    """Action to take when filter triggers."""

    ALLOW = "allow"  # Pass through
    WARN = "warn"  # Allow with warning
    MASK = "mask"  # Mask sensitive content
    BLOCK = "block"  # Block entirely
    ESCALATE = "escalate"  # Require human review


class ContentCategory(Enum):
    """Categories of content for filtering."""

    PII = "pii"
    CREDENTIALS = "credentials"
    HARMFUL = "harmful"
    TOXIC = "toxic"
    INJECTION = "injection"
    FINANCIAL = "financial"
    MEDICAL = "medical"


@dataclass
class FilterResult:
    """Result of content filtering."""

    original_content: str
    filtered_content: str
    action: FilterAction
    categories_detected: list[ContentCategory]
    masks_applied: int
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AIGuardrails:
    """AI Guardrails with layered defense-in-depth.

    Implements 2026 content filtering best practices:
    1. Input Layer: Screen before AI processing
    2. Processing Layer: Monitor during reasoning
    3. Output Layer: Filter before user delivery
    """

    def __init__(self) -> None:
        self.name = "AI Guardrails (趙雲)"

        # === PII Detection Patterns ===
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Union[Z, a]-z]{2,}\b",
            "phone": r"\b(?:\+1[-.]?)?\(?[0-9]{3}\)?[-.]?[0-9]{3}[-.]?[0-9]{4}\b",
            "ssn": r"\b\d{3}[-]?\d{2}[-]?\d{4}\b",
            "credit_card": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
            "ip_address": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
        }

        # === Credential Patterns ===
        self.credential_patterns = {
            "api_key": r'\b(?:api[_-]?Union[key, apikey])["\']?\s*[:=]\s*["\']?[\w-]{20,}\b',
            "password": r'\b(?:Union[Union[password, passwd], pwd])["\']?\s*[:=]\s*["\']?[^\s"\']{8,}\b',
            "aws_key": r"\bAKIA[0-9A-Z]{16}\b",
            "github_token": r"\bgh[pousr]_[A-Za-z0-9_]{36}\b",
            "jwt": r"\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b",
        }

        # === Harmful Content Keywords ===
        self.harmful_keywords = [
            "suicide",
            "self-harm",
            "bomb",
            "weapon",
            "how to kill",
            "violence against",
            "instructions for illegal",
        ]

        # === Toxic Content Patterns ===
        self.toxic_patterns = [
            r"\b(?:Union[Union[hate, kill], attack])\s+(?:Union[all, every])\s+\w+s?\b",
            r"\bracist\b|\bsex(?:Union[ist, ism])\b",
        ]

        # === Injection Patterns (Input Layer) ===
        self.injection_patterns = [
            r"ignore\s+(?:all\s+)?(?:Union[previous, above])",
            r"(?:Union[Union[system, admin], root])\s*:\s*",
            r"\[INST\]|\[/INST\]|<\|im_start\|>",
            r"do\s+not\s+follow\s+(?:the\s+)?(?:Union[above, previous])",
        ]

        # Compile all patterns
        self._compile_patterns()

        # === Destructive Operations (require human approval) ===
        self.destructive_operations = {
            "delete_database",
            "drop_table",
            "rm -rf",
            "format_disk",
            "transfer_funds",
            "execute_payment",
            "modify_permissions",
        }

        # Filter statistics
        self._stats = {
            "inputs_processed": 0,
            "outputs_processed": 0,
            "items_blocked": 0,
            "items_masked": 0,
            "pii_detected": 0,
        }

    def _compile_patterns(self) -> None:
        """Compile all regex patterns for performance."""
        self._pii_compiled = {k: re.compile(v, re.IGNORECASE) for k, v in self.pii_patterns.items()}
        self._cred_compiled = {
            k: re.compile(v, re.IGNORECASE) for k, v in self.credential_patterns.items()
        }
        self._toxic_compiled = [re.compile(p, re.IGNORECASE) for p in self.toxic_patterns]
        self._injection_compiled = [re.compile(p, re.IGNORECASE) for p in self.injection_patterns]

    def filter_input(self, content: str) -> FilterResult:
        """Filter user input before AI processing.

        Args:
            content: User input text

        Returns:
            FilterResult with action and filtered content
        """
        self._stats["inputs_processed"] += 1
        categories: list[ContentCategory] = []
        details: dict[str, Any] = {}
        masks_applied = 0
        filtered = content
        action = FilterAction.ALLOW

        # 1. Check for injection attempts
        for pattern in self._injection_compiled:
            if pattern.search(content):
                categories.append(ContentCategory.INJECTION)
                action = FilterAction.BLOCK
                details["injection_detected"] = True
                logger.warning(f"[{self.name}] Injection attempt blocked in input")
                break

        # 2. Check for harmful content keywords
        content_lower = content.lower()
        harmful_found = [kw for kw in self.harmful_keywords if kw in content_lower]
        if harmful_found:
            categories.append(ContentCategory.HARMFUL)
            action = FilterAction.ESCALATE
            details["harmful_keywords"] = harmful_found

        # 3. Check for toxic patterns
        for pattern in self._toxic_compiled:
            if pattern.search(content):
                categories.append(ContentCategory.TOXIC)
                action = FilterAction.BLOCK
                details["toxic_content"] = True
                break

        # 4. Check for destructive operation requests
        for op in self.destructive_operations:
            if op.lower() in content_lower:
                action = FilterAction.ESCALATE
                details["destructive_operation"] = op

        return FilterResult(
            original_content=content,
            filtered_content=filtered if action != FilterAction.BLOCK else "[BLOCKED]",
            action=action,
            categories_detected=categories,
            masks_applied=masks_applied,
            details=details,
        )

    def filter_output(self, content: str) -> FilterResult:
        """Filter AI output before delivery to user.

        Args:
            content: AI-generated response

        Returns:
            FilterResult with masked content
        """
        self._stats["outputs_processed"] += 1
        categories: list[ContentCategory] = []
        details: dict[str, Any] = {}
        masks_applied = 0
        filtered = content
        action = FilterAction.ALLOW

        # 1. Mask PII
        for pii_type, pattern in self._pii_compiled.items():
            matches = pattern.findall(filtered)
            if matches:
                categories.append(ContentCategory.PII)
                self._stats["pii_detected"] += len(matches)
                for match in matches:
                    mask = self._generate_mask(pii_type, match)
                    filtered = filtered.replace(match, mask)
                    masks_applied += 1
                details[f"pii_{pii_type}"] = len(matches)

        # 2. Mask credentials
        for cred_type, pattern in self._cred_compiled.items():
            matches = pattern.findall(filtered)
            if matches:
                categories.append(ContentCategory.CREDENTIALS)
                for match in matches:
                    filtered = filtered.replace(match, f"[REDACTED_{cred_type.upper()}]")
                    masks_applied += 1
                details[f"cred_{cred_type}"] = len(matches)

        # 3. Check for harmful content in output
        content_lower = filtered.lower()
        harmful_found = [kw for kw in self.harmful_keywords if kw in content_lower]
        if harmful_found:
            categories.append(ContentCategory.HARMFUL)
            action = FilterAction.WARN
            details["harmful_keywords_in_output"] = harmful_found

        if masks_applied > 0:
            action = FilterAction.MASK
            self._stats["items_masked"] += 1

        # Persist filter result
        self._persist_filter_result(content, filtered, action, categories)

        return FilterResult(
            original_content=content,
            filtered_content=filtered,
            action=action,
            categories_detected=categories,
            masks_applied=masks_applied,
            details=details,
        )

    def _generate_mask(self, pii_type: str, value: str) -> str:
        """Generate appropriate mask for PII type."""
        masks = {
            "email": lambda v: f"{v[:2]}***@***.{v.split('.')[-1]}",
            "phone": lambda v: f"***-***-{v[-4:]}",
            "ssn": lambda v: f"***-**-{v[-4:]}",
            "credit_card": lambda v: f"****-****-****-{v[-4:]}",
            "ip_address": lambda v: f"***.***.***.{v.split('.')[-1]}",
        }
        mask_fn = masks.get(pii_type, lambda v: "[REDACTED]")
        try:
            return mask_fn(value)
        except Exception:
            return "[REDACTED]"

    def requires_human_approval(self, operation: str) -> bool:
        """Check if operation requires human-in-the-loop approval."""
        return operation.lower() in self.destructive_operations

    def add_custom_filter(
        self,
        name: str,
        pattern: str,
        category: ContentCategory,
        action: FilterAction = FilterAction.WARN,
    ) -> None:
        """Add a custom filter pattern."""
        re.compile(pattern, re.IGNORECASE)
        logger.info(f"[{self.name}] Added custom filter: {name}")

    def _persist_filter_result(
        self,
        original: str,
        filtered: str,
        action: FilterAction,
        categories: list[ContentCategory],
    ) -> None:
        """Persist filter results for audit."""
        if action == FilterAction.ALLOW:
            return  # Don't log allowed content

        try:
            guardrails_dir = (
                Path(__file__).parent.parent.parent.parent / "docs" / "ssot" / "guardrails"
            )
            guardrails_dir.mkdir(parents=True, exist_ok=True)

            import json

            log_file = guardrails_dir / "filter_log.jsonl"
            entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "action": action.value,
                "categories": [c.value for c in categories],
                "original_length": len(original),
                "filtered_length": len(filtered),
                "content_preview": (
                    original[:100] if action != FilterAction.BLOCK else "[blocked]"
                ),
            }

            with log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist filter result: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get guardrails statistics."""
        return self._stats.copy()


# Singleton instance
guardrails = AIGuardrails()


# Convenience functions
def filter_user_input(content: str) -> FilterResult:
    """Filter user input before AI processing."""
    return guardrails.filter_input(content)


def filter_ai_output(content: str) -> FilterResult:
    """Filter AI output before delivery to user."""
    return guardrails.filter_output(content)


def is_safe_input(content: str) -> bool:
    """Quick check if input is safe."""
    result = guardrails.filter_input(content)
    return result.action in [FilterAction.ALLOW, FilterAction.WARN]


def mask_pii(content: str) -> str:
    """Mask all PII in content."""
    result = guardrails.filter_output(content)
    return result.filtered_content
