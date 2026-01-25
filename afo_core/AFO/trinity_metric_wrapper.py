from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class TrinityMetricResult:
    score: float
    details: dict[str, Any]


@dataclass
class TrinityScore:
    """Trinity 5-Pillar Score (SSOT)."""

    truth: float = 0.5
    goodness: float = 0.5
    beauty: float = 0.5
    serenity: float = 0.5
    eternity: float = 0.5

    def combine(self, other: TrinityScore) -> TrinityScore:
        """Combine two scores (simple average for fallback)."""
        return TrinityScore(
            truth=(self.truth + other.truth) / 2,
            goodness=(self.goodness + other.goodness) / 2,
            beauty=(self.beauty + other.beauty) / 2,
            serenity=(self.serenity + other.serenity) / 2,
            eternity=(self.eternity + other.eternity) / 2,
        )


class TrinityMetricWrapper:
    def __init__(self, metric_fn: Callable[[str, str], float]) -> None:
        self._metric_fn = metric_fn

    def score(self, prompt: str, target: str) -> TrinityMetricResult:
        s = float(self._metric_fn(prompt, target))
        if s < 0.0:
            s = 0.0
        if s > 1.0:
            s = 1.0
        return TrinityMetricResult(score=s, details={})
