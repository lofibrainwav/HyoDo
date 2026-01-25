from __future__ import annotations

import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from AFO.bayesian_tuner import BayesianTuner, TuningCandidate

if TYPE_CHECKING:
    from AFO.trinity_metric_wrapper import TrinityMetricResult, TrinityMetricWrapper


@dataclass(frozen=True)
class MiproOptimizeResult:
    best_prompt: str
    best_score: float


class MiproOptimizer:
    def __init__(self, metric: TrinityMetricWrapper) -> None:
        self._metric = metric
        self._tuner = BayesianTuner()

    def optimize(self, base_prompts: list[str], target: str) -> MiproOptimizeResult:
        if os.getenv("AFO_MIPRO_ENABLED") != "1":
            if base_prompts:
                return MiproOptimizeResult(best_prompt=base_prompts[0], best_score=0.0)
            return MiproOptimizeResult(best_prompt="", best_score=0.0)

        scored: list[TuningCandidate] = []
        for p in base_prompts:
            r: TrinityMetricResult = self._metric.score(p, target)
            scored.append(TuningCandidate(prompt=p, score=r.score))

        best = self._tuner.select_best(scored)
        if best is None:
            return MiproOptimizeResult(best_prompt="", best_score=0.0)
        return MiproOptimizeResult(best_prompt=best.prompt, best_score=float(best.score))
