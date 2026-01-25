"""
LearningVerificationAgent 기능 테스트 (Phase Delta 검증)

眞善美孝永 - 학습 검증 에이전트 단위 테스트
"""

from unittest.mock import MagicMock

import pytest
from services.verification_engines import LearningVerificationReport

# ═══════════════════════════════════════════════════════════════════
# Mock 객체들
# ═══════════════════════════════════════════════════════════════════


def create_mock_verification_report(
    confidence: float = 0.85,
    improvement: float = 10.0,
    baseline_score: float = 70.0,
    post_score: float = 80.0,
) -> LearningVerificationReport:
    """테스트용 학습 검증 리포트 생성"""
    return LearningVerificationReport(
        session_id="LEARN_VERIFY-TEST",
        topic="Python Advanced",
        baseline_assessment={
            "trinity_score": baseline_score,
            "assessment_timestamp": "2026-01-13T12:00:00",
        },
        learning_effectiveness={
            "baseline_trinity_score": baseline_score,
            "post_trinity_score": post_score,
            "trinity_improvement": improvement,
            "success_threshold_met": improvement > 5,
            "avg_step_success_rate": 0.85,
        },
        pattern_analysis={
            "pattern_strength": "moderate",
            "consistent_improvement": True,
        },
        confidence_score=confidence,
        recommendations=["학습 접근법이 효과적임"],
    )


# ═══════════════════════════════════════════════════════════════════
# 테스트 클래스
# ═══════════════════════════════════════════════════════════════════


class TestLearningVerificationAgentCore:
    """LearningVerificationAgent 핵심 기능 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        """Mock LearningVerificationEngine"""
        engine = MagicMock()
        engine.verify_learning_session = MagicMock(return_value=create_mock_verification_report())
        return engine

    @pytest.fixture
    def mock_base_learner(self) -> None:
        """Mock IntegratedLearningSystem"""
        learner = MagicMock()
        learner.conduct_comprehensive_learning_session = MagicMock(
            return_value={
                "baseline_monitoring": {"trinity_score": 70.0},
                "final_analysis": {"trinity_score": 80.0},
                "learning_path": {"learning_path": ["material1", "material2"]},
                "execution_results": [
                    {"success": True, "step": 1},
                    {"success": True, "step": 2},
                    {"success": False, "step": 3},
                ],
            }
        )
        return learner

    def test_agent_initialization(self, mock_verification_engine, mock_base_learner) -> None:
        """LearningVerificationAgent 초기화 테스트"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        assert agent.base_learner == mock_base_learner
        assert agent.verification_engine == mock_verification_engine
        assert agent.learning_history == []
        assert agent.learning_confidence_threshold == 0.8


class TestLearningPatternAnalysis:
    """학습 패턴 분석 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.fixture
    def mock_base_learner(self) -> None:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_analyze_patterns_high_consistency(
        self, mock_verification_engine, mock_base_learner
    ):
        """높은 일관성 패턴 분석"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        base_session = {
            "execution_results": [
                {"success": True},
                {"success": True},
                {"success": True},
                {"success": True},
            ],
            "learning_path": {"learning_path": ["m1", "m2", "m3"]},
        }

        verification = create_mock_verification_report(confidence=0.92, improvement=15.0)

        patterns = await agent._analyze_learning_patterns(base_session, verification)

        assert "improvement_trajectory" in patterns
        assert any("급격한 개선" in t for t in patterns["improvement_trajectory"])
        assert any("높은 메타 인지" in m for m in patterns["meta_learning_capacity"])

    @pytest.mark.asyncio
    async def test_analyze_patterns_low_improvement(
        self, mock_verification_engine, mock_base_learner
    ):
        """낮은 개선 패턴 분석"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        base_session = {
            "execution_results": [{"success": False}, {"success": False}],
            "learning_path": {"learning_path": ["m1"]},
        }

        verification = create_mock_verification_report(confidence=0.60, improvement=2.0)

        patterns = await agent._analyze_learning_patterns(base_session, verification)

        # 약한 개선 또는 개선 부재 패턴
        trajectory_texts = " ".join(patterns["improvement_trajectory"])
        assert "약한 개선" in trajectory_texts or "개선 부재" in trajectory_texts


class TestFalseReportingDetection:
    """거짓보고 탐지 테스트 (Phase Delta 핵심)"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.fixture
    def mock_base_learner(self) -> None:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_detect_unrealistic_improvement(
        self, mock_verification_engine, mock_base_learner
    ):
        """비현실적 개선 거짓보고 탐지"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        # 거짓보고 시뮬레이션: 0점 → 100점 급상승 (비현실적)
        base_session = {
            "execution_results": [],
            "learning_path": {"learning_path": []},  # 학습 자료 없음
        }

        verification = create_mock_verification_report(
            confidence=0.99,
            improvement=80.0,
            baseline_score=10.0,  # 매우 낮은 시작
            post_score=95.0,  # 급격히 높은 끝
        )

        false_patterns = await agent._detect_false_reporting_patterns(base_session, verification)

        # 거짓보고 패턴 탐지됨
        assert "confidence_inflation" in false_patterns["detected_patterns"]
        assert len(false_patterns["confidence_manipulation"]) > 0

    @pytest.mark.asyncio
    async def test_detect_material_manipulation(self, mock_verification_engine, mock_base_learner):
        """학습 자료 조작 탐지"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        # 거짓보고: 학습 자료 없이 과도한 개선
        base_session = {
            "execution_results": [],
            "learning_path": {"learning_path": []},  # 자료 없음
        }

        verification = create_mock_verification_report(
            improvement=15.0,  # 높은 개선
            baseline_score=60.0,
            post_score=75.0,
        )

        false_patterns = await agent._detect_false_reporting_patterns(base_session, verification)

        # 패턴 조작 탐지
        assert "material_manipulation" in false_patterns["detected_patterns"]

    @pytest.mark.asyncio
    async def test_legitimate_improvement_not_flagged(
        self, mock_verification_engine, mock_base_learner
    ):
        """정상적인 개선은 거짓보고로 탐지되지 않음"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        # 정상적인 학습 세션
        base_session = {
            "execution_results": [
                {"success": True},
                {"success": True},
                {"success": False},
            ],
            "learning_path": {"learning_path": ["m1", "m2", "m3"]},
        }

        verification = create_mock_verification_report(
            improvement=8.0,  # 적당한 개선
            baseline_score=65.0,
            post_score=73.0,
        )

        false_patterns = await agent._detect_false_reporting_patterns(base_session, verification)

        # 거짓보고 패턴 없음
        assert len(false_patterns["detected_patterns"]) == 0
        assert false_patterns["risk_level"] == "low"


class TestLearningImprovements:
    """학습 개선 제안 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.fixture
    def mock_base_learner(self) -> None:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_generate_improvements_low_confidence(
        self, mock_verification_engine, mock_base_learner
    ):
        """낮은 신뢰성에 대한 개선 제안"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        verification = create_mock_verification_report(confidence=0.60)
        patterns = {
            "consistency_patterns": ["낮은 일관성: 불안정한 학습 성과"],
            "improvement_trajectory": ["약한 개선: 추가 학습 필요"],
        }
        false_reporting = {"risk_level": "low"}

        improvements = await agent._generate_learning_improvements(
            verification, patterns, false_reporting
        )

        assert len(improvements) >= 2
        # 기초 복습 제안 확인
        assert any("신뢰성 강화" in i or "기초" in i for i in improvements)

    @pytest.mark.asyncio
    async def test_generate_improvements_high_risk(
        self, mock_verification_engine, mock_base_learner
    ):
        """높은 위험에 대한 개선 제안"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        verification = create_mock_verification_report(confidence=0.85)
        patterns = {"consistency_patterns": [], "improvement_trajectory": []}
        false_reporting = {"risk_level": "high"}  # 높은 거짓보고 위험

        improvements = await agent._generate_learning_improvements(
            verification, patterns, false_reporting
        )

        # 신뢰성 검증 강화 제안 확인
        assert any("신뢰성 검증" in i or "투명성" in i for i in improvements)


class TestOverallConfidenceCalculation:
    """종합 신뢰성 점수 계산 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.fixture
    def mock_base_learner(self) -> None:
        return MagicMock()

    def test_calculate_confidence_with_bonus(self, mock_verification_engine, mock_base_learner):
        """보너스가 있는 신뢰성 계산"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        verification = create_mock_verification_report(confidence=0.80)
        patterns = {
            "consistency_patterns": ["높은 일관성"],
            "improvement_trajectory": ["급격한 개선"],
        }
        false_reporting = {"risk_level": "low"}

        confidence = agent._calculate_overall_learning_confidence(
            verification, patterns, false_reporting
        )

        # 기본 0.80 + 일관성 보너스 0.05 + 개선 보너스 0.05 = 0.90
        assert confidence > 0.80
        assert confidence <= 1.0

    def test_calculate_confidence_with_penalty(self, mock_verification_engine, mock_base_learner):
        """패널티가 있는 신뢰성 계산"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        verification = create_mock_verification_report(confidence=0.85)
        patterns = {"consistency_patterns": [], "improvement_trajectory": []}
        false_reporting = {"risk_level": "high"}  # -0.2 패널티

        confidence = agent._calculate_overall_learning_confidence(
            verification, patterns, false_reporting
        )

        # 기본 0.85 - 패널티 0.2 = 0.65
        assert confidence < 0.85
        assert confidence >= 0.0


class TestLearningVerificationAgentState:
    """LearningVerificationAgent 상태 관리 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.fixture
    def mock_base_learner(self) -> None:
        return MagicMock()

    def test_get_learning_history_empty(self, mock_verification_engine, mock_base_learner):
        """빈 학습 히스토리 조회"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        history = agent.get_learning_history()
        assert history == []

    def test_get_learning_history_with_data(self, mock_verification_engine, mock_base_learner):
        """학습 히스토리 데이터 조회"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        # 히스토리 추가
        agent.learning_history.append(create_mock_verification_report())

        history = agent.get_learning_history()

        assert len(history) == 1
        assert history[0]["session_id"] == "LEARN_VERIFY-TEST"
        assert history[0]["topic"] == "Python Advanced"

    def test_get_learning_analytics_empty(self, mock_verification_engine, mock_base_learner):
        """빈 학습 분석 조회"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        analytics = agent.get_learning_analytics()
        assert "message" in analytics

    def test_get_learning_analytics_with_data(self, mock_verification_engine, mock_base_learner):
        """학습 분석 데이터 조회"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        # 여러 검증 결과 추가
        for _ in range(3):
            agent.learning_history.append(
                create_mock_verification_report(confidence=0.85, improvement=12.0)
            )

        analytics = agent.get_learning_analytics()

        assert analytics["total_sessions"] == 3
        assert analytics["avg_confidence_score"] == pytest.approx(0.85, rel=0.01)
        assert analytics["avg_improvement"] == pytest.approx(12.0, rel=0.01)


class TestLearningVerificationAgentHealth:
    """LearningVerificationAgent 건강 상태 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.fixture
    def mock_base_learner(self) -> None:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_run_health_check_healthy(self, mock_verification_engine, mock_base_learner):
        """건강한 상태 점검"""
        from services.learning_verification_agent import LearningVerificationAgent

        agent = LearningVerificationAgent(
            base_learner=mock_base_learner,
            verification_engine=mock_verification_engine,
        )

        health = await agent.run_health_check()

        assert health["agent_status"] == "healthy"
        assert health["base_learner"] == "operational"
        assert health["verification_engine"] == "operational"
        assert health["history_size"] == 0


class TestLearningVerificationAgentFactory:
    """LearningVerificationAgent 팩토리 테스트"""

    def test_factory_create_agent(self) -> None:
        """팩토리 에이전트 생성"""
        from services.learning_verification_agent import (
            LearningVerificationAgentFactory,
        )

        # Mock을 사용하여 IntegratedLearningSystem 의존성 우회
        mock_base = MagicMock()

        agent = LearningVerificationAgentFactory.create_agent(base_learner=mock_base)

        assert agent is not None
        assert hasattr(agent, "verification_engine")
        assert hasattr(agent, "conduct_meta_learning_session")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
