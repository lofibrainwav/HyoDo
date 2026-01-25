"""Agent Messaging Infrastructure (TICKET-108)

L2 Infrastructure Layer - 실시간 통신/외부 감지 기반 확립
SSOT: AGENTS.md, TICKET-108

보안 채널 기반 Cross-Agent 메시징 프로토콜.
"""

from .channel import (
    ChannelBackplane,
    InMemoryBackplane,
    SecureAgentChannel,
)
from .protocol import (
    # Models
    AgentMessage,
    # Protocol
    AgentMessagingProtocol,
    MessageAck,
    MessageEnvelope,
    # Enums
    MessagePriority,
    MessageStatus,
    SecureChannelConfig,
    SecurityLevel,
)
from .security import (
    AuthToken,
    MessageSecurity,
    SecurityContext,
)

__all__ = [
    # Enums
    "MessagePriority",
    "MessageStatus",
    "SecurityLevel",
    # Models
    "AgentMessage",
    "MessageEnvelope",
    "MessageAck",
    "SecureChannelConfig",
    # Protocol
    "AgentMessagingProtocol",
    # Security
    "MessageSecurity",
    "SecurityContext",
    "AuthToken",
    # Channel
    "SecureAgentChannel",
    "ChannelBackplane",
    "InMemoryBackplane",
]
