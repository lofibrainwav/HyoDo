from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TuningCandidate:
    prompt: str
    score: float


class BayesianTuner:
    def select_best(self, candidates: list[TuningCandidate]) -> TuningCandidate | None:
        if not candidates:
            return None
        return max(candidates, key=lambda c: c.score)
