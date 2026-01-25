"""Onboarding Models - 온보딩 데이터 모델"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


# Pydantic Models (FastAPI)
class OnboardingRequest(BaseModel):
    """온보딩 요청 모델"""

    user_id: str | None = None
    agent_type: str | None = None
    language: str = "ko"


class OnboardingResponse(BaseModel):
    """온보딩 응답 모델"""

    stage: int
    title: str
    description: str
    next_action: str
    data: dict[str, Any]


class SystemArchitectureResponse(BaseModel):
    """시스템 아키텍처 응답 모델"""

    sanctuaries: list[dict[str, Any]]
    organs: list[dict[str, Any]]
    strategists: list[dict[str, Any]]
    pillars: list[dict[str, Any]]


class AgentMemorySystemResponse(BaseModel):
    """에이전트 기억 시스템 응답 모델"""

    context7: dict[str, Any]
    memory_manager: dict[str, Any]
    yeongdeok: dict[str, Any]
    integration_status: dict[str, bool]


class MemorySearchRequest(BaseModel):
    """메모리 검색 요청 모델"""

    query: str


class MemorySearchResponse(BaseModel):
    """메모리 검색 응답 모델"""

    query: str
    context7_response: dict[str, Any] | None
    memory_response: dict[str, Any] | None
    yeongdeok_response: dict[str, Any] | None


# Dataclasses (내부 사용)
@dataclass
class SanctuaryData:
    """성역 데이터"""

    sanctuary_type: str
    label: str
    organ_label: str
    position_x: float
    position_y: float
    scale: float
    trinity_score: float
    risk_level: int
    description: str


@dataclass
class OrganData:
    """오장 데이터"""

    name: str
    role: str
    implementation: str
    status: str


@dataclass
class StrategistData:
    """전략가 데이터"""

    name: str
    pillar: str
    weight: float
    role: str
    symbol: str
    trinity_score: float


@dataclass
class PillarData:
    """기둥 데이터"""

    name: str
    weight: float
    description: str
    trinity_score: float


__all__ = [
    # Pydantic Models
    "OnboardingRequest",
    "OnboardingResponse",
    "SystemArchitectureResponse",
    "AgentMemorySystemResponse",
    "MemorySearchRequest",
    "MemorySearchResponse",
    # Dataclasses
    "SanctuaryData",
    "OrganData",
    "StrategistData",
    "PillarData",
]
