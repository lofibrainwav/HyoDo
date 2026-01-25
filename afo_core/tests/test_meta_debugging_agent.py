"""
MetaDebuggingAgent 기능 테스트 (Phase Delta 검증)

眞善美孝永 - 메타 디버깅 에이전트 단위 테스트
"""

from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from services.verification_engines import MetaVerificationResult

# ═══════════════════════════════════════════════════════════════════
# Mock 객체들
# ═══════════════════════════════════════════════════════════════════


@dataclass
class MockDebuggingReport:
    """테스트용 Mock DebuggingReport"""

    trinity_score: float = 90.0
    pillar_scores: dict = None
    total_errors: int = 5
    errors_by_category: dict = None
    report_id: str = "REPORT-TEST"

    def __post_init__(self) -> None:
        if self.pillar_scores is None:
            self.pillar_scores = {
                "truth": 95.0,
                "goodness": 90.0,
                "beauty": 85.0,
                "serenity": 80.0,
                "eternity": 100.0,
            }
        if self.errors_by_category is None:
            self.errors_by_category = {
                "眞_PYRIGHT": 2,
                "美_RUFF": 3,
                "善_PYTEST": 0,
                "永_SBOM": 0,
            }


# ═══════════════════════════════════════════════════════════════════
# 테스트 클래스
# ═══════════════════════════════════════════════════════════════════


class TestMetaDebuggingAgentCore:
    """MetaDebuggingAgent 핵심 기능 테스트"""

    @pytest.fixture
    def mock_base_debugger(self) -> None:
        """Mock AutomatedDebuggingSystem"""
        debugger = MagicMock()
        debugger.run_full_debugging_cycle = AsyncMock(return_value=MockDebuggingReport())
        debugger._emit = AsyncMock()
        debugger._run_pyright = AsyncMock(return_value=[])
        debugger._run_ruff = AsyncMock(return_value=["lint1", "lint2"])
        debugger._run_pytest = AsyncMock(return_value=(100, 5, 0))
        debugger._check_sbom = AsyncMock(return_value=True)
        return debugger

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        """Mock MetaVerificationEngine"""
        engine = MagicMock()
        engine.run_comprehensive_verification = AsyncMock(
            return_value=MetaVerificationResult(
                verification_id="VERIFY-TEST",
                timestamp=datetime.now(),
                base_result_verified=True,
                trinity_calculation_accuracy=0.95,
                pillar_score_consistency=0.90,
                error_detection_accuracy=0.85,
                false_positive_rate=0.1,
                confidence_score=0.88,
                detected_anomalies=[],
                improvement_suggestions=["현재 메타 검증 정확성이 우수함 - 유지"],
            )
        )
        return engine

    @pytest.mark.asyncio
    async def test_meta_debugging_agent_initialization(self, mock_verification_engine):
        """MetaDebuggingAgent 초기화 테스트"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            # Import here to apply patch
            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(
                project_root="/test", verification_engine=mock_verification_engine
            )

            assert agent.verification_engine == mock_verification_engine
            assert agent.verification_history == []
            assert agent.meta_confidence_threshold == 0.85

    @pytest.mark.asyncio
    async def test_analyze_learning_patterns_empty_history(self, mock_verification_engine):
        """빈 히스토리에서 학습 패턴 분석"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            verification = MetaVerificationResult(
                verification_id="VERIFY-001",
                timestamp=datetime.now(),
                base_result_verified=True,
                trinity_calculation_accuracy=0.95,
                pillar_score_consistency=0.90,
                error_detection_accuracy=0.85,
                false_positive_rate=0.1,
                confidence_score=0.88,
                detected_anomalies=["테스트 이상"],
                improvement_suggestions=[],
            )

            insights = await agent._analyze_learning_patterns(verification)

            assert "verification_trends" in insights
            assert "anomaly_patterns" in insights
            assert insights["confidence_trend"] == "stable"
            assert insights["anomaly_patterns"] == ["테스트 이상"]

    @pytest.mark.asyncio
    async def test_apply_system_improvements_degrading(self, mock_verification_engine):
        """신뢰성 하락 시 시스템 개선 테스트"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)
            agent.meta_confidence_threshold = 0.85

            insights = {
                "confidence_trend": "degrading",
                "improvement_velocity": -0.03,
                "anomaly_patterns": ["pattern1", "pattern2"],
            }

            improvements = await agent._apply_system_improvements(insights)

            # 임계값 강화 확인
            assert agent.meta_confidence_threshold <= 0.85
            assert len(improvements) >= 2  # 임계값 변경 + 속도 경고 + 패턴 경고

    @pytest.mark.asyncio
    async def test_apply_system_improvements_improving(self, mock_verification_engine):
        """신뢰성 향상 시 시스템 개선 테스트"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)
            agent.meta_confidence_threshold = 0.85

            insights = {
                "confidence_trend": "improving",
                "improvement_velocity": 0.06,
                "anomaly_patterns": [],
            }

            improvements = await agent._apply_system_improvements(insights)

            # 임계값 완화 확인
            assert agent.meta_confidence_threshold >= 0.85
            assert len(improvements) >= 1  # 최소 하나의 개선 사항

    @pytest.mark.asyncio
    async def test_prepare_next_cycle_optimizations_low_confidence(self, mock_verification_engine):
        """낮은 신뢰성 시 다음 사이클 최적화 준비"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            verification = MetaVerificationResult(
                verification_id="VERIFY-001",
                timestamp=datetime.now(),
                base_result_verified=True,
                trinity_calculation_accuracy=0.70,
                pillar_score_consistency=0.75,
                error_detection_accuracy=0.60,
                false_positive_rate=0.25,
                confidence_score=0.65,  # 낮은 신뢰성
                detected_anomalies=[],
                improvement_suggestions=[
                    "Trinity Score 계산 개선",
                    "기둥 일관성 로직 개선",
                ],
            )

            optimizations = await agent._prepare_next_cycle_optimizations(verification, {})

            assert optimizations["suggested_verification_depth"] == "deep"
            assert "confidence_improvement" in optimizations["focus_areas"]
            assert "reduce_false_positives" in optimizations["risk_mitigations"]
            assert "improve_error_accuracy" in optimizations["risk_mitigations"]

    def test_calculate_overall_meta_confidence_improving(self, mock_verification_engine):
        """향상 추세 신뢰성 점수 계산"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            verification = MetaVerificationResult(
                verification_id="VERIFY-001",
                timestamp=datetime.now(),
                base_result_verified=True,
                trinity_calculation_accuracy=0.90,
                pillar_score_consistency=0.90,
                error_detection_accuracy=0.90,
                false_positive_rate=0.1,
                confidence_score=0.85,
                detected_anomalies=[],
                improvement_suggestions=[],
            )

            insights = {
                "confidence_trend": "improving",
                "improvement_velocity": 0.04,
            }

            confidence = agent._calculate_overall_meta_confidence(verification, insights)

            # 기본 0.85 + 향상 보너스 0.05 + 속도 보너스 0.03 = 0.93
            assert confidence > 0.85
            assert confidence <= 1.0


class TestMetaDebuggingAgentState:
    """MetaDebuggingAgent 상태 관리 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    def test_get_verification_history_empty(self, mock_verification_engine) -> None:
        """빈 검증 히스토리 조회"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            history = agent.get_verification_history()
            assert history == []

    def test_get_verification_history_with_data(self, mock_verification_engine) -> None:
        """검증 히스토리 데이터 조회"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            # 히스토리 추가
            agent.verification_history.append(
                MetaVerificationResult(
                    verification_id="VERIFY-001",
                    timestamp=datetime.now(),
                    base_result_verified=True,
                    trinity_calculation_accuracy=0.95,
                    pillar_score_consistency=0.90,
                    error_detection_accuracy=0.85,
                    false_positive_rate=0.1,
                    confidence_score=0.88,
                    detected_anomalies=["anomaly1"],
                    improvement_suggestions=["suggestion1"],
                )
            )

            history = agent.get_verification_history()

            assert len(history) == 1
            assert history[0]["verification_id"] == "VERIFY-001"
            assert history[0]["confidence_score"] == 0.88
            assert history[0]["anomalies_count"] == 1
            assert history[0]["suggestions_count"] == 1

    def test_get_learning_analytics_empty(self, mock_verification_engine) -> None:
        """빈 학습 분석 조회"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            analytics = agent.get_learning_analytics()
            assert "message" in analytics

    def test_get_learning_analytics_with_data(self, mock_verification_engine) -> None:
        """학습 분석 데이터 조회"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            # 여러 검증 결과 추가
            for i, score in enumerate([0.80, 0.85, 0.90]):
                agent.verification_history.append(
                    MetaVerificationResult(
                        verification_id=f"VERIFY-{i:03d}",
                        timestamp=datetime.now(),
                        base_result_verified=True,
                        trinity_calculation_accuracy=score,
                        pillar_score_consistency=score,
                        error_detection_accuracy=score,
                        false_positive_rate=0.1,
                        confidence_score=score,
                        detected_anomalies=[],
                        improvement_suggestions=[],
                    )
                )

            analytics = agent.get_learning_analytics()

            assert analytics["total_verifications"] == 3
            assert analytics["avg_confidence_score"] == pytest.approx(0.85, rel=0.01)
            assert analytics["avg_improvement"] > 0  # 개선 추세


class TestMetaDebuggingAgentHealth:
    """MetaDebuggingAgent 건강 상태 테스트"""

    @pytest.fixture
    def mock_verification_engine(self) -> None:
        return MagicMock()

    @pytest.mark.asyncio
    async def test_run_health_check_healthy(self, mock_verification_engine):
        """건강한 상태 점검"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            health = await agent.run_health_check()

            assert health["agent_status"] == "healthy"
            assert health["base_debugger"] == "operational"
            assert health["verification_engine"] == "operational"
            assert health["history_size"] == 0

    @pytest.mark.asyncio
    async def test_run_health_check_with_recent_verification(self, mock_verification_engine):
        """최근 검증이 있는 상태 점검"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgent

            agent = MetaDebuggingAgent(verification_engine=mock_verification_engine)

            # 최근 검증 추가
            agent.verification_history.append(
                MetaVerificationResult(
                    verification_id="VERIFY-RECENT",
                    timestamp=datetime.now(),
                    base_result_verified=True,
                    trinity_calculation_accuracy=0.95,
                    pillar_score_consistency=0.90,
                    error_detection_accuracy=0.85,
                    false_positive_rate=0.1,
                    confidence_score=0.92,
                    detected_anomalies=["recent_anomaly"],
                    improvement_suggestions=[],
                )
            )

            health = await agent.run_health_check()

            assert health["agent_status"] == "healthy"
            assert health["history_size"] == 1
            assert health["recent_verification"]["confidence_score"] == 0.92
            assert health["recent_verification"]["anomalies"] == 1


class TestMetaDebuggingAgentFactory:
    """MetaDebuggingAgent 팩토리 테스트"""

    def test_factory_create_agent(self) -> None:
        """팩토리 에이전트 생성"""
        with patch("services.meta_debugging_agent.AutomatedDebuggingSystem") as MockAutoDebug:
            MockAutoDebug.return_value = MagicMock()

            from services.meta_debugging_agent import MetaDebuggingAgentFactory

            agent = MetaDebuggingAgentFactory.create_agent()

            assert agent is not None
            assert hasattr(agent, "verification_engine")
            assert hasattr(agent, "run_meta_debugging_cycle")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
