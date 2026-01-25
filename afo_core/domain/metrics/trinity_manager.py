# Trinity Score: 90.0 (Established by Chancellor)
from typing import Any

from AFO.trinity import TrinityInputs, TrinityMetrics


class TrinityManager:
    """
    [TrinityManager]
    The Keeper of the Kingdom's Balance.
    Manages the dynamic state of Trinity Scores (Base + Delta).

    Architecture (PDF Page 3):
    - Base Scores: Initialize at 100%.
    - Delta Logic: Apply real-time +/- based on actions.
    - Clamping: Ensure 0 <= Score <= 100.
    """

    # Trigger Definitions (SSOT Goodness)
    TRIGGERS = {
        "VERIFICATION_SUCCESS": {"truth": 5.0, "goodness": 2.0},
        "VERIFICATION_FAIL": {"truth": -10.0, "risk": 5.0},  # Risk increases
        "DRY_RUN_ACTIVE": {"goodness": 10.0, "risk": -5.0},
        "AUTO_RUN_ACTION": {"filial_serenity": 10.0, "beauty": 5.0},
        "MANUAL_INTERVENTION": {"filial_serenity": -5.0},  # Friction
        "ELEGANT_RESPONSE": {"beauty": 8.0},
        "PERSISTENCE_SAVE": {"eternity": 5.0},  # Checking point
    }

    def __init__(self) -> None:
        # Initial State: Perfect Harmony
        self.base_inputs = TrinityInputs(
            truth=1.0, goodness=1.0, beauty=1.0, filial_serenity=1.0
        )  # 100%
        self.eternity = 1.0

        # Global Accumulators
        self.deltas: dict[str, float] = {
            "truth": 0.0,
            "goodness": 0.0,
            "beauty": 0.0,
            "filial_serenity": 0.0,
            "eternity": 0.0,
        }

        # Agent-Specific Accumulators (Phase 69)
        self.agent_deltas: dict[str, dict[str, float]] = {
            "jang_yeong_sil": {
                "truth": 0.0,
                "goodness": 0.0,
                "beauty": 0.0,
                "filial_serenity": 0.0,
                "eternity": 0.0,
            },
            "yi_sun_sin": {
                "truth": 0.0,
                "goodness": 0.0,
                "beauty": 0.0,
                "filial_serenity": 0.0,
                "eternity": 0.0,
            },
            "shin_saimdang": {
                "truth": 0.0,
                "goodness": 0.0,
                "beauty": 0.0,
                "filial_serenity": 0.0,
                "eternity": 0.0,
            },
        }

    def apply_trigger(
        self, trigger_name: str, agent_name: str | None = None
    ) -> TrinityMetrics:
        """Apply a predefined trigger event to modify scores."""
        delta_map = self.TRIGGERS.get(trigger_name, {})

        # Apply to Global
        self._apply_delta_map(self.deltas, delta_map)

        # Apply to Specific Agent if specified
        if agent_name and agent_name in self.agent_deltas:
            self._apply_delta_map(self.agent_deltas[agent_name], delta_map)
            return self.get_agent_metrics(agent_name)

        return self.get_current_metrics()

    def _apply_delta_map(
        self, target_deltas: dict[str, float], delta_map: dict[str, float]
    ) -> None:
        """Helper to apply deltas to a target dictionary."""
        for key, value in delta_map.items():
            if key == "risk":
                # Risk reduces Goodness
                target_deltas["goodness"] -= value
            elif key in target_deltas:
                target_deltas[key] += value

    def get_current_metrics(self) -> TrinityMetrics:
        """Calculate Global System metrics."""
        return self._calculate_metrics(self.deltas)

    def get_agent_metrics(self, agent_name: str) -> TrinityMetrics:
        """Calculate Agent-Specific metrics."""
        if agent_name not in self.agent_deltas:
            return self.get_current_metrics()  # Fallback to global
        return self._calculate_metrics(self.agent_deltas[agent_name])

    def _calculate_metrics(self, deltas: dict[str, float]) -> TrinityMetrics:
        """Internal calculation logic."""
        new_inputs = TrinityInputs(
            truth=self.base_inputs.truth + (deltas["truth"] / 100.0),
            goodness=self.base_inputs.goodness + (deltas["goodness"] / 100.0),
            beauty=self.base_inputs.beauty + (deltas["beauty"] / 100.0),
            filial_serenity=self.base_inputs.filial_serenity
            + (deltas["filial_serenity"] / 100.0),
        )
        new_eternity = self.eternity + (deltas["eternity"] / 100.0)
        return TrinityMetrics.from_inputs(new_inputs, eternity=new_eternity)

    def get_all_metrics(self) -> dict[str, Any]:
        """Get Global + All Agents metrics (API View)."""
        return {
            "global": self.get_current_metrics().to_dict(),
            "agents": {
                name: self.get_agent_metrics(name).to_dict()
                for name in self.agent_deltas.keys()
            },
        }


# Singleton Instance
trinity_manager = TrinityManager()
