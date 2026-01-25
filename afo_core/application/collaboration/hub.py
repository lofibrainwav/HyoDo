"""L3 Collaboration Hub (TICKET-107)

Application Layer - L2 Messaging 위에서 동작하는 협업 조정자(Coordinator).
"""

from __future__ import annotations

import logging
from uuid import UUID

if __import__("typing").TYPE_CHECKING:
    from infrastructure.messaging.channel import SecureAgentChannel

# Domain Models
# L3 Components
from AFO.trinity_score_sharing.domain_models import AgentType
from application.collaboration.models import DiscussionTopic, VoteType
from application.collaboration.session import CollaborationSession

# L2 Infrastructure
from infrastructure.messaging.protocol import (
    AgentMessagingProtocol,
    MessageEnvelope,
    MessagePriority,
    MessageType,
)

logger = logging.getLogger(__name__)


class CollaborationHub:
    """협업 허브 (Orchestrator)

    복수의 협업 세션을 관리하고, L2 메시지 라우팅을 담당.
    """

    def __init__(
        self,
        protocol: AgentMessagingProtocol,
        channel: SecureAgentChannel,  # Hub uses its own channel or shares one
    ) -> None:
        self.protocol = protocol
        self.channel = channel
        self.sessions: dict[UUID, CollaborationSession] = {}

        # Register Message Handlers
        self._register_handlers()
        logger.info("CollaborationHub initialized")

    def _register_handlers(self) -> None:
        """L2 메시지 핸들러 등록"""
        # Hub intercepts collaboration-related messages
        # In a real system, Hub subscribes to "COLLABORATION" topic via Backplane.
        # Here, we assume Hub checks messages addressed to 'ALL' or via Protocol hooks.
        # For simplicity, we register callbacks on the Protocol directly.

        # Binding L2 handlers
        self.protocol.register_handler(
            MessageType.COLLABORATION_REQUEST, self._handle_collaboration_request
        )
        self.protocol.register_handler(MessageType.TRINITY_SCORE_UPDATE, self._handle_vote)
        # TRINITY_SCORE_UPDATE used as vote signal (generic message handling)

    async def create_session(
        self,
        topic_title: str,
        description: str,
        initiator: AgentType,
        required_participants: list[AgentType] | None = None,
    ) -> CollaborationSession:
        """새로운 협업 세션 생성"""
        topic = DiscussionTopic(
            topic_id=f"TICKET-{len(self.sessions) + 100}",  # 임시 ID
            title=topic_title,
            description=description,
            initiator=initiator,
        )

        session = CollaborationSession(topic, required_participants)
        self.sessions[session.session_id] = session

        # Broadcast Start
        await self.channel.broadcast_to_strategists(
            from_agent=AgentType.CHANCELLOR,
            message_type=MessageType.SYSTEM_ALERT,
            session_id=str(session.session_id),
            payload={
                "event": "SESSION_STARTED",
                "session_id": str(session.session_id),
                "topic": topic_title,
            },
            priority=MessagePriority.HIGH,  # type: ignore
        )

        return session

    def get_session(self, session_id: UUID | str) -> CollaborationSession | None:
        if isinstance(session_id, str):
            try:
                session_id = UUID(session_id)
            except ValueError:
                return None
        return self.sessions.get(session_id)

    async def _handle_collaboration_request(self, envelope: MessageEnvelope) -> None:
        """협업 요청 처리 (새 세션 생성)"""
        msg = envelope.message
        payload = msg.payload

        logger.info(f"Received collaboration request from {msg.from_agent}")
        await self.create_session(
            topic_title=payload.get("title", "Untitled"),
            description=payload.get("description", ""),
            initiator=msg.from_agent,
            required_participants=payload.get("required_participants"),
        )

    async def _handle_vote(self, envelope: MessageEnvelope) -> None:
        """투표 메시지 처리 (Phase 79 - P79-004)

        Payload structure:
            session_id: str - 세션 ID
            vote_type: str - "approve", "reject", "abstain", "veco"
            trinity_score: float - 투표자의 Trinity Score (가중치)
            reasoning: str | None - 투표 사유
        """
        msg = envelope.message
        payload = msg.payload

        # Extract vote data
        session_id_str = payload.get("session_id")
        vote_type_str = payload.get("vote_type", "abstain")
        trinity_score = payload.get("trinity_score", 1.0)
        reasoning = payload.get("reasoning")

        if not session_id_str:
            logger.warning(f"Vote message missing session_id from {msg.from_agent}")
            return

        # Find session
        session = self.get_session(session_id_str)
        if not session:
            logger.warning(f"Vote for unknown session {session_id_str} from {msg.from_agent}")
            return

        # Parse vote type
        try:
            vote_type = VoteType(vote_type_str)
        except ValueError:
            logger.warning(f"Invalid vote_type '{vote_type_str}' from {msg.from_agent}")
            vote_type = VoteType.ABSTAIN

        # Process vote
        logger.info(
            f"Vote received: {msg.from_agent} -> {vote_type.value} for session {session_id_str}"
        )
        session.process_vote(
            agent=msg.from_agent,
            vote_type=vote_type,
            trinity_score=float(trinity_score),
            reasoning=reasoning,
        )

        # Broadcast vote confirmation
        await self.channel.broadcast_to_strategists(
            from_agent=AgentType.CHANCELLOR,
            message_type=MessageType.SYSTEM_ALERT,
            session_id=session_id_str,
            payload={
                "event": "VOTE_RECORDED",
                "session_id": session_id_str,
                "voter": msg.from_agent.value
                if hasattr(msg.from_agent, "value")
                else str(msg.from_agent),
                "vote_type": vote_type.value,
            },
            priority=MessagePriority.NORMAL,  # type: ignore
        )
