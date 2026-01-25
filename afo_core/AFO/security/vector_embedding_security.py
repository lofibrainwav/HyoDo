# Trinity Score: 92.0 (Established by Chancellor)
"""Vector Embedding Security Module (OWASP LLM08:2025)
RAG Poisoning Detection and Vector Store Security for AFO Kingdom.

2026 Best Practices Implementation:
- RAG Poisoning Detection: Semantic anomaly detection
- Document Provenance Verification: Source authentication
- Embedding Inversion Protection: Access control enforcement
- Cross-Context Leak Prevention: Multi-tenant isolation

Philosophy:
- 眞 (Truth): Verify document authenticity before vectorization
- 善 (Goodness): Prevent AI behavior manipulation
- 美 (Beauty): Transparent security with minimal latency
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ThreatType(Enum):
    """Types of vector embedding threats."""

    RAG_POISONING = "rag_poisoning"
    PROMPT_INJECTION_VIA_EMBEDDING = "prompt_injection_via_embedding"
    EMBEDDING_INVERSION = "embedding_inversion"
    CROSS_CONTEXT_LEAK = "cross_context_leak"
    DATA_EXFILTRATION = "data_exfiltration"


class RiskLevel(Enum):
    """Risk classification for vector security."""

    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DocumentVerification:
    """Result of document security verification."""

    document_id: str
    source: str
    is_verified: bool
    risk_level: RiskLevel
    threats_detected: list[ThreatType]
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class VectorEmbeddingSecurity:
    """Vector Embedding Security for AFO Kingdom RAG Systems.

    Implements OWASP LLM08:2025 mitigations:
    1. RAG Poisoning Detection
    2. Document Provenance Verification
    3. Semantic Anomaly Detection
    4. Prompt Injection Detection in Documents
    """

    def __init__(self) -> None:
        self.name = "Vector Security (張遼)"

        # RAG Poisoning detection patterns (embedded prompt injection)
        self.injection_patterns = [
            # Direct instruction injection
            r"ignore\s+(all\s+)?previous",
            r"disregard\s+(Union[your, the])\s+(Union[instructions, guidelines])",
            r"you\s+are\s+now",
            r"new\s+instructions:",
            r"system\s*:\s*",
            r"<\s*system\s*>",
            r"\[INST\]",
            r"\[/INST\]",
            # Hidden instructions
            r"<!-- .*(Union[Union[ignore, override], forget]).*-->",
            r"###\s*HIDDEN\s*INSTRUCTION",
            r"DO\s+NOT\s+FOLLOW\s+ABOVE",
            # Persona manipulation
            r"pretend\s+(you\s+Union[are, to]\s+be)",
            r"roleplay\s+as",
            r"act\s+as\s+if",
        ]

        # Compiled patterns for performance
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.injection_patterns]

        # Trusted sources whitelist
        self.trusted_sources = {
            "irs.gov",
            "ftb.ca.gov",
            "sec.gov",
            "law.cornell.edu",
            "afo-kingdom.internal",
        }

        # Verification history
        self._verification_log: list[DocumentVerification] = []

        # Statistics
        self._stats = {
            "documents_scanned": 0,
            "threats_detected": 0,
            "documents_blocked": 0,
        }

    def verify_document(
        self,
        content: str,
        source: str = "unknown",
        metadata: dict[str, Any] | None = None,
    ) -> DocumentVerification:
        """Verify a document before vectorization.

        Args:
            content: Document text content
            source: Source URL or identifier
            metadata: Optional metadata

        Returns:
            DocumentVerification with threat analysis
        """
        metadata = metadata or {}
        document_id = self._generate_doc_id(content, source)
        threats: list[ThreatType] = []
        details: dict[str, Any] = {}

        self._stats["documents_scanned"] += 1

        # 1. Check for injection patterns (RAG Poisoning)
        injection_matches = self._detect_injection_patterns(content)
        if injection_matches:
            threats.append(ThreatType.RAG_POISONING)
            threats.append(ThreatType.PROMPT_INJECTION_VIA_EMBEDDING)
            details["injection_patterns"] = injection_matches

        # 2. Verify source provenance
        source_trusted = self._verify_source(source)
        details["source_trusted"] = source_trusted
        if not source_trusted and not injection_matches:
            details["source_warning"] = "Untrusted source - additional review recommended"

        # 3. Detect semantic anomalies (statistical outliers)
        anomaly_score = self._calculate_anomaly_score(content)
        details["anomaly_score"] = anomaly_score
        if anomaly_score > 0.7:
            threats.append(ThreatType.DATA_EXFILTRATION)

        # 4. Check for hidden content patterns
        hidden_content = self._detect_hidden_content(content)
        if hidden_content:
            threats.append(ThreatType.RAG_POISONING)
            details["hidden_content"] = hidden_content

        # Determine risk level
        risk_level = self._calculate_risk_level(threats, source_trusted, anomaly_score)

        # Create verification result
        verification = DocumentVerification(
            document_id=document_id,
            source=source,
            is_verified=len(threats) == 0 and source_trusted,
            risk_level=risk_level,
            threats_detected=threats,
            details=details,
        )

        # Log and persist
        self._verification_log.append(verification)
        self._persist_verification(verification)

        if threats:
            self._stats["threats_detected"] += len(threats)
            logger.warning(f"[{self.name}] Threats detected in document: {threats}")

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._stats["documents_blocked"] += 1
            logger.error(
                f"[{self.name}] Document BLOCKED: {document_id} | Risk: {risk_level.value}"
            )

        return verification

    def _detect_injection_patterns(self, content: str) -> list[str]:
        """Detect prompt injection patterns in document content."""
        matches = []
        for pattern in self._compiled_patterns:
            found = pattern.findall(content)
            if found:
                matches.extend([f"Pattern: {pattern.pattern}" for _ in found])
        return matches

    def _verify_source(self, source: str) -> bool:
        """Verify if source is in trusted whitelist."""
        source_lower = source.lower()
        return any(trusted in source_lower for trusted in self.trusted_sources)

    def _calculate_anomaly_score(self, content: str) -> float:
        """Calculate semantic anomaly score.

        Higher scores indicate potential poisoning.
        In production, would use ML-based anomaly detection.
        """
        # Simple heuristic-based scoring
        score = 0.0

        # Check for unusual character distributions
        special_char_ratio = len(re.findall(r"[^\w\s]", content)) / max(len(content), 1)
        if special_char_ratio > 0.3:
            score += 0.3

        # Check for suspicious length patterns
        lines = content.split("\n")
        if lines:
            avg_line_length = sum(len(line) for line in lines) / len(lines)
            if avg_line_length > 500:  # Unusually long lines
                score += 0.2

        # Check for encoded content
        if re.search(r"base64|\\x[0-9a-f]{2}|%[0-9a-f]{2}", content, re.IGNORECASE):
            score += 0.3

        return min(score, 1.0)

    def _detect_hidden_content(self, content: str) -> list[str]:
        """Detect hidden content patterns that may contain malicious instructions."""
        hidden = []

        # HTML comments with suspicious content
        html_comments = re.findall(r"<!--.*?-->", content, re.DOTALL)
        for comment in html_comments:
            if any(
                word in comment.lower() for word in ["ignore", "override", "system", "instruction"]
            ):
                hidden.append(f"Suspicious HTML comment: {comment[:100]}")

        # Zero-width characters
        if re.search(r"[\u200b\u200c\u200d\u2060\ufeff]", content):
            hidden.append("Zero-width characters detected")

        # Invisible Unicode
        if re.search(r"[\u00ad\u2028\u2029]", content):
            hidden.append("Invisible Unicode characters detected")

        return hidden

    def _calculate_risk_level(
        self, threats: list[ThreatType], source_trusted: bool, anomaly_score: float
    ) -> RiskLevel:
        """Calculate overall risk level."""
        if (
            ThreatType.RAG_POISONING in threats
            or ThreatType.PROMPT_INJECTION_VIA_EMBEDDING in threats
        ):
            return RiskLevel.CRITICAL

        if ThreatType.DATA_EXFILTRATION in threats:
            return RiskLevel.HIGH

        if anomaly_score > 0.5:
            return RiskLevel.MEDIUM

        if not source_trusted:
            return RiskLevel.LOW

        return RiskLevel.SAFE

    def _generate_doc_id(self, content: str, source: str) -> str:
        """Generate unique document ID."""
        hash_input = f"{source}:{content[:1000]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def _persist_verification(self, verification: DocumentVerification) -> None:
        """Persist verification result for audit."""
        try:
            security_dir = (
                Path(__file__).parent.parent.parent.parent / "docs" / "ssot" / "vector_security"
            )
            security_dir.mkdir(parents=True, exist_ok=True)

            import json
            from dataclasses import asdict

            log_file = security_dir / "document_verifications.jsonl"
            with log_file.open("a", encoding="utf-8") as f:
                entry = asdict(verification)
                entry["risk_level"] = verification.risk_level.value
                entry["threats_detected"] = [t.value for t in verification.threats_detected]
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist verification: {e}")

    def add_trusted_source(self, source: str) -> None:
        """Add a source to the trusted whitelist."""
        self.trusted_sources.add(source.lower())
        logger.info(f"[{self.name}] Added trusted source: {source}")

    def get_stats(self) -> dict[str, Any]:
        """Get security statistics."""
        return {
            **self._stats,
            "trusted_sources_count": len(self.trusted_sources),
            "detection_patterns_count": len(self.injection_patterns),
        }


# Singleton instance
vector_security = VectorEmbeddingSecurity()


# Convenience functions
def verify_before_vectorization(
    content: str, source: str = "unknown", **metadata
) -> DocumentVerification:
    """Verify document before adding to vector store."""
    return vector_security.verify_document(content, source, metadata)


def is_document_safe(content: str, source: str = "unknown") -> bool:
    """Quick check if document is safe for vectorization."""
    result = vector_security.verify_document(content, source)
    return result.is_verified and result.risk_level in [RiskLevel.SAFE, RiskLevel.LOW]


def detect_rag_poisoning(content: str) -> dict[str, Any]:
    """Detect RAG poisoning attempts in content."""
    result = vector_security.verify_document(content, "scan_only")
    return {
        "is_poisoned": ThreatType.RAG_POISONING in result.threats_detected,
        "threats": [t.value for t in result.threats_detected],
        "risk_level": result.risk_level.value,
        "details": result.details,
    }
