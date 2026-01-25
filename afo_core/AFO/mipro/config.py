from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

"""MIPROv2 Configuration with type safety."""


@dataclass(frozen=True)
class MiproConfig:
    """Configuration for MIPROv2 optimization."""

    auto: Literal["light", "medium", "heavy"] = "light"
    max_bootstrapped_demos: int = 4
    max_labeled_demos: int = 4
    num_trials: int | None = None
    batch_size: int = 5
