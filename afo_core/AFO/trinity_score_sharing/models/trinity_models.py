"""Trinity Pillar and Score Models.

眞善美孝영 5기둥 점수 모델 및 에이전트별 점수 기록 구조.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .enums import AgentType, BalanceStatus, OptimizationStrategy

# SSOT 가중치 상수로 정의
WEIGHT_TRUTH: float = 0.35
WEIGHT_GOODNESS: float = 0.35
WEIGHT_BEAUTY: float = 0.20
WEIGHT_SERENITY: float = 0.08
WEIGHT_ETERNITY: float = 0.02

# 거버넌스 임계값
THRESHOLD_AUTO_RUN_SCORE: float = 90.0
THRESHOLD_AUTO_RUN_RISK: float = 10.0

WEIGHT_TRUTH_100: float = 35.0
WEIGHT_GOODNESS_100: float = 35.0
WEIGHT_BEAUTY_100: float = 20.0
WEIGHT_SERENITY_100: float = 8.0
WEIGHT_ETERNITY_100: float = 2.0

WEIGHTS = {
    "truth": WEIGHT_TRUTH,
    "goodness": WEIGHT_GOODNESS,
    "beauty": WEIGHT_BEAUTY,
    "serenity": WEIGHT_SERENITY,
    "eternity": WEIGHT_ETERNITY,
}


class PillarScores(BaseModel):
    """眞善美孝永 5기둥 점수 (0.0 ~ 1.0)."""

    truth: float = Field(0.0, ge=0.0, le=1.0)
    goodness: float = Field(0.0, ge=0.0, le=1.0)
    beauty: float = Field(0.0, ge=0.0, le=1.0)
    serenity: float = Field(0.0, ge=0.0, le=1.0)
    eternity: float = Field(0.0, ge=0.0, le=1.0)

    @property
    def trinity_score(self) -> float:
        """가중 합 계산 (0.0 ~ 1.0)."""
        return (
            self.truth * WEIGHT_TRUTH
            + self.goodness * WEIGHT_GOODNESS
            + self.beauty * WEIGHT_BEAUTY
            + self.serenity * WEIGHT_SERENITY
            + self.eternity * WEIGHT_ETERNITY
        )

    @property
    def trinity_score_100(self) -> float:
        """100점 스케일 Trinity Score."""
        return self.trinity_score * 100

    @property
    def balance_delta(self) -> float:
        """5기둥 균형 편차 (max - min)."""
        scores = [self.truth, self.goodness, self.beauty, self.serenity, self.eternity]
        return max(scores) - min(scores)

    @property
    def balance_status(self) -> BalanceStatus:
        """균형 상태 판정."""
        delta = self.balance_delta
        if delta < 0.1:
            return BalanceStatus.BALANCED
        elif delta < 0.3:
            return BalanceStatus.WARNING
        else:
            return BalanceStatus.IMBALANCED

    def to_weights_dict(self) -> dict[str, float]:
        """가중치 딕셔너리 반환."""
        return {
            "truth": WEIGHT_TRUTH,
            "goodness": WEIGHT_GOODNESS,
            "beauty": WEIGHT_BEAUTY,
            "serenity": WEIGHT_SERENITY,
            "eternity": WEIGHT_ETERNITY,
        }


class AgentScoreEntry(BaseModel):
    """개별 Agent의 Trinity Score 엔트리."""

    agent_id: str
    agent_type: AgentType
    pillar_scores: PillarScores
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    contribution_weight: float = Field(1.0, ge=0.0)

    @property
    def trinity_score(self) -> float:
        """현재 Trinity Score."""
        return self.pillar_scores.trinity_score

    @property
    def weighted_contribution(self) -> float:
        """가중 기여도 (confidence × contribution_weight × trinity_score)."""
        return self.confidence * self.contribution_weight * self.trinity_score


class TrinityScoreUpdateEvent(BaseModel):
    """점수 업데이트 이벤트."""

    event_id: UUID = Field(default_factory=uuid4)
    session_id: str
    agent_id: str
    new_scores: PillarScores
    reason: str
    timestamp: datetime = Field(default_factory=datetime.now)


class CollaborationFeedback(BaseModel):
    """협업 피드백."""

    feedback_id: UUID = Field(default_factory=uuid4)
    session_id: str
    from_agent: str
    to_agent: str
    rating: float = Field(1.0, ge=0.0, le=1.0)
    comment: str = ""


class CollaborationMetricsSnapshot(BaseModel):
    """협업 메트릭 스냅샷."""

    session_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    average_trinity_score: float
    consensus_level: float
    active_agents: list[str]


class OptimizationPolicy(BaseModel):
    """최적화 정책."""

    policy_id: str
    strategy: OptimizationStrategy
    min_score_threshold: float = 0.7


class SharingPolicy(BaseModel):
    """공유 정책."""

    policy_id: str
    is_public: bool = False
    allowed_agents: list[AgentType] = []


class TrinityScorePool(BaseModel):
    """점수 풀 - 다중 에이전트의 Trinity Score를 관리하는 컨테이너."""

    pool_id: str
    session_id: str
    entries: list[AgentScoreEntry] = []
    auto_optimize: bool = True

    @property
    def agent_count(self) -> int:
        """풀에 등록된 에이전트 수."""
        return len(self.entries)

    @property
    def average_trinity_score(self) -> float:
        """풀 내 평균 Trinity Score."""
        if not self.entries:
            return 0.0
        return sum(e.trinity_score for e in self.entries) / len(self.entries)

    @property
    def weighted_average_score(self) -> float:
        """가중 평균 Trinity Score (기여도 반영)."""
        if not self.entries:
            return 0.0
        total_weight = sum(e.contribution_weight for e in self.entries)
        if total_weight == 0:
            return 0.0
        return sum(e.weighted_contribution for e in self.entries) / total_weight

    @property
    def collaboration_intensity(self) -> float:
        """협업 강도 (에이전트 수 기반)."""
        return min(1.0, self.agent_count / 3.0)  # 3명이 최대

    @property
    def score_variance(self) -> float:
        """점수 분산 (에이전트 간 점수 차이)."""
        if len(self.entries) < 2:
            return 0.0
        scores = [e.trinity_score for e in self.entries]
        mean = sum(scores) / len(scores)
        return sum((s - mean) ** 2 for s in scores) / len(scores)

    def get_governance_decision(self) -> str:
        """거버넌스 결정 (AUTO_RUN 또는 ASK_COMMANDER)."""
        if not self.entries:
            return "ASK_COMMANDER"

        avg_score = self.average_trinity_score * 100  # 100점 스케일
        avg_confidence = sum(e.confidence for e in self.entries) / len(self.entries)

        if avg_score >= THRESHOLD_AUTO_RUN_SCORE and avg_confidence >= 0.9:
            return "AUTO_RUN"
        return "ASK_COMMANDER"

    def should_optimize(self) -> bool:
        """최적화 필요 여부 판단."""
        if not self.auto_optimize:
            return False
        if self.agent_count < 2:
            return False
        # 분산이 0.2 이상이면 최적화 필요
        return self.score_variance >= 0.02  # 0.2^2 = 0.04, sqrt(0.02) ≈ 0.14


class TrinityScoreSharingContract(BaseModel):
    """점수 공유 계약."""

    contract_id: UUID = Field(default_factory=uuid4)
    session_id: str
    parties: list[str]
    sharing_policy: SharingPolicy
    optimization_policy: OptimizationPolicy
