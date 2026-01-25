from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, Union

from pydantic import BaseModel, Field

# Trinity Score: 90.0 (Established by Chancellor)


class PhilosophyScores(BaseModel):
    """眞善美孝(Serenity) 점수"""

    truth: float = Field(ge=0.0, le=100.0)
    goodness: float = Field(ge=0.0, le=100.0)
    beauty: float = Field(ge=0.0, le=100.0)
    serenity: float = Field(ge=0.0, le=100.0)

    @property
    def average(self) -> float:
        return (self.truth + self.goodness + self.beauty + self.serenity) / 4.0


class SkillRequest(BaseModel):
    """스킬 등록 요청"""

    skill_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    execution_mode: str = Field(..., min_length=1)
    parameters: dict[str, Any] | None = Field(default=None)


class SkillResponse(BaseModel):
    """스킬 응답"""

    skill_id: str
    name: str
    description: str
    category: Any
    execution_mode: Any
    status: Any | None = None
    philosophy: PhilosophyScores | None = None
    tags: list[str] | None = None
    parameters: dict[str, Any] | None = None
    execution_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SkillFilterRequest(BaseModel):
    """스킬 목록 필터"""

    category: str | None = None
    status: str | None = None
    tags: list[str] | None = None
    search: str | None = None
    min_philosophy_avg: float | None = Field(default=None, ge=0.0, le=100.0)
    execution_mode: str | None = None
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=0, le=100)


class SkillListResponse(BaseModel):
    """스킬 목록 응답"""

    skills: list[SkillResponse]
    total_count: int
    filtered_count: int
    offset: int
    limit: int


class SkillExecuteRequest(BaseModel):
    """스킬 실행 요청"""

    skill_id: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout: int | None = Field(default=30, ge=1, le=300)


class SkillExecutionResult(BaseModel):
    """스킬 실행 결과"""

    skill_id: str
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    philosophy_score: PhilosophyScores | None = None
    status: str = "unknown"


class SkillCategoryStats(BaseModel):
    """카테고리별 스킬 통계"""

    category: str
    count: int
    avg_philosophy: float = 0.0
    execution_count: int = 0
    description: str = ""


class SkillStatsResponse(BaseModel):
    """스킬 시스템 통계"""

    total_skills: int = 0
    active_skills: int = 0
    categories: list[SkillCategoryStats] = Field(default_factory=list)
    recent_executions: int = 0
    avg_execution_time: float = 0.0
    philosophy_distribution: dict[str, int] = Field(default_factory=dict)
    execution_stats: dict[str, Any] = Field(default_factory=dict)
