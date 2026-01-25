# Trinity Score: 93.0 (美 - Communication Bridge)
"""Cross-Pillar Communication Layer.

Strategist 간 메시지 패싱 및 상호 참조를 위한 통신 레이어.
각 Pillar가 독립적으로 실행되면서도 필요 시 다른 Pillar의 인사이트를 참조합니다.

AFO 철학:
- 美 (Beauty): Strategist 간 우아한 협력
- 孝 (Serenity): 조화로운 의사결정
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """메시지 유형."""

    INSIGHT = "insight"  # 인사이트 공유
    CONCERN = "concern"  # 우려 사항 전파
    QUESTION = "question"  # 다른 Pillar에 질문
    RESPONSE = "response"  # 질문에 대한 응답
    VETO = "veto"  # 거부권 행사
    ENDORSEMENT = "endorsement"  # 지지 표명


class Priority(str, Enum):
    """메시지 우선순위."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CrossPillarMessage:
    """Pillar 간 메시지."""

    id: str = field(default_factory=lambda: uuid4().hex[:8])
    type: MessageType = MessageType.INSIGHT
    priority: Priority = Priority.MEDIUM

    # 발신/수신
    from_pillar: str = ""  # TRUTH / GOODNESS / BEAUTY
    to_pillar: str = ""  # 특정 Pillar 또는 "ALL"
    context_id: str = ""  # 연관된 StrategistContext ID

    # 내용
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    # 메타
    timestamp: float = field(default_factory=time.time)
    ttl_seconds: float = 60.0  # 메시지 유효 시간
    processed: bool = False

    @property
    def is_expired(self) -> bool:
        """메시지 만료 여부."""
        return time.time() - self.timestamp > self.ttl_seconds

    @property
    def is_broadcast(self) -> bool:
        """브로드캐스트 메시지 여부."""
        return self.to_pillar.upper() == "ALL"


@dataclass
class MessageChannel:
    """Pillar별 메시지 채널."""

    pillar: str
    inbox: asyncio.Queue[CrossPillarMessage] = field(
        default_factory=lambda: asyncio.Queue(maxsize=100)
    )
    handlers: dict[MessageType, list[Callable]] = field(default_factory=dict)

    def register_handler(self, msg_type: MessageType, handler: Callable) -> None:
        """메시지 타입별 핸들러 등록."""
        if msg_type not in self.handlers:
            self.handlers[msg_type] = []
        self.handlers[msg_type].append(handler)

    async def process_message(self, message: CrossPillarMessage) -> Any:
        """메시지 처리."""
        if message.is_expired:
            logger.debug(f"Message {message.id} expired, skipping")
            return None

        handlers = self.handlers.get(message.type, [])
        results = []

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(message)
                else:
                    result = handler(message)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler error for {message.type}: {e}")

        message.processed = True
        return results


class CrossPillarBus:
    """Pillar 간 메시지 버스.

    Usage:
        bus = CrossPillarBus()

        # 채널 생성
        bus.create_channel("truth")
        bus.create_channel("goodness")
        bus.create_channel("beauty")

        # 핸들러 등록
        bus.register_handler("goodness", MessageType.CONCERN, handle_concern)

        # 메시지 발송
        await bus.send(CrossPillarMessage(
            type=MessageType.CONCERN,
            from_pillar="truth",
            to_pillar="goodness",
            content="Security pattern detected",
        ))

        # 메시지 수신 처리
        await bus.process_channel("goodness")
    """

    def __init__(self) -> None:
        """버스 초기화."""
        self._channels: dict[str, MessageChannel] = {}
        self._message_history: list[CrossPillarMessage] = []
        self._max_history = 1000

    def create_channel(self, pillar: str) -> MessageChannel:
        """Pillar용 채널 생성."""
        pillar_lower = pillar.lower()
        if pillar_lower not in self._channels:
            self._channels[pillar_lower] = MessageChannel(pillar=pillar_lower)
        return self._channels[pillar_lower]

    def get_channel(self, pillar: str) -> MessageChannel | None:
        """채널 조회."""
        return self._channels.get(pillar.lower())

    def register_handler(
        self,
        pillar: str,
        msg_type: MessageType,
        handler: Callable,
    ) -> None:
        """Pillar 채널에 핸들러 등록."""
        channel = self.get_channel(pillar)
        if channel:
            channel.register_handler(msg_type, handler)

    async def send(self, message: CrossPillarMessage) -> bool:
        """메시지 발송.

        Args:
            message: 발송할 메시지

        Returns:
            발송 성공 여부
        """
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[-self._max_history :]

        if message.is_broadcast:
            # 모든 채널에 발송 (발신자 제외)
            for pillar, channel in self._channels.items():
                if pillar != message.from_pillar.lower():
                    try:
                        channel.inbox.put_nowait(message)
                    except asyncio.QueueFull:
                        logger.warning(f"Channel {pillar} inbox full, message dropped")
            return True
        else:
            # 특정 채널에 발송
            channel = self.get_channel(message.to_pillar)
            if channel:
                try:
                    channel.inbox.put_nowait(message)
                    return True
                except asyncio.QueueFull:
                    logger.warning(f"Channel {message.to_pillar} inbox full")
                    return False
            return False

    async def process_channel(self, pillar: str, max_messages: int = 10) -> list[Any]:
        """채널의 대기 메시지 처리.

        Args:
            pillar: 처리할 Pillar
            max_messages: 최대 처리 메시지 수

        Returns:
            처리 결과 목록
        """
        channel = self.get_channel(pillar)
        if not channel:
            return []

        results = []
        processed = 0

        while not channel.inbox.empty() and processed < max_messages:
            try:
                message = channel.inbox.get_nowait()
                result = await channel.process_message(message)
                results.append(result)
                processed += 1
            except asyncio.QueueEmpty:
                break

        return results

    async def broadcast_concern(
        self,
        from_pillar: str,
        content: str,
        data: dict[str, Any] | None = None,
        priority: Priority = Priority.HIGH,
    ) -> None:
        """우려 사항 브로드캐스트 (편의 메서드)."""
        message = CrossPillarMessage(
            type=MessageType.CONCERN,
            priority=priority,
            from_pillar=from_pillar,
            to_pillar="ALL",
            content=content,
            data=data or {},
        )
        await self.send(message)
        logger.info(f"[{from_pillar}] Broadcast CONCERN: {content[:50]}...")

    async def request_endorsement(
        self,
        from_pillar: str,
        to_pillar: str,
        content: str,
        context_id: str,
    ) -> None:
        """다른 Pillar에 지지 요청."""
        message = CrossPillarMessage(
            type=MessageType.QUESTION,
            from_pillar=from_pillar,
            to_pillar=to_pillar,
            content=f"Endorsement requested: {content}",
            context_id=context_id,
        )
        await self.send(message)

    async def veto(
        self,
        from_pillar: str,
        content: str,
        context_id: str,
    ) -> None:
        """거부권 행사 (모든 Pillar에 통보)."""
        message = CrossPillarMessage(
            type=MessageType.VETO,
            priority=Priority.CRITICAL,
            from_pillar=from_pillar,
            to_pillar="ALL",
            content=content,
            context_id=context_id,
        )
        await self.send(message)
        logger.warning(f"[{from_pillar}] VETO: {content}")

    def get_recent_insights(
        self,
        for_pillar: str | None = None,
        limit: int = 10,
    ) -> list[CrossPillarMessage]:
        """최근 인사이트 조회.

        Args:
            for_pillar: 특정 Pillar용 메시지만 필터 (None이면 전체)
            limit: 최대 반환 개수

        Returns:
            최근 인사이트 메시지 목록
        """
        insights = [
            m
            for m in self._message_history
            if m.type == MessageType.INSIGHT
            and not m.is_expired
            and (for_pillar is None or m.to_pillar.lower() in ["all", for_pillar.lower()])
        ]
        return insights[-limit:]

    def get_active_concerns(self) -> list[CrossPillarMessage]:
        """활성 우려 사항 조회."""
        return [
            m
            for m in self._message_history
            if m.type == MessageType.CONCERN and not m.is_expired and not m.processed
        ]

    def get_status(self) -> dict[str, Any]:
        """버스 상태 조회."""
        return {
            "channels": list(self._channels.keys()),
            "history_size": len(self._message_history),
            "active_concerns": len(self.get_active_concerns()),
            "channel_status": {
                pillar: {
                    "inbox_size": channel.inbox.qsize(),
                    "handlers": list(channel.handlers.keys()),
                }
                for pillar, channel in self._channels.items()
            },
        }


# 싱글톤 인스턴스
_default_bus: CrossPillarBus | None = None


def get_cross_pillar_bus() -> CrossPillarBus:
    """기본 Cross-Pillar Bus 조회."""
    global _default_bus
    if _default_bus is None:
        _default_bus = CrossPillarBus()
        # 기본 채널 생성
        _default_bus.create_channel("truth")
        _default_bus.create_channel("goodness")
        _default_bus.create_channel("beauty")
    return _default_bus
