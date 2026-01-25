"""Chancellor V3 Orchestrator Models.
Phase 73: The Truth Crusade & Quality Fortress
Pillar: 眞 (Truth) - Strict Typing & Schema Safety
"""

from enum import Enum
from typing import Any, Type

from pydantic import BaseModel, Field


# --- Cost Types ---
class CostTier(str, Enum):
    """비용 티어 정의."""

    FREE = "free"
    CHEAP = "cheap"
    EXPENSIVE = "expensive"


class ModelConfig(BaseModel):
    """모델별 상세 설정 모델."""

    model_id: str
    provider: str
    cost_tier: CostTier
    max_tokens: int
    quality_score: float
    cost_per_1k_tokens: float = 0.0

    def __repr__(self) -> str:
        return f"ModelConfig({self.model_id}, tier={self.cost_tier.value})"


# --- Router Analysis Models ---
class KeyTriggerAnalysis(BaseModel):
    """키워드 트리거 분석 결과."""

    pillars: list[str] = Field(..., description="선택된 기둥 목록")
    matched_triggers: dict[str, list[str]] = Field(..., description="매칭된 트리거 목록")
    scores: dict[str, float] = Field(..., description="기둥별 가중치 합계")
    confidence: float = Field(..., description="분석 신뢰도 (0.0~1.0)")
    total_triggers_matched: int = Field(..., description="총 매칭된 트리거 수")


class CostEstimate(BaseModel):
    """비용 및 모델 추정 정보."""

    tier: str = Field(..., description="선택된 비용 티어")
    model: str = Field(..., description="선택된 모델 ID")
    estimated_tokens: int = Field(..., description="추정 사용 토큰 수")
    estimated_cost_usd: float = Field(..., description="추정 비용 (USD)")
    quality_score: float = Field(..., description="추정 품질 점수")


class RoutingInfo(BaseModel):
    """전체 라우팅 분석 정보 (V3 전용)."""

    version: str = Field("V3", description="라우터 버전")
    key_trigger: KeyTriggerAnalysis = Field(..., description="키워드 라우팅 상세")
    cost_aware: CostEstimate = Field(..., description="비용 라우팅 상세")
    optimization: dict[str, Any] = Field(..., description="최적화 수치")


# --- Assessment Models ---
class StrategistSummary(BaseModel):
    """개별 Strategist 결과 요약."""

    score: float = Field(..., description="기둥별 점수 (0.0~1.0)")
    reasoning: str = Field(..., description="요약된 평가 근거")
    issues_count: int = Field(..., description="발견된 이슈 수")
    has_errors: bool = Field(..., description="실행 중 에러 발생 여부")
    duration_ms: float = Field(..., description="실행 소요 시간 (ms)")


class DecisionThresholds(BaseModel):
    """의사결정 임계값 정보."""

    auto_run_trinity: float
    auto_run_risk: float
    ask_trinity: float
    ask_risk: float


class AssessmentResult(BaseModel):
    """최종 통합 평가 결과 및 의사결정."""

    decision: str = Field(..., description="최종 판정 (AUTO_RUN / ASK_COMMANDER / BLOCK)")
    trinity_score: float = Field(..., description="최종 Trinity Score (0-100)")
    risk_score: float = Field(..., description="최종 Risk Score (0-100)")
    confidence: float = Field(..., description="판정 신뢰도 (0.0~1.0)")
    pillar_scores: dict[str, float] = Field(..., description="5기둥 상세 점수")
    thresholds: DecisionThresholds = Field(..., description="판정 기준 임계값")
    strategist_results: dict[str, StrategistSummary] = Field(..., description="전략가별 요약 결과")
