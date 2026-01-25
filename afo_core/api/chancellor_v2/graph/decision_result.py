from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

"""Decision Result - Chancellor Graph V2 Decision Structure (SSOT).

Provides standardized decision result structure for Chancellor Graph V2.
Ensures transparency between ASK_COMMANDER/AUTO_RUN/ERROR modes.
"""


@dataclass
class DecisionResult:
    """Standardized decision result for Chancellor Graph operations.

    SSOT Contract: Never return bare boolean. Always provide structured reasoning.
    """

    mode: str  # "AUTO_RUN" | "ASK_COMMANDER" | "ERROR"
    trinity_score: float  # 0-100
    risk_score: float  # 0-100
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "truth": 0.35,
            "goodness": 0.35,
            "beauty": 0.20,
            "serenity": 0.08,
            "eternity": 0.02,
        }
    )
    pillar_scores: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)  # Why this decision?
    errors: list[dict[str, Any]] = field(default_factory=list)  # What went wrong?

    @classmethod
    def auto_run(
        cls,
        trinity_score: float,
        risk_score: float,
        pillar_scores: dict[str, float],
        reasons: list[str] = None,
    ) -> DecisionResult:
        """Create AUTO_RUN decision result."""
        return cls(
            mode="AUTO_RUN",
            trinity_score=trinity_score,
            risk_score=risk_score,
            pillar_scores=pillar_scores,
            reasons=reasons or ["Trinity Score ≥ 90", "Risk Score ≤ 10"],
        )

    @classmethod
    def ask_commander(
        cls,
        trinity_score: float,
        risk_score: float,
        pillar_scores: dict[str, float],
        reasons: list[str] = None,
    ) -> DecisionResult:
        """Create ASK_COMMANDER decision result."""
        reasons = reasons or []
        if trinity_score < 90:
            reasons.append(f"Trinity Score {trinity_score:.1f} < 90")
        if risk_score > 10:
            reasons.append(f"Risk Score {risk_score:.1f} > 10")

        return cls(
            mode="ASK_COMMANDER",
            trinity_score=trinity_score,
            risk_score=risk_score,
            pillar_scores=pillar_scores,
            reasons=reasons,
        )

    @classmethod
    def error(
        cls,
        error_type: str,
        message: str,
        where: str = "",
        trinity_score: float = 0.0,
        risk_score: float = 0.0,
    ) -> DecisionResult:
        """Create ERROR decision result."""
        return cls(
            mode="ERROR",
            trinity_score=trinity_score,
            risk_score=risk_score,
            errors=[{"type": error_type, "message": message, "where": where}],
            reasons=[f"Error: {message}"],
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_legacy_bool(self) -> bool:
        """Convert to legacy boolean for backward compatibility.

        WARNING: This loses all reasoning information.
        Use to_dict() instead for proper decision handling.
        """
        return self.mode == "AUTO_RUN"

    def __str__(self) -> str:
        return f"DecisionResult(mode={self.mode}, trinity={self.trinity_score:.1f}, risk={self.risk_score:.1f})"
