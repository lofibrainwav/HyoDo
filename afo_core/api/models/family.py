# Trinity Score: 90.0 (Established by Chancellor)
"""Family Hub OS Models
眞 (Truth): Pydantic 기반 타입 안전성 확보
"""

from datetime import datetime

from pydantic import BaseModel, Field


class FamilyMember(BaseModel):
    """가족 구성원 모델
    美 (Beauty): 명확한 역할 정의
    """

    id: str = Field(..., description="구성원 고유 ID")
    name: str = Field(..., description="구성원 이름")
    role: str = Field(..., description="가족 내 역할 (예: Head, Supporter)")
    status: str = Field(default="Active", description="현재 상태 (예: Sleeping, Working)")
    current_location: str = Field(default="Home", description="현재 위치 (가상)")
    last_active: datetime = Field(default_factory=datetime.now, description="마지막 활동 시간")


class Activity(BaseModel):
    """활동 로그 모델
    善 (Goodness): 기록을 통한 이해와 배려
    """

    id: str = Field(..., description="활동 고유 ID")
    member_id: str = Field(..., description="구성원 ID")
    type: str = Field(..., description="활동 유형 (예: Study, Play)")
    description: str = Field(..., description="활동 상세 내용")
    timestamp: datetime = Field(default_factory=datetime.now, description="활동 시간")
    trinity_impact: float = Field(
        default=0.0, description="행복 지표에 미치는 영향 (-10.0 ~ +10.0)"
    )


class FamilyHubSystem(BaseModel):
    """Family Hub 시스템 상태 모델
    孝 (Serenity): 가족 전체의 평온함 수치화
    """

    overall_happiness: float = Field(default=0.0, description="가족 전체 행복 지수")
    active_members_count: int = Field(default=0, description="현재 활동 중인 구성원 수")
    members: list[FamilyMember] = Field(default_factory=list, description="구성원 목록")
    activities: list[Activity] = Field(default_factory=list, description="최근 활동 목록")
