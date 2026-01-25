"""L3 Collaboration Hub Models (TICKET-107)

Application Layer - 3책사 협업을 위한 데이터 모델 정의.
SSOT: AGENTS.md, TICKET-107
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# Runtime import for Pydantic model validation (intentional - TC001 suppressed)
from AFO.trinity_score_sharing.domain_models import AgentType


class CollaborationState(str, Enum):
    """협업 세션 상태"""

    IDLE = "idle"  # 대기
    DISCUSSING = "discussing"  # 토론 중 (정반합)
    VOTING = "voting"  # 투표 중
    CONSENSUS_REACHED = "consensus_reached"  # 합의 도달
    DEADLOCK = "deadlock"  # 교착 상태 (중재 필요)
    CANCELLED = "cancelled"  # 취소됨
    COMPLETED = "completed"  # 완료됨


class VoteType(str, Enum):
    """투표 유형"""

    APPROVE = "approve"  # 찬성
    REJECT = "reject"  # 반대
    ABSTAIN = "abstain"  # 기권
    VECO = "veco"  # Veto with Comment (조건부 거부/수정 제안)


class Vote(BaseModel):
    """개별 투표"""

    agent: AgentType
    vote_type: VoteType
    weight: float = Field(default=1.0, ge=0.0, le=2.0)  # Trinity Score 기반 가중치
    reasoning: str | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ConsensusResult(BaseModel):
    """합의 결과"""

    success: bool
    approvals: int
    rejections: int
    abstentions: int
    weighted_approval_rate: float  # 가중치 반영 찬성률 (0.0 ~ 1.0)
    decision: str  # "APPROVED", "REJECTED", "DEADLOCK"
    rag_context_summary: str | None = None  # 합의된 결론 요약
    timestamp: datetime = Field(default_factory=datetime.now)


class DiscussionTopic(BaseModel):
    """토론 주제 (Ticket 또는 Issue)"""

    topic_id: str  # TICKET-ID or UUID
    title: str
    description: str
    initiator: AgentType
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class CollaborationContext(BaseModel):
    """협업 세션 컨텍스트"""

    session_id: UUID = Field(default_factory=uuid4)
    topic: DiscussionTopic
    state: CollaborationState = CollaborationState.IDLE

    # 참여자
    participants: list[AgentType] = Field(default_factory=list)

    # 상태 메타데이터
    started_at: datetime = Field(default_factory=datetime.now)
    last_activity_at: datetime = Field(default_factory=datetime.now)

    # 결과
    result: ConsensusResult | None = None
