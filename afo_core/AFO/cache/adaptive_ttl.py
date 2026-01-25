# Trinity Score: 91.0 (美 Beauty - Adaptive Perception)
"""
Adaptive TTL Strategy - Phase 82

Dynamic TTL calculation based on Trinity Score and system entropy.
High confidence (Trinity ≥ 95) → longer cache TTL (1.5x)
Degraded state (Trinity < 80) → shorter TTL (0.5x) for faster refresh.

Integration with TelemetryBridge (Phase 80) for real-time metrics.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SystemState(str, Enum):
    """System health states affecting TTL."""

    EXCELLENT = "excellent"  # Trinity >= 95
    HEALTHY = "healthy"  # Trinity 90-94
    NORMAL = "normal"  # Trinity 80-89
    DEGRADED = "degraded"  # Trinity 70-79
    CRITICAL = "critical"  # Trinity < 70


@dataclass
class TTLConfig:
    """Configuration for adaptive TTL calculation."""

    # Base TTL values (seconds)
    ai_response_base: int = 1800  # 30 minutes
    db_query_base: int = 300  # 5 minutes
    chart_data_base: int = 600  # 10 minutes
    irs_data_base: int = 3600  # 1 hour
    user_session_base: int = 7200  # 2 hours

    # Multipliers by system state
    excellent_multiplier: float = 1.5
    healthy_multiplier: float = 1.2
    normal_multiplier: float = 1.0
    degraded_multiplier: float = 0.7
    critical_multiplier: float = 0.5

    # Entropy adjustment (higher entropy = shorter TTL)
    entropy_impact: float = 0.3  # How much entropy affects TTL (0-1)

    # Minimum and maximum TTL bounds
    min_ttl: int = 30  # 30 seconds minimum
    max_ttl: int = 86400  # 24 hours maximum


@dataclass
class TTLDecision:
    """Result of TTL calculation."""

    base_ttl: int
    final_ttl: int
    multiplier: float
    system_state: SystemState
    trinity_score: float
    entropy: float
    reasoning: str
    calculated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "base_ttl": self.base_ttl,
            "final_ttl": self.final_ttl,
            "multiplier": round(self.multiplier, 3),
            "system_state": self.system_state.value,
            "trinity_score": round(self.trinity_score, 2),
            "entropy": round(self.entropy, 4),
            "reasoning": self.reasoning,
            "calculated_at": self.calculated_at.isoformat(),
        }


class AdaptiveTTLStrategy:
    """
    Adaptive TTL calculation based on system health metrics.

    Uses Trinity Score and entropy from TelemetryBridge to
    dynamically adjust cache TTL for optimal performance.
    """

    def __init__(self, config: TTLConfig | None = None) -> None:
        self.config = config or TTLConfig()
        self._last_trinity_score: float = 100.0
        self._last_entropy: float = 0.0
        self._history: list[TTLDecision] = []

    def get_system_state(self, trinity_score: float) -> SystemState:
        """Determine system state from Trinity Score."""
        if trinity_score >= 95:
            return SystemState.EXCELLENT
        if trinity_score >= 90:
            return SystemState.HEALTHY
        if trinity_score >= 80:
            return SystemState.NORMAL
        if trinity_score >= 70:
            return SystemState.DEGRADED
        return SystemState.CRITICAL

    def get_state_multiplier(self, state: SystemState) -> float:
        """Get TTL multiplier for system state."""
        multipliers = {
            SystemState.EXCELLENT: self.config.excellent_multiplier,
            SystemState.HEALTHY: self.config.healthy_multiplier,
            SystemState.NORMAL: self.config.normal_multiplier,
            SystemState.DEGRADED: self.config.degraded_multiplier,
            SystemState.CRITICAL: self.config.critical_multiplier,
        }
        return multipliers.get(state, 1.0)

    def calculate_ttl(
        self,
        base_ttl: int,
        trinity_score: float | None = None,
        entropy: float | None = None,
        cache_type: str = "default",
    ) -> TTLDecision:
        """
        Calculate adaptive TTL based on system metrics.

        Args:
            base_ttl: Base TTL value in seconds
            trinity_score: Current Trinity Score (0-100)
            entropy: Current system entropy (0-1)
            cache_type: Type of cached data for logging

        Returns:
            TTLDecision with calculated values
        """
        # Use last known values if not provided
        trinity_score = trinity_score if trinity_score is not None else self._last_trinity_score
        entropy = entropy if entropy is not None else self._last_entropy

        # Update last known values
        self._last_trinity_score = trinity_score
        self._last_entropy = entropy

        # Determine system state
        state = self.get_system_state(trinity_score)

        # Get base multiplier from state
        state_multiplier = self.get_state_multiplier(state)

        # Apply entropy adjustment
        # Higher entropy = shorter TTL (multiply by 1 - entropy * impact)
        entropy_adjustment = 1.0 - (entropy * self.config.entropy_impact)
        entropy_adjustment = max(0.5, min(1.0, entropy_adjustment))

        # Calculate final multiplier
        final_multiplier = state_multiplier * entropy_adjustment

        # Calculate final TTL
        final_ttl = int(base_ttl * final_multiplier)

        # Apply bounds
        final_ttl = max(self.config.min_ttl, min(self.config.max_ttl, final_ttl))

        # Build reasoning
        reasoning = self._build_reasoning(
            state, state_multiplier, entropy, entropy_adjustment, cache_type
        )

        decision = TTLDecision(
            base_ttl=base_ttl,
            final_ttl=final_ttl,
            multiplier=final_multiplier,
            system_state=state,
            trinity_score=trinity_score,
            entropy=entropy,
            reasoning=reasoning,
        )

        # Store in history
        self._history.append(decision)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        logger.debug(
            f"📊 Adaptive TTL [{cache_type}]: {base_ttl}s → {final_ttl}s "
            f"(×{final_multiplier:.2f}, state={state.value})"
        )

        return decision

    def _build_reasoning(
        self,
        state: SystemState,
        state_mult: float,
        entropy: float,
        entropy_adj: float,
        cache_type: str,
    ) -> str:
        """Build human-readable reasoning for TTL decision."""
        parts = [f"Cache type: {cache_type}"]

        if state == SystemState.EXCELLENT:
            parts.append(f"System excellent (×{state_mult}): extending TTL")
        elif state == SystemState.HEALTHY:
            parts.append(f"System healthy (×{state_mult}): slightly extending TTL")
        elif state == SystemState.NORMAL:
            parts.append(f"System normal (×{state_mult}): using base TTL")
        elif state == SystemState.DEGRADED:
            parts.append(f"System degraded (×{state_mult}): reducing TTL for freshness")
        else:
            parts.append(f"System critical (×{state_mult}): minimizing TTL")

        if entropy > 0.3:
            parts.append(
                f"High entropy ({entropy:.2f}): reducing TTL by {(1 - entropy_adj) * 100:.0f}%"
            )
        elif entropy > 0.1:
            parts.append(f"Moderate entropy ({entropy:.2f}): slight TTL reduction")

        return "; ".join(parts)

    def get_ai_response_ttl(
        self,
        trinity_score: float | None = None,
        entropy: float | None = None,
    ) -> TTLDecision:
        """Get adaptive TTL for AI response caching."""
        return self.calculate_ttl(
            self.config.ai_response_base,
            trinity_score,
            entropy,
            "ai_response",
        )

    def get_db_query_ttl(
        self,
        trinity_score: float | None = None,
        entropy: float | None = None,
    ) -> TTLDecision:
        """Get adaptive TTL for database query caching."""
        return self.calculate_ttl(
            self.config.db_query_base,
            trinity_score,
            entropy,
            "db_query",
        )

    def get_irs_data_ttl(
        self,
        trinity_score: float | None = None,
        entropy: float | None = None,
    ) -> TTLDecision:
        """Get adaptive TTL for IRS data caching."""
        return self.calculate_ttl(
            self.config.irs_data_base,
            trinity_score,
            entropy,
            "irs_data",
        )

    def get_chart_data_ttl(
        self,
        trinity_score: float | None = None,
        entropy: float | None = None,
    ) -> TTLDecision:
        """Get adaptive TTL for chart/visualization data."""
        return self.calculate_ttl(
            self.config.chart_data_base,
            trinity_score,
            entropy,
            "chart_data",
        )

    def update_metrics(
        self,
        trinity_score: float,
        entropy: float,
    ) -> None:
        """Update cached metrics from TelemetryBridge."""
        self._last_trinity_score = trinity_score
        self._last_entropy = entropy

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent TTL decision history."""
        return [d.to_dict() for d in self._history[-limit:]]

    def get_stats(self) -> dict[str, Any]:
        """Get TTL strategy statistics."""
        if not self._history:
            return {
                "decisions_made": 0,
                "avg_multiplier": 1.0,
                "current_trinity_score": self._last_trinity_score,
                "current_entropy": self._last_entropy,
            }

        multipliers = [d.multiplier for d in self._history]
        states = [d.system_state.value for d in self._history]

        return {
            "decisions_made": len(self._history),
            "avg_multiplier": round(sum(multipliers) / len(multipliers), 3),
            "min_multiplier": round(min(multipliers), 3),
            "max_multiplier": round(max(multipliers), 3),
            "current_trinity_score": round(self._last_trinity_score, 2),
            "current_entropy": round(self._last_entropy, 4),
            "state_distribution": {state: states.count(state) for state in set(states)},
        }


# Global singleton instance
_adaptive_ttl: AdaptiveTTLStrategy | None = None


def get_adaptive_ttl_strategy() -> AdaptiveTTLStrategy:
    """Get or create the global adaptive TTL strategy instance."""
    global _adaptive_ttl
    if _adaptive_ttl is None:
        _adaptive_ttl = AdaptiveTTLStrategy()
    return _adaptive_ttl


def calculate_adaptive_ttl(
    base_ttl: int,
    trinity_score: float | None = None,
    entropy: float | None = None,
) -> int:
    """Convenience function to calculate adaptive TTL."""
    strategy = get_adaptive_ttl_strategy()
    decision = strategy.calculate_ttl(base_ttl, trinity_score, entropy)
    return decision.final_ttl


async def sync_with_telemetry() -> None:
    """Sync TTL strategy with TelemetryBridge metrics."""
    try:
        from infrastructure.telemetry_bridge import get_telemetry_bridge

        bridge = get_telemetry_bridge()
        state = bridge.get_current_state()

        strategy = get_adaptive_ttl_strategy()
        strategy.update_metrics(
            trinity_score=state.get("trinity_score", 100.0),
            entropy=state.get("entropy", 0.0),
        )

        logger.debug("📊 Adaptive TTL synced with TelemetryBridge")
    except ImportError:
        logger.debug("TelemetryBridge not available, using cached metrics")
    except Exception as e:
        logger.warning(f"Failed to sync with TelemetryBridge: {e}")
