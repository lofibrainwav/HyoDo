"""Trinity Score Sharing System

모듈화된 Trinity Score 공유 및 협업 최적화 시스템.

TICKET-109: L1 Domain Layer - Trinity Score 공유 모델 정의
SSOT: TRINITY_OS_PERSONAS.yaml, domain/metrics/trinity_ssot.py
"""

from .collaboration_analysis import (
    analyze_collaboration_context,
    analyze_score_distribution,
    assess_convergence_status,
    calculate_adjustment_confidence,
    calculate_collaboration_impact,
    calculate_collaboration_intensity,
    calculate_collaborative_adjustment,
    calculate_variance,
    check_convergence,
    generate_adjustment_reason,
)
from .domain_models import (
    AgentScoreEntry,
    # Enums
    AgentType,
    BalanceStatus,
    # Events & Metrics
    CollaborationFeedback,
    CollaborationMetricsSnapshot,
    CollaborationQuality,
    OptimizationPolicy,
    OptimizationStrategy,
    # Core Models
    PillarScores,
    # Policies
    SharingPolicy,
    TrinityScorePool,
    # Contract
    TrinityScoreSharingContract,
    TrinityScoreUpdateEvent,
)
from .feedback_manager import FeedbackLoopManager
from .models import CollaborationMetrics, TrinityScoreUpdate
from .optimizer import TrinityScoreOptimizer
from .sharing_system import TrinityScoreSharingSystem

__all__ = [
    # Domain Enums (TICKET-109)
    "AgentType",
    "BalanceStatus",
    "CollaborationQuality",
    "OptimizationStrategy",
    # Domain Models (TICKET-109)
    "PillarScores",
    "AgentScoreEntry",
    "TrinityScorePool",
    # Policies (TICKET-109)
    "SharingPolicy",
    "OptimizationPolicy",
    # Events & Metrics (TICKET-109)
    "CollaborationFeedback",
    "TrinityScoreUpdateEvent",
    "CollaborationMetricsSnapshot",
    # Contract (TICKET-109)
    "TrinityScoreSharingContract",
    # Legacy Models
    "TrinityScoreUpdate",
    "CollaborationMetrics",
    # Core Classes
    "TrinityScoreSharingSystem",
    "TrinityScoreOptimizer",
    "FeedbackLoopManager",
    # Collaboration Analysis (extracted from sharing_system_full.py)
    "calculate_variance",
    "analyze_score_distribution",
    "calculate_collaboration_intensity",
    "calculate_collaboration_impact",
    "analyze_collaboration_context",
    "calculate_collaborative_adjustment",
    "generate_adjustment_reason",
    "calculate_adjustment_confidence",
    "assess_convergence_status",
    "check_convergence",
]
