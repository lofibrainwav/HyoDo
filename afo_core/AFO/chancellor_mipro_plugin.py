from __future__ import annotations

import os
from dataclasses import dataclass

"""Chancellor MIPRO Plugin for feature flag control.

Provides NO-OP by default, enables MIPRO optimization when flags are set.
This plugin controls MIPRO integration with Chancellor Graph V2.
"""


@dataclass(frozen=True)
class ChancellorMiproPlan:
    """MIPRO plugin execution plan."""

    enabled: bool
    reason: str


def plan() -> ChancellorMiproPlan:
    """Determine MIPRO execution plan based on feature flags.

    Returns:
        Plan indicating whether MIPRO should be enabled
    """
    enabled = (
        os.getenv("AFO_MIPRO_ENABLED", "0") == "1"
        and os.getenv("AFO_MIPRO_CHANCELLOR_ENABLED", "0") == "1"
    )

    if not enabled:
        return ChancellorMiproPlan(
            enabled=False,
            reason=f"AFO_MIPRO_ENABLED!={os.getenv('AFO_MIPRO_ENABLED', '0')} or AFO_MIPRO_CHANCELLOR_ENABLED!={os.getenv('AFO_MIPRO_CHANCELLOR_ENABLED', '0')}",
        )

    return ChancellorMiproPlan(enabled=True, reason="Feature flags enabled")


class ChancellorMiproPlugin:
    """Plugin for controlling MIPRO integration with Chancellor Graph."""

    def plan(self) -> ChancellorMiproPlan:
        """Get current MIPRO execution plan."""
        return plan()


def maybe_apply_mipro(_graph: object) -> bool:
    """Legacy function for backward    enabled: bool
        reason: str


    daph: Graph object (not used in current implementation)

        Returns:
            Always returns False (NO-OP)
    """
    # This is a NO-OP function for backward compatibility
    # Actual MIPRO logic is handled in ChancellorGraph.mipro_node()
    return False
