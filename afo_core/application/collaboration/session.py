"""L3 Collaboration Session Management (TICKET-107)

Application Layer - 개별 협업 세션의 상태 및 라이프사이클 관리.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from AFO.trinity_score_sharing.domain_models import AgentType
    from infrastructure.messaging.protocol import AgentMessage


import logging
from datetime import datetime
from typing import Any

# L3 Components
from application.collaboration.models import (
    CollaborationContext,
    CollaborationState,
    DiscussionTopic,
    VoteType,
)
from application.collaboration.voting import VotingMachine

logger = logging.getLogger(__name__)


class CollaborationSession:
    """협업 세션

    하나의 주제(Topic)에 대한 토론, 투표, 합의 과정을 캡슐화.
    State Machine pattern 적용.
    """

    def __init__(
        self,
        topic: DiscussionTopic,
        required_participants: list[AgentType] | None = None,
    ) -> None:
        self.context = CollaborationContext(
            topic=topic,
            participants=required_participants or [],
        )
        self.voting_machine = VotingMachine()
        self.message_history: list[AgentMessage] = []
        self._required_participants = required_participants or []

        # Start discussion immediately
        self.transition_to(CollaborationState.DISCUSSING)
        logger.info(f"Session {self.context.session_id} started for topic '{topic.title}'")

    @property
    def session_id(self) -> UUID:
        return self.context.session_id

    @property
    def state(self) -> CollaborationState:
        return self.context.state

    def transition_to(self, new_state: CollaborationState) -> None:
        """상태 전이"""
        old_state = self.context.state
        self.context.state = new_state
        self.context.last_activity_at = datetime.now()
        logger.info(f"Session {self.session_id}: {old_state.value} -> {new_state.value}")

    def add_message(self, message: AgentMessage) -> None:
        """메시지 기록 추가"""
        self.message_history.append(message)
        self.context.last_activity_at = datetime.now()

        # 참여자 자동 등록
        if message.from_agent not in self.context.participants:
            self.context.participants.append(message.from_agent)

    def process_vote(
        self,
        agent: AgentType,
        vote_type: VoteType,
        trinity_score: float,
        reasoning: str | None,
    ) -> None:
        """투표 처리"""
        if self.state != CollaborationState.VOTING:
            logger.warning(f"Vote received in invalid state: {self.state}")
            return

        self.voting_machine.cast_vote(agent, vote_type, trinity_score, reasoning)

        # 모든 필수 참여자가 투표했으면 결과 집계 시도
        if self._check_everyone_voted():
            self._finalize_voting()

    def _check_everyone_voted(self) -> bool:
        """모든 필수 참여자의 투표 여부 확인"""
        if not self._required_participants:
            return False  # 필수 참여자가 없으면 수동 집계 대기? 일단 False

        voted_agents = set(self.voting_machine.votes.keys())
        required = set(self._required_participants)
        return required.issubset(voted_agents)

    def _finalize_voting(self) -> None:
        """투표 종료 및 결과 도출"""
        result = self.voting_machine.tally_votes(self._required_participants)
        self.context.result = result

        if result.decision in ["APPROVED", "REJECTED"]:
            self.transition_to(CollaborationState.CONSENSUS_REACHED)
            logger.info(f"Consensus Reached: {result.decision}")
        else:
            self.transition_to(CollaborationState.DEADLOCK)
            logger.warning("Session Deadlocked")

    def get_summary(self) -> dict[str, Any]:
        """세션 요약 반환"""
        return {
            "session_id": str(self.session_id),
            "topic": self.context.topic.model_dump(),
            "state": self.state.value,
            "message_count": len(self.message_history),
            "result": self.context.result.model_dump() if self.context.result else None,
            "participants": [p.value for p in self.context.participants],
        }
