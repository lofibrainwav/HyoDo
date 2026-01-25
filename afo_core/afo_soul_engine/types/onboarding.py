from typing import Any, List, Optional

from pydantic import BaseModel


# Request Models
class OnboardingRequest(BaseModel):
    """온보딩 요청 모델"""

    user_id: str | None = None
    agent_type: str | None = None
    language: str = "ko"


# Response Models
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


class AgentRegistration(BaseModel):
    """에이전트 등록 요청 모델"""

    agent_id: str
    agent_type: str  # claude, opencode, antigravity, gemini, codex
    capabilities: list[str] = []
    version: str = "1.0.0"


class KnowledgeQuery(BaseModel):
    """지식 검색 요청 모델"""

    query: str
    agent_id: str
    top_k: int = 5
