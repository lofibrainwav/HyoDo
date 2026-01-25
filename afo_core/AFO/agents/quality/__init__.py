"""Quality Inspection Agents Package.

코드 품질을 지속적으로 감시하고 개선하는 에이전트 군단.
Ruff, MonkeyType, 구문 분석 등을 전문적으로 수행함.
"""

from __future__ import annotations

from .ruff import FastRuffAgent
from .scout import QualityScoutAgent

# 편의를 위해 인스턴스 미리 생성
quality_scout_agent = QualityScoutAgent()
fast_ruff_agent = FastRuffAgent()

FAST_CHECK_AGENTS = [
    fast_ruff_agent,
]

__all__ = [
    "QualityScoutAgent",
    "FastRuffAgent",
    "quality_scout_agent",
    "fast_ruff_agent",
    "FAST_CHECK_AGENTS",
]
