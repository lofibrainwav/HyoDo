from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentLevel(str, Enum):
    """AI 에이전트 레벨"""

    ASSOCIATE = "ASSOCIATE"  # 초안/수집
    MANAGER = "MANAGER"  # 전략/품질
    AUDITOR = "AUDITOR"  # 규정/감사


class RCAteWorkflow(BaseModel):
    """R.C.A.T.E. 구조화 워크플로우"""

    role: str = Field(..., description="에이전트 역할 정의")
    context: dict[str, Any] = Field(..., description="IRS/FTB SSOT + 고객 데이터 + 비즈니스 목적")
    action: str = Field(..., description="구체적인 실행 계획")
    task: list[str] = Field(..., description="세부 작업 분해")
    execution: dict[str, Any] = Field(..., description="단계별 실행 결과")


class EvidenceBundle(BaseModel):
    """증거 번들 - 완전한 재현 가능성 보장 (JULIE_CPA_2_010126.md 확장)"""

    bundle_id: str = Field(..., description="UUID 기반 증거 ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="데이터 가져온 시각"
    )
    input_hash: str = Field(..., description="입력 데이터 해시")
    output_hash: str = Field(..., description="출력 결과 해시")
    sha256_hash: str = Field(..., description="번들 전체 SHA256 해시")
    evidence_links: list[str] = Field(..., description="IRS/FTB 근거 링크")
    calculation_log: dict[str, Any] = Field(..., description="계산 수식 및 파라미터")
    trinity_score: dict[str, float] = Field(..., description="Trinity Score 평가")
    impact_level: str = Field(default="medium", description="Critical/High/Medium 영향도")
    metacognition_insights: dict[str, Any] = Field(
        default_factory=dict, description="메타인지 검증 결과"
    )
    source_url: str = Field(default="", description="IRS/FTB 소스 URL")
    ticket: str = Field(default="TICKET-043", description="관련 티켓")
