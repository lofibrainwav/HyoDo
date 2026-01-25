"""
Julie CPA Agent Implementations

이 파일은 하위 호환성을 위한 래퍼입니다.
실제 구현은 AFO.julie_cpa.agents 모듈로 이동되었습니다.

Migration Guide:
    # Before
    from AFO.julie_cpa_agents import JulieAssociateAgent

    # After (recommended)
    from AFO.julie_cpa.agents import JulieAssociateAgent

Three-tier agent architecture for tax analysis, compliance, and auditing
integrated with Chancellor Graph and Trinity Score evaluation.
"""

from AFO.julie_cpa.agents import (
    JulieAssociateAgent,
    JulieAuditorAgent,
    JulieManagerAgent,
    process_julie_cpa_workflow,
)

__all__ = [
    "JulieAssociateAgent",
    "JulieManagerAgent",
    "JulieAuditorAgent",
    "process_julie_cpa_workflow",
]
