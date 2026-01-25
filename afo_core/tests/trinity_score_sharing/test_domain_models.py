"""Tests for Trinity Score Sharing Domain Models (TICKET-109)

L1 Domain Layer 도메인 모델 단위 테스트.
SSOT: TRINITY_OS_PERSONAS.yaml, domain/metrics/trinity_ssot.py
"""

from math import isclose
from uuid import UUID

import pytest

from AFO.trinity_score_sharing.domain_models import (
    WEIGHT_BEAUTY,
    WEIGHT_ETERNITY,
    WEIGHT_GOODNESS,
    WEIGHT_SERENITY,
    # Constants
    WEIGHT_TRUTH,
    AgentScoreEntry,
    # Enums
    AgentType,
    BalanceStatus,
    # Events & Metrics
    CollaborationFeedback,
    OptimizationPolicy,
    OptimizationStrategy,
    # Core Models
    PillarScores,
    # Policies
    SharingPolicy,
    TrinityScorePool,
    # Contract
    TrinityScoreSharingContract,
)


class TestPillarScores:
    """PillarScores 테스트"""

    def test_create_perfect_scores(self) -> None:
        """완벽한 점수 생성"""
        scores = PillarScores(
            truth=1.0,
            goodness=1.0,
            beauty=1.0,
            serenity=1.0,
            eternity=1.0,
        )
        assert isclose(scores.trinity_score, 1.0, rel_tol=1e-9)
        assert isclose(scores.trinity_score_100, 100.0, rel_tol=1e-9)
        assert scores.balance_delta == 0.0
        assert scores.balance_status == BalanceStatus.BALANCED

    def test_ssot_weights(self) -> None:
        """SSOT 가중치 검증 (0.35 + 0.35 + 0.20 + 0.08 + 0.02 = 1.0)"""
        total_weight = (
            WEIGHT_TRUTH + WEIGHT_GOODNESS + WEIGHT_BEAUTY + WEIGHT_SERENITY + WEIGHT_ETERNITY
        )
        assert isclose(total_weight, 1.0, rel_tol=1e-9)

    def test_trinity_score_calculation(self) -> None:
        """Trinity Score 계산 검증"""
        scores = PillarScores(
            truth=0.9,
            goodness=0.8,
            beauty=0.7,
            serenity=0.6,
            eternity=0.5,
        )
        # 0.35×0.9 + 0.35×0.8 + 0.20×0.7 + 0.08×0.6 + 0.02×0.5
        # = 0.315 + 0.28 + 0.14 + 0.048 + 0.01 = 0.793
        expected = 0.35 * 0.9 + 0.35 * 0.8 + 0.20 * 0.7 + 0.08 * 0.6 + 0.02 * 0.5
        assert abs(scores.trinity_score - expected) < 0.001

    def test_balance_status_balanced(self) -> None:
        """균형 상태 - balanced (delta < 0.1)"""
        # 모든 값이 0.05 범위 내에 있어야 BALANCED
        scores = PillarScores(truth=0.95, goodness=0.92, beauty=0.90, serenity=0.88, eternity=0.87)
        assert scores.balance_delta < 0.1
        assert scores.balance_status == BalanceStatus.BALANCED

    def test_balance_status_warning(self) -> None:
        """균형 상태 - warning (0.1 <= delta < 0.3)"""
        scores = PillarScores(truth=0.9, goodness=0.85, beauty=0.8, serenity=0.78, eternity=0.75)
        assert 0.1 <= scores.balance_delta < 0.3
        assert scores.balance_status == BalanceStatus.WARNING

    def test_balance_status_imbalanced(self) -> None:
        """균형 상태 - imbalanced"""
        scores = PillarScores(truth=1.0, goodness=0.9, beauty=0.5, serenity=0.6, eternity=0.4)
        assert scores.balance_delta == 0.6
        assert scores.balance_status == BalanceStatus.IMBALANCED


class TestAgentScoreEntry:
    """AgentScoreEntry 테스트"""

    def test_create_entry(self) -> None:
        """Agent 점수 엔트리 생성"""
        entry = AgentScoreEntry(
            agent_id="test-agent-123",
            agent_type=AgentType.ASSOCIATE,
            pillar_scores=PillarScores(
                truth=0.9, goodness=0.85, beauty=0.8, serenity=0.9, eternity=0.95
            ),
        )
        assert entry.agent_type == AgentType.ASSOCIATE
        assert entry.agent_id == "test-agent-123"
        assert entry.trinity_score > 0.8

    def test_weighted_contribution(self) -> None:
        """가중 기여도 계산"""
        entry = AgentScoreEntry(
            agent_id="test-manager",
            agent_type=AgentType.MANAGER,
            pillar_scores=PillarScores(
                truth=0.9, goodness=0.9, beauty=0.9, serenity=0.9, eternity=0.9
            ),
            confidence=0.9,
            contribution_weight=0.8,
        )
        # weighted_contribution = confidence × contribution_weight × trinity_score
        expected = 0.9 * 0.8 * entry.trinity_score
        assert abs(entry.weighted_contribution - expected) < 0.001


class TestTrinityScorePool:
    """TrinityScorePool 테스트"""

    def test_create_empty_pool(self) -> None:
        """빈 풀 생성"""
        pool = TrinityScorePool(pool_id="pool-1", session_id="test-session")
        assert pool.agent_count == 0
        assert pool.average_trinity_score == 0.0
        assert not pool.should_optimize()

    def test_add_agents_to_pool(self) -> None:
        """풀에 Agent 추가"""
        entry1 = AgentScoreEntry(
            agent_id="associate-1",
            agent_type=AgentType.ASSOCIATE,
            pillar_scores=PillarScores(
                truth=0.9, goodness=0.9, beauty=0.9, serenity=0.9, eternity=0.9
            ),
        )
        entry2 = AgentScoreEntry(
            agent_id="manager-1",
            agent_type=AgentType.MANAGER,
            pillar_scores=PillarScores(
                truth=0.8, goodness=0.8, beauty=0.8, serenity=0.8, eternity=0.8
            ),
        )
        pool = TrinityScorePool(
            pool_id="pool-1", session_id="test-session", entries=[entry1, entry2]
        )

        assert pool.agent_count == 2
        assert pool.average_trinity_score > 0.8

    def test_governance_decision_auto_run(self) -> None:
        """거버넌스 결정 - AUTO_RUN"""
        # 높은 점수 (Trinity >= 90, Risk <= 10)
        entry = AgentScoreEntry(
            agent_id="auditor-1",
            agent_type=AgentType.AUDITOR,
            pillar_scores=PillarScores(
                truth=0.95, goodness=0.95, beauty=0.9, serenity=0.9, eternity=0.9
            ),
            confidence=0.95,
        )
        pool = TrinityScorePool(pool_id="pool-1", session_id="test", entries=[entry])

        assert pool.get_governance_decision() == "AUTO_RUN"

    def test_governance_decision_ask_commander(self) -> None:
        """거버넌스 결정 - ASK_COMMANDER"""
        # 낮은 점수
        entry = AgentScoreEntry(
            agent_id="associate-low",
            agent_type=AgentType.ASSOCIATE,
            pillar_scores=PillarScores(
                truth=0.7, goodness=0.7, beauty=0.7, serenity=0.7, eternity=0.7
            ),
            confidence=0.6,
        )
        pool = TrinityScorePool(pool_id="pool-1", session_id="test", entries=[entry])

        assert pool.get_governance_decision() == "ASK_COMMANDER"

    def test_should_optimize_with_high_variance(self) -> None:
        """높은 분산 시 최적화 필요"""
        # 매우 큰 점수 차이 (1.0 vs 0.0 = variance 0.25)
        entry1 = AgentScoreEntry(
            agent_id="associate-high",
            agent_type=AgentType.ASSOCIATE,
            pillar_scores=PillarScores(
                truth=1.0, goodness=1.0, beauty=1.0, serenity=1.0, eternity=1.0
            ),
        )
        entry2 = AgentScoreEntry(
            agent_id="manager-low",
            agent_type=AgentType.MANAGER,
            pillar_scores=PillarScores(
                truth=0.0, goodness=0.0, beauty=0.0, serenity=0.0, eternity=0.0
            ),
        )
        pool = TrinityScorePool(
            pool_id="pool-1", session_id="test", entries=[entry1, entry2], auto_optimize=True
        )

        # variance = ((1.0 - 0.5)^2 + (0.0 - 0.5)^2) / 2 = 0.25
        assert pool.score_variance >= 0.2
        assert pool.should_optimize()


class TestPolicies:
    """SharingPolicy, OptimizationPolicy 테스트"""

    def test_sharing_policy_creation(self) -> None:
        """공유 정책 생성"""
        policy = SharingPolicy(
            policy_id="sharing-1",
            is_public=True,
            allowed_agents=[AgentType.ASSOCIATE, AgentType.MANAGER],
        )
        assert policy.policy_id == "sharing-1"
        assert policy.is_public is True

    def test_optimization_policy_creation(self) -> None:
        """최적화 정책 생성"""
        policy = OptimizationPolicy(
            policy_id="opt-1", strategy=OptimizationStrategy.ADAPTIVE, min_score_threshold=0.8
        )
        assert policy.strategy == OptimizationStrategy.ADAPTIVE
        assert policy.min_score_threshold == 0.8


class TestCollaborationFeedback:
    """CollaborationFeedback 테스트"""

    def test_create_feedback(self) -> None:
        """피드백 생성"""
        feedback = CollaborationFeedback(
            session_id="test",
            from_agent="associate-1",
            to_agent="manager-1",
            rating=0.9,
            comment="Excellent collaboration",
        )
        assert feedback.rating == 0.9
        assert feedback.comment == "Excellent collaboration"
        assert feedback.from_agent == "associate-1"


class TestTrinityScoreSharingContract:
    """TrinityScoreSharingContract 테스트"""

    def test_contract_creation(self) -> None:
        """계약 생성"""
        sharing_policy = SharingPolicy(policy_id="sp-1")
        opt_policy = OptimizationPolicy(policy_id="opt-1", strategy=OptimizationStrategy.ADAPTIVE)
        contract = TrinityScoreSharingContract(
            session_id="test-session",
            parties=["agent-1", "agent-2"],
            sharing_policy=sharing_policy,
            optimization_policy=opt_policy,
        )
        assert contract.session_id == "test-session"
        assert len(contract.parties) == 2
