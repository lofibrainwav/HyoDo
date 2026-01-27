"""Secure Agent Channel (TICKET-108)

L2 Infrastructure Layer - 실시간 채널 백플레인
SSOT: AGENTS.md

WebSocket/Queue 기반 보안 통신 채널.
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable
from uuid import uuid4

from AFO.trinity_score_sharing.domain_models import AgentType

from .protocol import (
    AgentMessagingProtocol,
    MessageAck,
    MessageEnvelope,
    MessagePriority,
    MessageStatus,
    MessageType,
    SecureChannelConfig,
)
from .security import AuthToken, MessageSecurity, SecurityContext

logger = logging.getLogger(__name__)


class ChannelBackplane(ABC):
    """채널 백플레인 추상 클래스

    다양한 메시지 전송 방식(In-Memory, Redis, WebSocket 등)을 지원하기 위한 추상화.
    """

    @abstractmethod
    async def publish(self, channel: str, message: MessageEnvelope) -> bool:
        """메시지 발행"""
        pass

    @abstractmethod
    async def subscribe(
        self,
        channel: str,
        handler: Callable[[MessageEnvelope], Any],
    ) -> str:
        """채널 구독 (subscription_id 반환)"""
        pass

    @abstractmethod
    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 취소"""
        pass

    @abstractmethod
    async def get_pending_messages(self, channel: str, limit: int = 10) -> list[MessageEnvelope]:
        """대기 중인 메시지 조회"""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """백플레인 통계"""
        pass


@dataclass
class Subscription:
    """구독 정보"""

    subscription_id: str = field(default_factory=lambda: uuid4().hex[:8])
    channel: str = ""
    handler: Callable | None = None
    created_at: float = field(default_factory=time.time)
    message_count: int = 0
    active: bool = True


class InMemoryBackplane(ChannelBackplane):
    """인메모리 채널 백플레인

    개발/테스트용 인메모리 메시지 버스.
    프로덕션에서는 Redis 또는 RabbitMQ 사용 권장.
    """

    def __init__(self, max_queue_size: int = 1000) -> None:
        self._queues: dict[str, asyncio.Queue[MessageEnvelope]] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._message_history: dict[str, list[MessageEnvelope]] = {}
        self._max_queue_size = max_queue_size
        self._max_history = 100

        # 통계
        self._stats = {
            "messages_published": 0,
            "messages_delivered": 0,
            "subscriptions_active": 0,
            "channels_active": 0,
        }

        logger.info("InMemoryBackplane initialized")

    def _ensure_channel(self, channel: str) -> asyncio.Queue[MessageEnvelope]:
        """채널 존재 확인 및 생성"""
        if channel not in self._queues:
            self._queues[channel] = asyncio.Queue(maxsize=self._max_queue_size)
            self._message_history[channel] = []
            self._stats["channels_active"] = len(self._queues)
        return self._queues[channel]

    async def publish(self, channel: str, message: MessageEnvelope) -> bool:
        """메시지 발행"""
        queue = self._ensure_channel(channel)

        try:
            queue.put_nowait(message)

            # 히스토리 저장
            self._message_history[channel].append(message)
            if len(self._message_history[channel]) > self._max_history:
                self._message_history[channel] = self._message_history[channel][
                    -self._max_history :
                ]

            self._stats["messages_published"] += 1

            # 구독자에게 알림
            await self._notify_subscribers(channel, message)

            return True

        except asyncio.QueueFull:
            logger.warning(f"Channel {channel} queue full")
            return False

    async def _notify_subscribers(self, channel: str, message: MessageEnvelope) -> None:
        """구독자들에게 알림"""
        for _, sub in self._subscriptions.items():
            if sub.channel == channel and sub.active and sub.handler:
                try:
                    if asyncio.iscoroutinefunction(sub.handler):
                        await sub.handler(message)
                    else:
                        sub.handler(message)
                    sub.message_count += 1
                    self._stats["messages_delivered"] += 1
                except Exception as e:
                    logger.error(f"Subscriber handler error: {e}")

    async def subscribe(
        self,
        channel: str,
        handler: Callable[[MessageEnvelope], Any],
    ) -> str:
        """채널 구독"""
        self._ensure_channel(channel)

        subscription = Subscription(channel=channel, handler=handler)
        self._subscriptions[subscription.subscription_id] = subscription
        self._stats["subscriptions_active"] = len(
            [s for s in self._subscriptions.values() if s.active]
        )

        logger.info(f"Subscribed to channel {channel}: {subscription.subscription_id}")
        return subscription.subscription_id

    async def unsubscribe(self, subscription_id: str) -> bool:
        """구독 취소"""
        if subscription_id in self._subscriptions:
            self._subscriptions[subscription_id].active = False
            del self._subscriptions[subscription_id]
            self._stats["subscriptions_active"] = len(
                [s for s in self._subscriptions.values() if s.active]
            )
            return True
        return False

    async def get_pending_messages(self, channel: str, limit: int = 10) -> list[MessageEnvelope]:
        """대기 중인 메시지 조회"""
        if channel not in self._queues:
            return []

        queue = self._queues[channel]
        messages = []

        while not queue.empty() and len(messages) < limit:
            try:
                message = queue.get_nowait()
                if not message.message.is_expired:
                    messages.append(message)
            except asyncio.QueueEmpty:
                break

        return messages

    def get_stats(self) -> dict[str, Any]:
        """백플레인 통계"""
        return {
            **self._stats,
            "queue_sizes": {ch: q.qsize() for ch, q in self._queues.items()},
        }


class SecureAgentChannel:
    """보안 Agent 통신 채널

    TICKET-108의 핵심 구현: 보안 채널 기반 Cross-Agent 통신.
    """

    def __init__(
        self,
        config: SecureChannelConfig | None = None,
        backplane: ChannelBackplane | None = None,
        security: MessageSecurity | None = None,
    ):
        self.config = config or SecureChannelConfig()
        self.backplane = backplane or InMemoryBackplane()
        self.security = security or MessageSecurity()
        self.protocol = AgentMessagingProtocol(self.config)

        # 채널 상태
        self._agent_channels: dict[AgentType, str] = {}
        self._agent_tokens: dict[AgentType, AuthToken] = {}
        self._agent_contexts: dict[AgentType, SecurityContext] = {}

        # 통계
        self._stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "auth_failures": 0,
        }

        logger.info(f"SecureAgentChannel initialized with config: {self.config.name}")

    async def connect_agent(
        self,
        agent_type: AgentType,
        session_id: str,
        trinity_score: float = 0.8,
        permissions: list[str] | None = None,
    ) -> tuple[AuthToken, SecurityContext]:
        """Agent 연결 및 인증

        Returns:
            (인증 토큰, 보안 컨텍스트)
        """
        # 권한 확인
        if not self.config.is_agent_allowed(agent_type):
            raise PermissionError(f"Agent {agent_type} not allowed on this channel")

        # 토큰 생성
        token = self.security.generate_token(
            agent_type=agent_type,
            session_id=session_id,
            permissions=permissions or ["message:send", "message:receive"],
            trinity_score=trinity_score,
        )

        # 보안 컨텍스트 생성
        context = self.security.create_security_context(
            agent_type=agent_type,
            session_id=session_id,
            token=token,
        )

        # 채널 이름 생성 및 저장
        channel_name = f"agent:{agent_type.value}:{session_id}"
        self._agent_channels[agent_type] = channel_name
        self._agent_tokens[agent_type] = token
        self._agent_contexts[agent_type] = context

        # 백플레인에 채널 구독
        await self.backplane.subscribe(
            channel_name,
            lambda msg: self._handle_incoming_message(agent_type, msg),
        )

        logger.info(f"Agent {agent_type.value} connected to channel {channel_name}")
        return token, context

    async def disconnect_agent(self, agent_type: AgentType) -> bool:
        """Agent 연결 해제"""
        if agent_type not in self._agent_channels:
            return False

        # 토큰 취소
        if agent_type in self._agent_tokens:
            self.security.revoke_token(self._agent_tokens[agent_type].token_id)
            del self._agent_tokens[agent_type]

        # 컨텍스트 제거
        if agent_type in self._agent_contexts:
            del self._agent_contexts[agent_type]

        # 채널 제거
        del self._agent_channels[agent_type]

        logger.info(f"Agent {agent_type.value} disconnected")
        return True

    async def send_message(
        self,
        from_agent: AgentType,
        to_agent: AgentType | str,
        message_type: MessageType,
        session_id: str,
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> tuple[MessageAck, MessageEnvelope]:
        """메시지 전송

        Returns:
            (ACK, 전송된 봉투)
        """
        # 발신자 인증 확인
        if from_agent not in self._agent_tokens:
            self._stats["auth_failures"] += 1
            raise PermissionError(f"Agent {from_agent} not authenticated")

        token = self._agent_tokens[from_agent]
        if token.is_expired:
            self._stats["auth_failures"] += 1
            raise PermissionError(f"Token for {from_agent} expired")

        # 메시지 생성
        message = self.protocol.create_message(
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            session_id=session_id,
            payload=payload,
            priority=priority,
        )

        # 봉투 생성 및 서명
        envelope = self.protocol.wrap_message(message, sender_token=token.token_value)
        if self.config.require_signature:
            envelope.sign(self.security._secret_key)

        # 검증
        is_valid, error = self.protocol.validate_envelope(envelope)
        if not is_valid:
            self._stats["messages_failed"] += 1
            return MessageAck(
                message_id=message.message_id,
                envelope_id=envelope.envelope_id,
                acknowledged_by=from_agent,
                success=False,
                error_code="VALIDATION_FAILED",
                error_message=error,
            ), envelope

        # 대상 채널 결정
        target_channels = self._resolve_target_channels(to_agent, session_id)

        # 발행
        envelope.sent_at = datetime.now()
        message.status = MessageStatus.SENT

        for channel in target_channels:
            await self.backplane.publish(channel, envelope)

        self._stats["messages_sent"] += 1

        # ACK 생성
        ack = MessageAck(
            message_id=message.message_id,
            envelope_id=envelope.envelope_id,
            acknowledged_by=from_agent,
            success=True,
        )

        return ack, envelope

    def _resolve_target_channels(
        self,
        to_agent: AgentType | str,
        session_id: str,
    ) -> list[str]:
        """대상 채널 목록 결정"""
        if to_agent == "ALL":
            return [f"agent:{agent.value}:{session_id}" for agent in AgentType]
        elif to_agent == "STRATEGISTS":
            strategists = [AgentType.JANG_YEONG_SIL, AgentType.YI_SUN_SIN, AgentType.SHIN_SAIMDANG]
            return [f"agent:{agent.value}:{session_id}" for agent in strategists]
        elif to_agent == "SCHOLARS":
            scholars = [
                AgentType.BANGTONG,
                AgentType.JARYONG,
                AgentType.YUKSON,
                AgentType.YEONGDEOK,
            ]
            return [f"agent:{agent.value}:{session_id}" for agent in scholars]
        elif isinstance(to_agent, AgentType):
            return [f"agent:{to_agent.value}:{session_id}"]
        return []

    async def _handle_incoming_message(
        self,
        agent_type: AgentType,
        envelope: MessageEnvelope,
    ) -> None:
        """수신 메시지 처리"""
        self._stats["messages_received"] += 1

        # 컨텍스트 업데이트
        if agent_type in self._agent_contexts:
            self._agent_contexts[agent_type].update_activity()

        # 프로토콜을 통해 처리
        await self.protocol.process_envelope(envelope)

    async def broadcast(
        self,
        from_agent: AgentType,
        message_type: MessageType,
        session_id: str,
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> tuple[MessageAck, MessageEnvelope]:
        """전체 브로드캐스트"""
        return await self.send_message(
            from_agent=from_agent,
            to_agent="ALL",
            message_type=message_type,
            session_id=session_id,
            payload=payload,
            priority=priority,
        )

    async def broadcast_to_strategists(
        self,
        from_agent: AgentType,
        message_type: MessageType,
        session_id: str,
        payload: dict[str, Any] | None = None,
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> tuple[MessageAck, MessageEnvelope]:
        """3책사에게 브로드캐스트"""
        return await self.send_message(
            from_agent=from_agent,
            to_agent="STRATEGISTS",
            message_type=message_type,
            session_id=session_id,
            payload=payload,
            priority=priority,
        )

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable,
    ) -> None:
        """메시지 핸들러 등록"""
        self.protocol.register_handler(message_type, handler)

    def get_stats(self) -> dict[str, Any]:
        """채널 통계"""
        return {
            "channel": {
                **self._stats,
                "connected_agents": list(self._agent_channels.keys()),
                "config": {
                    "name": self.config.name,
                    "security_level": self.config.security_level.value,
                },
            },
            "backplane": self.backplane.get_stats(),
            "security": self.security.get_security_stats(),
            "protocol": self.protocol.get_message_stats(),
        }
