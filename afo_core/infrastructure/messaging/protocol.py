"""Agent Messaging Protocol (TICKET-108)

L2 Infrastructure Layer - Agent 메시징 프로토콜 및 보안 채널 표준화
SSOT: AGENTS.md, domain_models.py (TICKET-109)

Cross-Agent 실시간 통신을 위한 표준화된 메시징 프로토콜.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

# TICKET-109 도메인 모델 통합
from AFO.trinity_score_sharing.domain_models import AgentType, PillarScores

logger = logging.getLogger(__name__)


class MessagePriority(str, Enum):
    """메시지 우선순위"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class MessageStatus(str, Enum):
    """메시지 상태"""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"


class SecurityLevel(str, Enum):
    """보안 레벨"""

    PUBLIC = "public"  # 인증 불필요
    AUTHENTICATED = "authenticated"  # 인증 필요
    ENCRYPTED = "encrypted"  # 인증 + 암호화
    FULL = "full"  # 인증 + 암호화 + 서명


class MessageType(str, Enum):
    """메시지 타입"""

    # Trinity Score 관련
    TRINITY_SCORE_UPDATE = "trinity_score_update"
    TRINITY_SCORE_SYNC = "trinity_score_sync"

    # 협업 관련
    COLLABORATION_REQUEST = "collaboration_request"

    # Agent 통신
    AGENT_REQUEST = "agent_request"

    # 시스템
    SYSTEM_ALERT = "system_alert"

    # Pillar 간 통신 (cross_pillar.py 호환)
    INSIGHT = "insight"
    CONCERN = "concern"
    QUESTION = "question"
    RESPONSE = "response"
    VETO = "veto"
    ENDORSEMENT = "endorsement"


class AgentMessage(BaseModel):
    """Agent 간 메시지 (L2 Infrastructure 표준)

    TICKET-109 도메인 모델과 통합된 메시징 프로토콜.
    """

    # 식별자
    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID | None = None  # 요청-응답 연결용
    session_id: str = Field(min_length=1, max_length=256)

    # 발신/수신
    from_agent: AgentType
    to_agent: AgentType | Literal["ALL", "STRATEGISTS", "SCHOLARS"]

    # 메시지 내용
    message_type: MessageType
    priority: MessagePriority = MessagePriority.NORMAL
    payload: dict[str, Any] = Field(default_factory=dict)

    # Trinity Score 컨텍스트 (옵션)
    pillar_scores: PillarScores | None = None

    # 시간 관련
    timestamp: datetime = Field(default_factory=datetime.now)
    expires_at: datetime | None = None
    ttl_seconds: int = Field(default=300, ge=1, le=3600)

    # 상태
    status: MessageStatus = MessageStatus.PENDING
    retry_count: int = Field(default=0, ge=0, le=10)

    @property
    def is_expired(self) -> bool:
        """메시지 만료 여부"""
        if self.expires_at:
            return datetime.now() > self.expires_at
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds

    @property
    def is_broadcast(self) -> bool:
        """브로드캐스트 메시지 여부"""
        return self.to_agent in ["ALL", "STRATEGISTS", "SCHOLARS"]

    def get_target_agents(self) -> list[AgentType]:
        """대상 Agent 목록"""
        if self.to_agent == "ALL":
            return list(AgentType)
        elif self.to_agent == "STRATEGISTS":
            return [AgentType.JANG_YEONG_SIL, AgentType.YI_SUN_SIN, AgentType.SHIN_SAIMDANG]
        elif self.to_agent == "SCHOLARS":
            return [AgentType.BANGTONG, AgentType.JARYONG, AgentType.YUKSON, AgentType.YEONGDEOK]
        else:
            return [self.to_agent] if isinstance(self.to_agent, AgentType) else []


class MessageEnvelope(BaseModel):
    """메시지 봉투 (보안 레이어)

    메시지를 감싸는 보안 봉투. 인증, 암호화, 서명 정보 포함.
    """

    envelope_id: UUID = Field(default_factory=uuid4)
    message: AgentMessage

    # 보안 메타데이터
    security_level: SecurityLevel = SecurityLevel.AUTHENTICATED
    sender_token: str | None = None  # JWT 또는 API 토큰
    signature: str | None = None  # HMAC 서명
    encrypted: bool = False

    # 라우팅 메타데이터
    hop_count: int = Field(default=0, ge=0, le=10)
    route_path: list[str] = Field(default_factory=list)

    # 전송 메타데이터
    sent_at: datetime | None = None
    acknowledged_at: datetime | None = None

    def sign(self, secret_key: str) -> str:
        """메시지 서명 생성"""
        payload = (
            f"{self.envelope_id}:{self.message.message_id}:{self.message.timestamp.isoformat()}"
        )
        signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        self.signature = signature
        return signature

    def verify_signature(self, secret_key: str) -> bool:
        """서명 검증"""
        if not self.signature:
            return False
        # 서명 재계산 (self.signature를 수정하지 않음)
        payload = (
            f"{self.envelope_id}:{self.message.message_id}:{self.message.timestamp.isoformat()}"
        )
        expected = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(self.signature, expected)


class MessageAck(BaseModel):
    """메시지 확인 응답"""

    ack_id: UUID = Field(default_factory=uuid4)
    message_id: UUID
    envelope_id: UUID
    acknowledged_by: AgentType
    timestamp: datetime = Field(default_factory=datetime.now)

    # 처리 결과
    success: bool = True
    error_code: str | None = None
    error_message: str | None = None

    # 처리 시간 (ms)
    processing_time_ms: float | None = None


class SecureChannelConfig(BaseModel):
    """보안 채널 설정"""

    channel_id: UUID = Field(default_factory=uuid4)
    name: str = Field(default="default", max_length=128)

    # 보안 설정
    security_level: SecurityLevel = SecurityLevel.AUTHENTICATED
    require_signature: bool = False
    require_encryption: bool = False

    # 인증 설정
    auth_enabled: bool = True
    allowed_agents: list[AgentType] = Field(default_factory=list)
    blocked_agents: list[AgentType] = Field(default_factory=list)

    # 속도 제한
    rate_limit_enabled: bool = True
    max_messages_per_minute: int = Field(default=100, ge=1, le=10000)
    max_message_size_bytes: int = Field(default=65536, ge=1024, le=10485760)

    # 재시도 설정
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0)

    # 타임아웃
    connect_timeout_seconds: float = Field(default=10.0, ge=1.0, le=300.0)
    message_timeout_seconds: float = Field(default=30.0, ge=1.0, le=600.0)

    def is_agent_allowed(self, agent: AgentType) -> bool:
        """Agent 접근 허용 여부"""
        if agent in self.blocked_agents:
            return False
        return not self.allowed_agents or agent in self.allowed_agents


class AgentMessagingProtocol:
    """Agent 메시징 프로토콜 (L2 Infrastructure)

    Cross-Agent 통신을 위한 표준화된 프로토콜.
    TICKET-109 도메인 모델과 통합.
    """

    VERSION = "1.0.0"

    def __init__(self, config: SecureChannelConfig | None = None) -> None:
        self.config = config or SecureChannelConfig()
        self._message_handlers: dict[MessageType, list] = {}
        self._pending_messages: dict[UUID, MessageEnvelope] = {}
        self._message_history: list[MessageEnvelope] = []
        self._max_history = 1000

        # 속도 제한 추적
        self._rate_limit_tracker: dict[str, list[float]] = {}

        logger.info(f"AgentMessagingProtocol v{self.VERSION} initialized")

    def register_handler(
        self,
        message_type: MessageType,
        handler,
    ) -> None:
        """메시지 핸들러 등록"""
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    def create_message(
        self,
        from_agent: AgentType,
        to_agent: AgentType | str,
        message_type: MessageType,
        session_id: str,
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        pillar_scores: PillarScores | None = None,
        correlation_id: UUID | None = None,
    ) -> AgentMessage:
        """메시지 생성"""
        return AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            session_id=session_id,
            payload=payload or {},
            priority=priority,
            pillar_scores=pillar_scores,
            correlation_id=correlation_id,
        )

    def wrap_message(
        self,
        message: AgentMessage,
        sender_token: str | None = None,
        security_level: SecurityLevel | None = None,
    ) -> MessageEnvelope:
        """메시지를 보안 봉투로 감싸기"""
        return MessageEnvelope(
            message=message,
            security_level=security_level or self.config.security_level,
            sender_token=sender_token,
        )

    def check_rate_limit(self, agent: AgentType) -> bool:
        """속도 제한 확인"""
        if not self.config.rate_limit_enabled:
            return True

        agent_key = agent.value
        now = time.time()
        window_start = now - 60  # 1분 윈도우

        # 오래된 기록 정리
        if agent_key in self._rate_limit_tracker:
            self._rate_limit_tracker[agent_key] = [
                t for t in self._rate_limit_tracker[agent_key] if t > window_start
            ]
        else:
            self._rate_limit_tracker[agent_key] = []

        # 제한 확인
        if len(self._rate_limit_tracker[agent_key]) >= self.config.max_messages_per_minute:
            return False

        # 기록 추가
        self._rate_limit_tracker[agent_key].append(now)
        return True

    def validate_envelope(self, envelope: MessageEnvelope) -> tuple[bool, str | None]:
        """메시지 봉투 검증"""
        message = envelope.message

        # 만료 확인
        if message.is_expired:
            return False, "Message expired"

        # Agent 권한 확인
        if not self.config.is_agent_allowed(message.from_agent):
            return False, f"Agent {message.from_agent} not allowed"

        # 속도 제한 확인
        if not self.check_rate_limit(message.from_agent):
            return False, f"Rate limit exceeded for {message.from_agent}"

        # 서명 확인 (필요시)
        if self.config.require_signature and not envelope.signature:
            return False, "Signature required but not provided"

        # 메시지 크기 확인
        import json

        message_size = len(json.dumps(message.model_dump(), default=str).encode())
        if message_size > self.config.max_message_size_bytes:
            return False, f"Message size {message_size} exceeds limit"

        return True, None

    async def process_envelope(self, envelope: MessageEnvelope) -> MessageAck:
        """메시지 봉투 처리"""
        start_time = time.time()
        message = envelope.message

        # 검증
        is_valid, error = self.validate_envelope(envelope)
        if not is_valid:
            return MessageAck(
                message_id=message.message_id,
                envelope_id=envelope.envelope_id,
                acknowledged_by=AgentType.CHANCELLOR,
                success=False,
                error_code="VALIDATION_FAILED",
                error_message=error,
            )

        # 핸들러 실행
        handlers = self._message_handlers.get(message.message_type, [])
        errors = []

        for handler in handlers:
            try:
                import asyncio

                if asyncio.iscoroutinefunction(handler):
                    await handler(envelope)
                else:
                    handler(envelope)
            except Exception as e:
                logger.error(f"Handler error for {message.message_type}: {e}")
                errors.append(str(e))

        # 히스토리 저장
        self._message_history.append(envelope)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history :]

        # ACK 생성
        processing_time = (time.time() - start_time) * 1000
        envelope.message.status = MessageStatus.ACKNOWLEDGED
        envelope.acknowledged_at = datetime.now()

        return MessageAck(
            message_id=message.message_id,
            envelope_id=envelope.envelope_id,
            acknowledged_by=AgentType.CHANCELLOR,
            success=len(errors) == 0,
            error_code="HANDLER_ERROR" if errors else None,
            error_message="; ".join(errors) if errors else None,
            processing_time_ms=processing_time,
        )

    def get_pending_messages(
        self,
        for_agent: AgentType | None = None,
    ) -> list[MessageEnvelope]:
        """대기 중인 메시지 조회"""
        pending = [
            env
            for env in self._pending_messages.values()
            if not env.message.is_expired and env.message.status == MessageStatus.PENDING
        ]

        if for_agent:
            pending = [
                env
                for env in pending
                if env.message.to_agent == for_agent
                or env.message.to_agent in ["ALL", "STRATEGISTS", "SCHOLARS"]
            ]

        return sorted(pending, key=lambda e: e.message.priority.value, reverse=True)

    def get_message_stats(self) -> dict[str, Any]:
        """메시지 통계"""
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_priority: dict[str, int] = {}

        for env in self._message_history:
            msg = env.message
            by_type[msg.message_type.value] = by_type.get(msg.message_type.value, 0) + 1
            by_status[msg.status.value] = by_status.get(msg.status.value, 0) + 1
            by_priority[msg.priority.value] = by_priority.get(msg.priority.value, 0) + 1

        return {
            "version": self.VERSION,
            "total_messages": len(self._message_history),
            "pending_messages": len(self._pending_messages),
            "by_type": by_type,
            "by_status": by_status,
            "by_priority": by_priority,
            "config": {
                "security_level": self.config.security_level.value,
                "rate_limit_enabled": self.config.rate_limit_enabled,
                "max_messages_per_minute": self.config.max_messages_per_minute,
            },
        }
