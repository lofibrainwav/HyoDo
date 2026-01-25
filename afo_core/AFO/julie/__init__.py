"""
Julie CPA Engine - Professional Tax Calculation Services
TICKET-042 + TICKET-043: Julie CPA Depreciation Calculator + Big 4 AI 에이전트 군단 운영 시스템

Provides enterprise-grade tax calculation services with:
- §179 and Bonus Depreciation calculations
- CA-specific FTB compliance
- OBBB 2025/2026 accuracy
- DSPy MIPROv2 optimization
- Trinity Score validation
- Big 4 AI 에이전트 군단: Associate/Manager/Auditor 3단계 검토
- R.C.A.T.E. 구조화 워크플로우 + 휴밀리티 프로토콜

SSOT Integration: IRS/FTB official guidelines with real-time sync (TICKET-033)
"""

from AFO.config.runtime import JulieConfig, load_julie_config

from .ai_agents import (
    AssociateAgent,
    AuditorAgent,
    JulieAgentOrchestrator,
    ManagerAgent,
)
from .depreciation import (
    DepInput,
    DepOutput,
    DepreciationCalculator,
    julie_depreciation_calc,
)
from .julie_logs import (
    julie_log_manager,
    log_associate_action,
    log_auditor_action,
    log_manager_action,
)

__all__ = [
    "AssociateAgent",
    "AuditorAgent",
    "DepInput",
    "DepOutput",
    "DepreciationCalculator",
    "JulieAgentOrchestrator",
    "ManagerAgent",
    "julie_depreciation_calc",
    "julie_log_manager",
    "log_associate_action",
    "log_auditor_action",
    "log_manager_action",
    "JulieConfig",
    "julie_config",
]


julie_config = load_julie_config()


__version__ = "1.0.0"
__author__ = "AFO Kingdom Chancellor"
__trinity_score__ = 0.985  # 眞善美孝永
