from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class JulieConfig:
    enabled: bool = os.getenv("JULIE_ENABLED", "0") == "1"
    mode: str = os.getenv("JULIE_MODE", "prod")


@dataclass(frozen=True)
class TrinityConfig:
    enabled: bool = os.getenv("TRINITY_ENABLED", "1") != "0"


def load_julie_config() -> JulieConfig:
    return JulieConfig()
