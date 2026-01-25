# Trinity Score: 95.0 (Established by Chancellor)
"""
Meritocracy Models - 능력주의 시스템 데이터 모델

모델 후보, Agent 역할, 선택 증거 등의 데이터클래스 정의.
meritocracy_router.py에서 분리된 모듈.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TypedDict


class PerformanceRecord(TypedDict):
    """성능 기록 타입 정의"""

    timestamp: float
    task_type: str
    trinity_score: float
    response_time: float
    cost: float
    quality_metrics: dict[str, float]
    date: str


class ModelProvider(Enum):
    """AI 모델 제공자"""

    ANTHROPIC = "anthropic"
    XAI = "xai"
    GOOGLE = "google"
    META = "meta"
    OPENAI = "openai"
    LOCAL = "local"


@dataclass
class ModelCandidate:
    """모델 후보 정보"""

    model_id: str
    provider: ModelProvider
    model_name: str
    base_model: str  # 실제 호출할 모델 ID
    context_window: int
    max_tokens: int
    cost_per_token: float
    specialty_tags: list[str]
    performance_history: list[PerformanceRecord] = field(default_factory=list)

    def add_performance_record(
        self,
        task_type: str,
        trinity_score: float,
        response_time: float,
        cost: float,
        quality_metrics: dict[str, float],
    ) -> None:
        """성능 기록 추가"""
        record: PerformanceRecord = {
            "timestamp": time.time(),
            "task_type": task_type,
            "trinity_score": trinity_score,
            "response_time": response_time,
            "cost": cost,
            "quality_metrics": quality_metrics,
            "date": datetime.now().isoformat(),
        }
        self.performance_history.append(record)

        # 최근 100개 기록만 유지
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]

    def get_recent_performance(
        self, task_type: str | None = None, days: int = 7
    ) -> list[PerformanceRecord]:
        """최근 성능 기록 조회"""
        cutoff_time = time.time() - (days * 24 * 60 * 60)

        records = [r for r in self.performance_history if r["timestamp"] > cutoff_time]

        if task_type:
            records = [r for r in records if r["task_type"] == task_type]

        return records

    def calculate_trinity_score(self, task_type: str | None = None, days: int = 7) -> float:
        """Trinity Score 계산"""
        records = self.get_recent_performance(task_type, days)

        if not records:
            return 75.0  # 기본 점수

        # 가중 평균 계산 (최근 기록에 더 높은 가중치)
        total_weight = 0.0
        weighted_sum = 0.0

        for i, record in enumerate(records):
            # 최근 기록에 더 높은 가중치 (지수 감소)
            weight = 2 ** (i / len(records))
            weighted_sum += record["trinity_score"] * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 75.0


@dataclass
class AgentRole:
    """Agent 역할 정의"""

    agent_name: str
    role_description: str
    primary_tasks: list[str]
    trinity_weights: dict[str, float]  # truth, goodness, beauty, serenity, eternity
    model_candidates: list[str]  # 후보 모델 ID들
    min_trinity_threshold: float
    rotation_enabled: bool = True


class SelectionCriteria(TypedDict):
    """선택 기준 타입 정의"""

    pillar_weights: dict[str, float]
    priority: str
    constraints: list[str]


@dataclass
class SelectionEvidence:
    """선택 근거 증거"""

    selection_id: str
    agent_name: str
    task_description: str
    selected_model: str
    trinity_scores: dict[str, float]  # 각 모델의 점수
    selection_reasoning: str
    confidence_level: float
    alternatives_considered: list[str]
    selection_timestamp: float
    selection_criteria: SelectionCriteria

    def to_dict(self) -> dict[str, Any]:
        """Evidence를 딕셔너리로 변환"""
        return {
            "selection_id": self.selection_id,
            "agent_name": self.agent_name,
            "task_description": self.task_description,
            "selected_model": self.selected_model,
            "trinity_scores": self.trinity_scores,
            "selection_reasoning": self.selection_reasoning,
            "confidence_level": self.confidence_level,
            "alternatives_considered": self.alternatives_considered,
            "selection_timestamp": self.selection_timestamp,
            "selection_criteria": self.selection_criteria,
            "evidence_bundle": {
                "format_version": "1.0",
                "kingdom": "AFO",
                "philosophy": "眞善美孝永",
                "timestamp": datetime.fromtimestamp(self.selection_timestamp).isoformat(),
                "validator": "MeritocracyRouter",
            },
        }


__all__ = [
    "ModelProvider",
    "ModelCandidate",
    "AgentRole",
    "SelectionEvidence",
    "PerformanceRecord",
    "SelectionCriteria",
]
