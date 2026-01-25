"""
Event-Driven Message Bus for Tiger Generals (5호장군)

Implements Pub/Sub pattern for asynchronous communication between Tiger Generals.
Handles message routing, registration, and broadcasting.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .message_protocol import CrossPillarMessage

logger = logging.getLogger(__name__)


class MessageHandler(Protocol):
    """Message handler protocol"""

    async def handle(self, message: CrossPillarMessage) -> Any:
        """Handle incoming message"""
        pass


class MessageChannel:
    """Message channel for each Tiger General"""

    def __init__(self, general_name: str) -> None:
        self.general_name = general_name
        self.inbox: asyncio.Queue[Any] = asyncio.Queue(maxsize=100)
        self.handlers: dict[str, list[MessageHandler]] = {}

    def register_handler(self, message_type: str, handler: MessageHandler) -> None:
        """Register message handler"""
        if message_type not in self.handlers:
            self.handlers[message_type] = []
        self.handlers[message_type].append(handler)
        logger.debug(f"Registered handler for {self.general_name}.{message_type}")

    async def process_message(self, message: CrossPillarMessage) -> list[Any]:
        """Process incoming message"""
        if message.is_expired:
            logger.debug(f"Message {message.id} expired, skipping")
            return []

        handlers = self.handlers.get(message.type.value, [])
        results = []

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler.handle):
                    result = await handler.handle(message)
                else:
                    result = handler.handle(message)
                results.append(result)
            except Exception as e:
                logger.error(f"Handler error in {self.general_name}: {e}")

        message.processed = True
        return results


class TigerGeneralsEventBus:
    """Event-driven message bus for Tiger Generals"""

    def __init__(self) -> None:
        """Initialize event bus"""
        self.channels: dict[str, MessageChannel] = {}
        self.event_log: list[dict[str, Any]] = []
        self.max_log_size = 1000

    async def create_channel(self, general_name: str) -> MessageChannel:
        """Create message channel for Tiger General"""
        if general_name not in self.channels:
            self.channels[general_name] = MessageChannel(general_name)
            logger.info(f"Created channel for {general_name}")
        return self.channels[general_name]

    async def register_handler(
        self, general_name: str, message_type: str, handler: MessageHandler
    ) -> None:
        """Register message handler"""
        channel = await self.get_channel(general_name)
        if channel:
            channel.register_handler(message_type, handler)
            logger.info(f"Registered handler for {general_name}.{message_type}")

    async def publish(
        self,
        source: str,
        target: str | None,
        message_type: str,
        content: str,
        data: dict[str, Any] | None,
        priority: str = "MEDIUM",
    ) -> bool:
        """Publish message to event bus"""
        from .message_protocol import CrossPillarMessage, MessagePriority, MessageType

        message = CrossPillarMessage(
            type=MessageType(message_type),
            priority=MessagePriority(priority.lower()) if isinstance(priority, str) else priority,
            from_pillar=source,
            to_pillar=target or "",
            context_id=data.get("context_id", "") if data else "",
            content=content,
            data=data or {},
            ttl_seconds=60.0,
        )

        self.event_log.append(
            {
                "message_id": message.id,
                "type": message_type,
                "source": source,
                "target": target,
                "timestamp": datetime.fromtimestamp(message.timestamp).isoformat(),
                "content": content,
            }
        )

        if len(self.event_log) > self.max_log_size:
            self.event_log = self.event_log[-self.max_log_size :]

        if target and target != "ALL":
            return await self._send_to_channel(target, message)
        elif target == "ALL":
            await self._broadcast_to_all_channels(source, message)

        return False

    async def _send_to_channel(self, general_name: str, message: CrossPillarMessage) -> bool:
        """Send message to specific channel"""
        channel = self.channels.get(general_name)
        if not channel:
            logger.warning(f"No channel for {general_name}")
            return False

        try:
            channel.inbox.put_nowait(message)
            return True
        except asyncio.QueueFull:
            logger.error(f"Channel {general_name} inbox full, message dropped")
            return False

    async def _broadcast_to_all_channels(self, source: str, message: CrossPillarMessage) -> None:
        """Broadcast message to all channels (except sender)"""
        for general_name, channel in self.channels.items():
            if general_name != source:
                try:
                    channel.inbox.put_nowait(message)
                except asyncio.QueueFull:
                    logger.error(f"Channel {general_name} inbox full")

    async def get_channel(self, general_name: str) -> MessageChannel | None:
        """Get channel for specific general"""
        return self.channels.get(general_name)

    async def process_concern(self, source: str, content: str, data: dict[str, Any]) -> None:
        """Process concern"""
        await self.publish(
            source=source,
            target="ALL",
            message_type="CONCERN",
            content=content,
            data=data,
            priority="HIGH",
        )
        logger.info(f"Concern from {source}: {content[:50]}...")

    async def request_endorsement(
        self, source: str, target: str, content: str, context_id: str
    ) -> None:
        """Request endorsement"""
        await self.publish(
            source=source,
            target=target,
            message_type="QUESTION",
            content=f"Endorsement requested: {content}",
            data={"context_id": context_id},
            priority="HIGH",
        )

    async def veto(self, source: str, content: str, context_id: str) -> None:
        """Veto"""
        await self.publish(
            source=source,
            target="ALL",
            message_type="VETO",
            content=content,
            data={"context_id": context_id},
            priority="CRITICAL",
        )
        logger.warning(f"VETO from {source}: {content}")

    def get_recent_insights(
        self, for_general: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent insights"""
        insights = [
            e
            for e in self.event_log
            if e.get("type") == "INSIGHT"
            and not e.get("expired", False)
            and (for_general is None or e.get("target") in ["ALL", for_general])
        ]
        return insights[-limit:]

    def get_active_concerns(self) -> list[dict[str, Any]]:
        """Get active concerns"""
        return [
            e
            for e in self.event_log
            if e.get("type") == "CONCERN" and not e.get("processed", False)
        ]

    def get_status(self) -> dict[str, Any]:
        """Get event bus status"""
        return {
            "channels": list(self.channels.keys()),
            "history_size": len(self.event_log),
            "active_concerns": len(self.get_active_concerns()),
            "channel_status": {
                pillar: {
                    "inbox_size": channel.inbox.qsize(),
                    "handlers": list(channel.handlers.keys()),
                }
                for pillar, channel in self.channels.items()
            },
        }
