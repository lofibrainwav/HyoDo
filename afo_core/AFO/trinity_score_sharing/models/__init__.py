"""Trinity Score Sharing Domain Models Package.

L1 Domain Layer - 핵심 도메인 모델과 계약 정의.
眞善美孝永 5기둥 철학을 코드로 구조화함.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .enums import (
    AgentType,
    BalanceStatus,
    ChangeType,
    CollaborationQuality,
    ImpactLevel,
    OptimizationStrategy,
    ValidationStatus,
)
from .irs_models import ChangeImpactAnalysis, IRSChangeLog, RegulationMetadata
from .trinity_models import (
    THRESHOLD_AUTO_RUN_RISK,
    THRESHOLD_AUTO_RUN_SCORE,
    WEIGHT_BEAUTY,
    WEIGHT_ETERNITY,
    WEIGHT_GOODNESS,
    WEIGHT_SERENITY,
    WEIGHT_TRUTH,
    WEIGHTS,
    AgentScoreEntry,
    CollaborationFeedback,
    CollaborationMetricsSnapshot,
    OptimizationPolicy,
    PillarScores,
    SharingPolicy,
    TrinityScorePool,
    TrinityScoreSharingContract,
    TrinityScoreUpdateEvent,
)


@dataclass
class TrinityScoreUpdate:
    """Trinity Score 업데이트 이벤트"""

    agent_type: str
    session_id: str
    previous_score: float
    new_score: float
    change_reason: str
    contributing_factors: dict[str, float]
    timestamp: str
    collaboration_impact: float = 0.0


@dataclass
class CollaborationMetrics:
    """협업 메트릭 데이터"""

    session_id: str
    agent_contributions: dict[str, int]
    consensus_level: float
    efficiency_gain: float
    trinity_score_variance: float
    collaboration_quality: str
    timestamp: str


__all__ = [
    "AgentType",
    "ChangeType",
    "ImpactLevel",
    "ValidationStatus",
    "BalanceStatus",
    "OptimizationStrategy",
    "CollaborationQuality",
    "PillarScores",
    "AgentScoreEntry",
    "WEIGHTS",
    "WEIGHT_TRUTH",
    "WEIGHT_GOODNESS",
    "WEIGHT_BEAUTY",
    "WEIGHT_SERENITY",
    "WEIGHT_ETERNITY",
    "THRESHOLD_AUTO_RUN_SCORE",
    "THRESHOLD_AUTO_RUN_RISK",
    "RegulationMetadata",
    "ChangeImpactAnalysis",
    "IRSChangeLog",
    "CollaborationFeedback",
    "CollaborationMetricsSnapshot",
    "OptimizationPolicy",
    "SharingPolicy",
    "TrinityScorePool",
    "TrinityScoreSharingContract",
    "TrinityScoreUpdateEvent",
    "TrinityScoreUpdate",
    "CollaborationMetrics",
]
