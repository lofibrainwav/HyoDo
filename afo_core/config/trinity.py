# Trinity Score: 90.0 (Established by Chancellor)
"""Trinity Configuration (Single Source of Truth)

Defines the 5 Pillars of the AFO Kingdom and their weights.
This is the absolute reference for all scoring and governance logic.
"""

from enum import Enum
from typing import Final


class Pillar(str, Enum):
    """The 5 Pillars of AFO Kingdom"""

    TRUTH = "truth"  # 眞: Technical Certainty
    GOODNESS = "goodness"  # 善: Ethical Safety
    BEAUTY = "beauty"  # 美: UX/Aesthetics
    SERENITY = "serenity"  # 孝: Friction Reduction
    ETERNITY = "eternity"  # 永: Persistence/Legacy


class TrinityConfig:
    """Trinity Configuration Constants"""

    # SSOT Weights
    WEIGHTS: Final[dict[Pillar, float]] = {
        Pillar.TRUTH: 0.35,
        Pillar.GOODNESS: 0.35,
        Pillar.BEAUTY: 0.20,
        Pillar.SERENITY: 0.08,
        Pillar.ETERNITY: 0.02,
    }

    @staticmethod
    def validate() -> None:
        """Runtime validation of SSOT integrity"""
        total = sum(TrinityConfig.WEIGHTS.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"SSOT VIOLATION: Trinity Weights must sum to 1.0, got {total:.6f}")

    @classmethod
    def get_weight(cls, pillar: Pillar) -> float:
        """Safe accessor for pillar weights"""
        return cls.WEIGHTS[pillar]


# Runtime validation on import
TrinityConfig.validate()
