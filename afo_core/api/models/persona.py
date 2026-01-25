# Trinity Score: 90.0 (Established by Chancellor)
"""Persona Models
Phase 2: Family Hub OS - 페르소나 모델링
TRINITY-OS 페르소나 시스템 통합
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PersonaTrinityScore(BaseModel):
    """페르소나별 Trinity Score (眞善美孝永)"""

    truth: float = Field(default=0.0, ge=0.0, le=100.0, description="眞 (Truth) 점수")
    goodness: float = Field(default=0.0, ge=0.0, le=100.0, description="善 (Goodness) 점수")
    beauty: float = Field(default=0.0, ge=0.0, le=100.0, description="美 (Beauty) 점수")
    serenity: float = Field(default=0.0, ge=0.0, le=100.0, description="孝 (Serenity) 점수")
    eternity: float = Field(default=0.0, ge=0.0, le=100.0, description="永 (Eternity) 점수")
    total_score: float = Field(default=0.0, ge=0.0, le=100.0, description="총점")


class PersonaContext(BaseModel):
    """페르소나 맥락 정보"""

    current_role: str = Field(..., description="현재 역할 (사령관, 가족 가장, 창작자 등)")
    active_personas: list[str] = Field(default_factory=list, description="활성 페르소나 목록")
    preferences: dict[str, Any] = Field(default_factory=dict, description="페르소나별 선호도")
    behavior_patterns: dict[str, Any] = Field(default_factory=dict, description="행동 패턴")


class Persona(BaseModel):
    """페르소나 모델 (眞善美孝永)"""

    id: str = Field(..., description="페르소나 ID")
    name: str = Field(..., description="페르소나 이름")
    role: str = Field(..., description="역할 (사령관, 가족 가장, 창작자 등)")
    description: str = Field(..., description="페르소나 설명")
    icon: str = Field(default="👤", description="아이콘")
    color: str = Field(default="blue", description="색상")

    # Trinity Score
    trinity_score: PersonaTrinityScore = Field(
        default_factory=PersonaTrinityScore, description="페르소나별 Trinity Score"
    )

    # 맥락 정보
    context: PersonaContext = Field(
        default_factory=lambda: PersonaContext(current_role="user"),
        description="페르소나 맥락 정보",
    )

    # TRINITY-OS 연동
    trinity_os_persona_id: str | None = Field(
        default=None, description="TRINITY-OS 페르소나 ID (연동용)"
    )

    # 메타데이터
    created_at: datetime = Field(default_factory=datetime.utcnow, description="생성 일시")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="업데이트 일시")
    is_active: bool = Field(default=True, description="활성 상태")


class PersonaSwitchRequest(BaseModel):
    """페르소나 전환 요청"""

    persona_id: str = Field(..., description="전환할 페르소나 ID")
    context: dict[str, Any] = Field(default_factory=dict, description="추가 맥락 정보")


class PersonaResponse(BaseModel):
    """페르소나 응답 모델"""

    persona: Persona = Field(..., description="페르소나 정보")
    message: str = Field(..., description="응답 메시지")
    trinity_score: PersonaTrinityScore = Field(..., description="Trinity Score")


class PersonaLogEntry(BaseModel):
    """페르소나 로그 엔트리 (로그 브릿지용)"""

    persona_id: str = Field(..., description="페르소나 ID")
    action: str = Field(..., description="액션")
    context: dict[str, Any] = Field(default_factory=dict, description="맥락 정보")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="타임스탬프")
    trinity_score: PersonaTrinityScore | None = Field(
        default=None, description="Trinity Score (있는 경우)"
    )
