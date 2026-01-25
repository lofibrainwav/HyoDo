"""
Cross-Pillar Message Protocol for Tiger Generals (5호장군)

Standardized message format for inter-pillar communication.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class MessageType(str, Enum):
    """메시지 유형"""

    COMMAND = "command"
    STATUS = "status"
    INSIGHT = "insight"
    CONCERN = "concern"
    QUESTION = "question"
    RESPONSE = "response"
    VETO = "veto"
    ENDORSEMENT = "endorsement"


class MessagePriority(str, Enum):
    """메시지 우선순위"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CrossPillarMessage:
    """Cross-Pillar Message Protocol"""

    id: str = field(default_factory=lambda: uuid4().hex[:8])
    type: MessageType = MessageType.INSIGHT
    priority: MessagePriority = MessagePriority.MEDIUM

    # 발신/수신
    from_pillar: str = ""
    to_pillar: str = ""
    context_id: str = ""

    # 내용
    content: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    # 메타
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    ttl_seconds: float = 60.0
    processed: bool = False

    @property
    def is_expired(self) -> bool:
        """메시지 만료 여부"""
        return datetime.now().timestamp() - self.timestamp > self.ttl_seconds

    @property
    def is_broadcast(self) -> bool:
        """브로드캐스트 메시지 여부"""
        return self.to_pillar.upper() == "ALL"
