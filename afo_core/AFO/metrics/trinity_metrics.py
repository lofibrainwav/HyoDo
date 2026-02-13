"""Trinity Score Metrics Module.

Provides Trinity Score collection and Prometheus metrics integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..prometheus import (
    record_trinity_check,
    update_trinity_score,
    update_trinity_score_total,
)

logger = logging.getLogger(__name__)


@dataclass
class PillarScore:
    """Individual pillar score."""

    name: str
    score: float
    weight: float


@dataclass
class TrinityScoreResult:
    """Complete Trinity Score result."""

    truth: float
    goodness: float
    beauty: float
    serenity: float
    eternity: float
    total: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "眞": self.truth,
            "善": self.goodness,
            "美": self.beauty,
            "孝": self.serenity,
            "永": self.eternity,
            "total": self.total,
        }

    @property
    def pillars(self) -> list[PillarScore]:
        return [
            PillarScore("眞", self.truth, 0.35),
            PillarScore("善", self.goodness, 0.35),
            PillarScore("美", self.beauty, 0.20),
            PillarScore("孝", self.serenity, 0.08),
            PillarScore("永", self.eternity, 0.02),
        ]


class TrinityMetricsCollector:
    """Collects and records Trinity Score metrics."""

    def __init__(self) -> None:
        self._current_scores: dict[str, float] = {}
        logger.info("TrinityMetricsCollector initialized")

    def record_score(self, result: TrinityScoreResult) -> None:
        """Record a complete Trinity Score result.

        Args:
            result: Trinity score calculation result
        """
        for pillar in result.pillars:
            update_trinity_score(pillar.name, pillar.score)
            self._current_scores[pillar.name] = pillar.score

        update_trinity_score_total(result.total)
        self._current_scores["total"] = result.total

        logger.info(f"Trinity Score recorded: total={result.total:.1f}")

    def record_check(self, passed: bool) -> None:
        """Record a Trinity check result.

        Args:
            passed: Whether the check passed
        """
        result = "pass" if passed else "fail"
        record_trinity_check(result)
        logger.debug(f"Trinity check recorded: {result}")

    def get_current_scores(self) -> dict[str, float]:
        """Get current scores."""
        return self._current_scores.copy()


# Convenience functions
def calculate_trinity_score(
    truth: float,
    goodness: float,
    beauty: float,
    serenity: float,
    eternity: float,
) -> TrinityScoreResult:
    """Calculate Trinity Score with weights.

    Weights: 眞=35%, 善=35%, 美=20%, 孝=8%, 永=2%
    """
    total = truth * 0.35 + goodness * 0.35 + beauty * 0.20 + serenity * 0.08 + eternity * 0.02

    return TrinityScoreResult(
        truth=truth,
        goodness=goodness,
        beauty=beauty,
        serenity=serenity,
        eternity=eternity,
        total=total,
    )


__all__ = [
    "TrinityScoreResult",
    "PillarScore",
    "TrinityMetricsCollector",
    "calculate_trinity_score",
]
