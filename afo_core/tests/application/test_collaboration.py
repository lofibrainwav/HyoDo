"""Tests for L3 Collaboration Hub (TICKET-107)"""

import pytest
from datetime import datetime
from uuid import uuid4

from AFO.trinity_score_sharing.domain_models import AgentType
from infrastructure.messaging.protocol import AgentMessage, MessageType, AgentMessagingProtocol
from infrastructure.messaging.channel import SecureAgentChannel, InMemoryBackplane

from application.collaboration.models import (
    CollaborationState,
    DiscussionTopic,
    VoteType,
)
from application.collaboration.voting import VotingMachine
from application.collaboration.session import CollaborationSession
from application.collaboration.hub import CollaborationHub


class TestVotingMachine:
    """투표 엔진 테스트"""

    def test_weighted_voting_consensus(self) -> None:
        vm = VotingMachine()

        # 1. Zhuge Liang (Truth) - High Score
        vm.cast_vote(AgentType.ZHUGE_LIANG, VoteType.APPROVE, trinity_score=0.9)
        # Weight ≈ 1.45

        # 2. Sima Yi (Goodness) - Moderate Score
        vm.cast_vote(AgentType.SIMA_YI, VoteType.APPROVE, trinity_score=0.7)
        # Weight ≈ 1.35

        # 3. Zhou Yu (Beauty) - Abstain
        vm.cast_vote(AgentType.ZHOU_YU, VoteType.ABSTAIN, trinity_score=0.5)

        result = vm.tally_votes()

        assert result.success is True
        assert result.decision == "APPROVED"
        assert result.approvals == 2
        assert result.abstentions == 1
        assert result.weighted_approval_rate == 1.0  # (1.45+1.35) / (1.45+1.35) = 1.0 (Abstain ignored)

    def test_voting_rejection(self) -> None:
        vm = VotingMachine()
        vm.cast_vote(AgentType.ZHUGE_LIANG, VoteType.APPROVE, trinity_score=0.5) # W=1.25
        vm.cast_vote(AgentType.SIMA_YI, VoteType.REJECT, trinity_score=0.9) # W=1.45

        result = vm.tally_votes()

        # Total = 2.7, Approve = 1.25 -> Rate = 0.46
        # Threshold 0.66 > 0.46 > 0.34 (Deadlock zone? or Fail?)
        # Logic: if rate < (1-0.66) i.e. < 0.34 -> Rejected.
        # Here 0.46 is ambiguous (DEADLOCK) in current logic
        assert result.decision == "DEADLOCK"
        assert result.success is False

    def test_veto_blocks_consensus(self) -> None:
        vm = VotingMachine()
        vm.cast_vote(AgentType.ZHUGE_LIANG, VoteType.APPROVE, trinity_score=0.9)
        vm.cast_vote(AgentType.SIMA_YI, VoteType.APPROVE, trinity_score=0.9)
        vm.cast_vote(AgentType.ZHOU_YU, VoteType.VECO, trinity_score=0.5) # VETO!

        result = vm.tally_votes()

        assert result.decision == "DEADLOCK"
        assert "Veto exercised" in result.rag_context_summary


class TestCollaborationSession:
    """세션 관리 테스트"""


class TestCollaborationHub:
    """허브 오케스트레이션 테스트"""

    async def test_hub_session_creation(self):
        backplane = InMemoryBackplane()
        protocol = AgentMessagingProtocol()
        channel = SecureAgentChannel(backplane=backplane)
        # Connect explicitly
        await channel.connect_agent(AgentType.CHANCELLOR, "test-session")

        hub = CollaborationHub(protocol, channel)

        session = await hub.create_session(
            topic_title="New Policy",
            description="Test Policy",
            initiator=AgentType.CHANCELLOR
        )

        assert session is not None
        assert session.state == CollaborationState.DISCUSSING
        assert len(hub.sessions) == 1

        # Clean up
        await channel.disconnect_agent(AgentType.CHANCELLOR)
