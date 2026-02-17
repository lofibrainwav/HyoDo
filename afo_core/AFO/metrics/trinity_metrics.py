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
        # HYOGOOK V5 weights (Phase 127+): 仁25% 眞22% 善18% 忠15% 美15%
        return [
            PillarScore("眞", self.truth, 0.22),
            PillarScore("善", self.goodness, 0.18),
            PillarScore("美", self.beauty, 0.15),
            PillarScore("仁", self.serenity, 0.25),
            PillarScore("忠", self.eternity, 0.15),
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
    use_hyogook_v5: bool = True,
) -> TrinityScoreResult:
    """Calculate Trinity Score with Phase-aware weights.

    HYOGOOK V5 (Phase 127+): F = (T+G+In+B+C) + ⁵√(T×G×In×B×C)
    Legacy (Phase ≤126): F = T×0.18 + G×0.18 + B×0.12 + S×0.40 + E×0.12
    """
    import math

    if use_hyogook_v5:
        # HYOGOOK V5 Weights: 仁25% 眞22% 善18% 忠15% 美15%
        weights = {
            "truth": 0.22,
            "goodness": 0.18,
            "beauty": 0.15,
            "benevolence": 0.25,
            "loyalty": 0.15,
        }
        weighted_sum = (
            truth * weights["truth"]
            + goodness * weights["goodness"]
            + beauty * weights["beauty"]
            + serenity * weights["benevolence"]
            + eternity * weights["loyalty"]
        )
        geometric_mean = math.pow(truth * goodness * serenity * beauty * eternity, 1 / 5)
        total = weighted_sum + geometric_mean
    else:
        # Legacy WEIGHTED_V1: 眞18% 善18% 美12% 孝40% 永12%
        total = truth * 0.18 + goodness * 0.18 + beauty * 0.12 + serenity * 0.40 + eternity * 0.12

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
