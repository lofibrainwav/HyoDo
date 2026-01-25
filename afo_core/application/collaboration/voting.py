"""L3 Collaboration Hub Voting Machine (TICKET-107)

Application Layer - Trinity Score 기반 가중치 투표 엔진 via Strategy Pattern.
"""

from __future__ import annotations

import logging

from AFO.trinity_score_sharing.domain_models import AgentType

# L3 Models (AgentType is runtime imported in models.py)
from application.collaboration.models import ConsensusResult, Vote, VoteType

# L3 Models

logger = logging.getLogger(__name__)


class VotingMachine:
    """투표 및 합의 엔진

    Trinity Score 가중치를 반영하여 합의 도달 여부를 판단합니다.
    """

    # 합의 필요 기준 (가중치 찬성률)
    CONSENSUS_THRESHOLD = 0.66  # 2/3 초과

    def __init__(self) -> None:
        self.votes: dict[AgentType, Vote] = {}

    def cast_vote(
        self,
        agent: AgentType,
        vote_type: VoteType,
        trinity_score: float,
        reasoning: str | None = None,
    ) -> Vote:
        """투표 행사"""

        # 가중치 계산 (기본 1.0 + Trinity Score 보정)
        # 예: Trinity 0.9 -> Weight 1.45 (0.9 * 0.5 + 1.0)
        # 예: Trinity 0.5 -> Weight 1.25
        # 전략가는 기본 1.2 가중치 부여 가능 (여기서는 단순화하여 Trinity Score 비례)
        weight = 1.0 + (trinity_score * 0.5)

        vote = Vote(
            agent=agent,
            vote_type=vote_type,
            weight=weight,
            reasoning=reasoning,
        )
        self.votes[agent] = vote
        logger.info(f"Vote cast by {agent.value}: {vote_type.value} (Weight: {weight:.2f})")
        return vote

    def tally_votes(self, required_participants: list[AgentType] | None = None) -> ConsensusResult:
        """투표 집계 및 결과 도출"""

        # 정족수 확인 (Quorum Check)
        if required_participants:
            missing = [agent for agent in required_participants if agent not in self.votes]
            if missing:
                logger.warning(f"Quorum not met. Missing: {missing}")
                return self._create_deadlock_result(f"Quorum not met. Missing: {missing}")

        total_weight = 0.0
        approval_weight = 0.0
        rejection_weight = 0.0

        approvals = 0
        rejections = 0
        abstentions = 0
        vecos = 0

        for vote in self.votes.values():
            if vote.vote_type == VoteType.APPROVE:
                approvals += 1
                approval_weight += vote.weight
                total_weight += vote.weight
            elif vote.vote_type == VoteType.REJECT:
                rejections += 1
                rejection_weight += vote.weight
                total_weight += vote.weight
            elif vote.vote_type == VoteType.VECO:
                vecos += 1
                # Veto is a strong rejection
                rejection_weight += vote.weight * 1.5  # Veto 가중치 1.5배 패널티
                total_weight += vote.weight * 1.5
                # VETO prevents consensus immediately?
                # 전략: VETO가 있으면 무조건 DEADLOCK 처리하거나, 반대 가중치를 높임.
                # 여기서는 가중치를 높이는 방식 + DEADLOCK 플래그 사용
            elif vote.vote_type == VoteType.ABSTAIN:
                abstentions += 1
                # 기권은 총 가중치에 포함하지 않음 (의사표시 제외)

        # VETO 발생 시 즉시 DEADLOCK
        if vecos > 0:
            logger.info("VETO detected. Consensus blocked.")
            return self._create_deadlock_result(f"Veto exercised by {vecos} agents")

        if total_weight == 0:
            return self._create_deadlock_result("No valid votes cast")

        weighted_approval_rate = approval_weight / total_weight

        # 결정 로직
        if weighted_approval_rate > self.CONSENSUS_THRESHOLD:
            decision = "APPROVED"
            success = True
        elif weighted_approval_rate < (1.0 - self.CONSENSUS_THRESHOLD):
            # 확실한 거부 (찬성률 < 0.34)
            decision = "REJECTED"
            success = True  # "거부"라는 결론에 도달함 (합의된 거부)
        else:
            decision = "DEADLOCK"  # 애매한 상태
            success = False

        return ConsensusResult(
            success=success,
            approvals=approvals,
            rejections=rejections,
            abstentions=abstentions,
            weighted_approval_rate=weighted_approval_rate,
            decision=decision,
            rag_context_summary=f"Approvals: {approvals}, Rejections: {rejections}, Veto: {vecos}",
        )

    def _create_deadlock_result(self, reason: str) -> ConsensusResult:
        return ConsensusResult(
            success=False,
            approvals=0,
            rejections=0,
            abstentions=0,
            weighted_approval_rate=0.0,
            decision="DEADLOCK",
            rag_context_summary=reason,
        )

    def reset(self) -> None:
        """투표 초기화"""
        self.votes.clear()
