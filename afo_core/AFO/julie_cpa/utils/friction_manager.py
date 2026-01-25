# Trinity Score: 90.0 (Established by Chancellor)
import logging
from typing import Any

from AFO.julie_cpa.config import julie_config

# [The Prince #30: Cruelty Well Used (Kill processes)]
logger = logging.getLogger("AFO.JulieCPA.FrictionManager")


class FrictionManager:
    """[On War #34 & #35]
    Manages Friction (Difficulty) and Fog of War (Uncertainty).
    If friction is too high, it blocks execution to protect Serenity (孝).
    """

    MAX_FRICTION_THRESHOLD = julie_config.MAX_FRICTION_THRESHOLD

    @staticmethod
    def assess_friction(data: dict[str, Any]) -> float:
        """Calculates Friction Score based on data ambiguity and completeness."""
        score = 0.0

        # 1. Missing Data (fog)
        if not data:
            score += 50.0  # Critical Fog
            return score

        # 2. Type Uncertainty
        for _key, value in data.items():
            if value is None:
                score += 10.0  # Missing field
            elif isinstance(value, str) and len(value) == 0:
                score += 5.0  # Empty string

        # 3. Complexity (Nested structures)
        score += len(str(data)) * 0.01

        return score

    @staticmethod
    def check_fog_of_war(friction_score: float) -> bool:
        """[On War #34: Fog of War]
        Returns True if the situation is too foggy (unsafe) to proceed.
        """
        is_foggy = friction_score > FrictionManager.MAX_FRICTION_THRESHOLD
        if is_foggy:
            logger.warning(
                f"🌁 Fog of War Detected! Friction: {friction_score} > {FrictionManager.MAX_FRICTION_THRESHOLD}"
            )
            logger.info("🛑 Operation Blocked for Reconnaissance.")

        return is_foggy
