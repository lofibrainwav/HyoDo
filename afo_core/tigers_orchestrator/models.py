"""
Protocol Buffers + Pydantic Models for Tiger Generals (5호장군)

Type-safe interfaces for 5호장군 communication using Protocol Buffers (Protobuf)
and Pydantic models for validation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any, Generic, TypeVar
from uuid import uuid4

from pydantic import BaseModel, Field

T = TypeVar("T")


class MessagePriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MessageType(str, Enum):
    COMMAND = "command"
    STATUS = "status"
    INSIGHT = "insight"
    CONCERN = "concern"
    QUESTION = "question"
    RESPONSE = "response"
    VETO = "veto"
    ENDORSEMENT = "endorsement"


class CrossPillarMessage:
    """Cross-Pillar Message Protocol"""

    def __init__(
        self,
        message_type: MessageType = MessageType.INSIGHT,
        priority: MessagePriority = MessagePriority.MEDIUM,
        from_pillar: str = "",
        to_pillar: str = "",
        context_id: str = "",
        content: str = "",
        data: dict[str, Any] | None = None,
        timestamp: float | None = None,
        ttl_seconds: float = 60.0,
    ) -> None:
        self.id = f"msg_{uuid4().hex[:8]}"
        self.type = message_type
        self.priority = priority
        self.from_pillar = from_pillar
        self.to_pillar = to_pillar
        self.context_id = context_id
        self.content = content
        self.data = data or {}
        self.timestamp = timestamp if timestamp is not None else datetime.now().timestamp()
        self.ttl_seconds = ttl_seconds
        self.processed = False

    @property
    def is_expired(self) -> bool:
        return datetime.now().timestamp() - self.timestamp > self.ttl_seconds

    @property
    def is_broadcast(self) -> bool:
        return self.to_pillar.upper() == "ALL"


class TigerCommandBase(BaseModel):
    """5호장군 공통 커맨드"""

    command_id: str = Field(default_factory=lambda: uuid4().hex)
    context_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, str] = Field(default_factory=dict)


class TigerResponseBase(BaseModel, Generic[T]):
    """5호장군 공통 응답"""

    response_id: str = Field(default_factory=lambda: uuid4().hex)
    context_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    success: bool
    score: float = Field(ge=0.0, le=100.0)
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)


class TruthGuardInput(BaseModel):
    """관우 입력 모델"""

    base: TigerCommandBase
    input_data: dict[str, Any]


class TruthGuardOutput(BaseModel, Generic[T]):
    """관우 출력 모델"""

    base: TigerResponseBase[T]
    type_valid: bool
    validation_level: int = Field(ge=1, le=10)
    validation_errors: list[str] = Field(default_factory=list)


class GoodnessGateInput(BaseModel):
    """장비 입력 모델"""

    base: TigerCommandBase
    truth_output: TruthGuardOutput[dict[str, Any]]
    config: dict[str, Any]


class GoodnessGateOutput(BaseModel, Generic[T]):
    """장비 출력 모델"""

    base: TigerResponseBase[T]
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: str = Field(default="medium")
    blocked_reasons: list[str] = Field(default_factory=list)


class BeautyCraftInput(BaseModel):
    """조운 입력 모델"""

    base: TigerCommandBase
    goodness_output: GoodnessGateOutput[dict[str, Any]]
    code_snippet: str
    ux_level: int = Field(ge=1, le=10)


class BeautyCraftOutput(BaseModel, Generic[T]):
    """조운 출력 모델"""

    base: TigerResponseBase[T]
    enhanced_code: str
    beauty_score: int = Field(ge=0, le=100)


class SerenityDeployInput(BaseModel):
    """마초 입력 모델"""

    base: TigerCommandBase
    beauty_output: BeautyCraftOutput[dict[str, Any]]
    deployment_config: dict[str, Any]


class SerenityDeployOutput(BaseModel, Generic[T]):
    """마초 출력 모델"""

    base: TigerResponseBase[T]
    deployment_status: str
    dry_run: bool
    rollback_available: bool = Field(default=False)


class EternityLogInput(BaseModel):
    """황충 입력 모델"""

    base: TigerCommandBase
    serenity_output: SerenityDeployOutput[dict[str, Any]]
    action: str
    details: dict[str, Any]


class EternityLogOutput(BaseModel, Generic[T]):
    """황충 출력 모델"""

    base: TigerResponseBase[T]
    log_id: str = Field(default_factory=lambda: uuid4().hex)
    persisted: bool
    evidence_path: str | None


class DecisionType(str, Enum):
    """Decision type for Trinity Score based routing"""

    AUTO_RUN = "auto_run"
    ASK_COMMANDER = "ask_commander"
    BLOCK = "block"


class ActionType(str, Enum):
    """Action types for Ambassador pattern"""

    DEPLOY = "deploy"
    NOTIFY = "notify"
    SET_STATE = "set_state"
    ROLLBACK = "rollback"
    LOG_EVIDENCE = "log_evidence"


class DecisionAction(BaseModel):
    """Decision action model for Ambassador pattern execution"""

    action_id: str = Field(default_factory=lambda: uuid4().hex)
    action_type: ActionType
    target: str
    payload: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    decision_type: DecisionType = DecisionType.ASK_COMMANDER
    priority: MessagePriority = MessagePriority.MEDIUM
