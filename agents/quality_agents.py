"""Quality Agents - Refactored Wrapper.

Original code moved to: AFO/agents/quality/
"""

from .quality import (
    FAST_CHECK_AGENTS,
    FastRuffAgent,
    QualityScoutAgent,
    fast_ruff_agent,
    quality_scout_agent,
)


def initialize_quality_agents() -> None:
    pass  # Wrapper implementation


__all__ = [
    "QualityScoutAgent",
    "FastRuffAgent",
    "quality_scout_agent",
    "fast_ruff_agent",
    "FAST_CHECK_AGENTS",
    "initialize_quality_agents",
]
