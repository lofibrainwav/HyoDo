"""Trinity Sharing Enums.

AFO Kingdom 에이전트 유형, 변경 유형, 영향도 수준 등 핵심 열거형 정의.
"""

from __future__ import annotations

from enum import Enum


class AgentType(str, Enum):
    """AFO Kingdom Agent 타입 정의."""

    ASSOCIATE = "associate"
    MANAGER = "manager"
    AUDITOR = "auditor"
    ZHUGE_LIANG = "jang_yeong_sil"
    SIMA_YI = "sima_yi"
    ZHOU_YU = "zhou_yu"
    BANGTONG = "bangtong"
    JARYONG = "jaryong"
    YUKSON = "yukson"
    YEONGDEOK = "yeongdeok"
    CHANCELLOR = "chancellor"
    COMMANDER = "commander"


class ChangeType(str, Enum):
    """IRS 변경 유형."""

    NEW_REGULATION = "new_regulation"
    AMENDMENT = "amendment"
    REPEAL = "repeal"
    CLARIFICATION = "clarification"


class ImpactLevel(str, Enum):
    """변경 영향도 수준."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class ValidationStatus(str, Enum):
    """변경 사항 검증 상태."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


class BalanceStatus(str, Enum):
    """5기둥 균형 상태."""

    BALANCED = "balanced"
    WARNING = "warning"
    IMBALANCED = "imbalanced"


class OptimizationStrategy(str, Enum):
    """최적화 전략 타입."""

    COLLABORATIVE_BOOSTING = "collaborative_boosting"
    CONSENSUS_DRIVEN = "consensus_driven"
    PERFORMANCE_BASED = "performance_based"
    ADAPTIVE = "adaptive"


class CollaborationQuality(str, Enum):
    """협업 품질 등급."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    NEEDS_IMPROVEMENT = "needs_improvement"
