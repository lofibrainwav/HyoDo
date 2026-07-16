"""HyoDo Agents Package - Standalone AI Code Quality Agents.

This package provides autonomous agents for code quality automation
without external dependencies like Redis or AFO Kingdom.

Core Components:
- InMemoryQueue: Redis replacement for standalone operation
- QualityScoutAgent: Fast code quality scanning
- FastRuffAgent: Ruff linting integration
- 4 Scholars: , , , 
- 3 Strategists: , , 

Usage:
    from agents import InMemoryQueue, QualityScoutAgent
    from agents.jeong_yak_yong_core import jeong_yak_yong_core
"""

from agents.ci_cd_agents import InMemoryQueue
from agents.quality import (
    FAST_CHECK_AGENTS,
    FastRuffAgent,
    QualityLevel,
    QualityResult,
    QualityScoutAgent,
    fast_ruff_agent,
    quality_scout_agent,
)

__all__ = [
    # Queue
    "InMemoryQueue",
    # Quality
    "QualityScoutAgent",
    "FastRuffAgent",
    "QualityLevel",
    "QualityResult",
    "quality_scout_agent",
    "fast_ruff_agent",
    "FAST_CHECK_AGENTS",
]

__version__ = "3.0.0"
