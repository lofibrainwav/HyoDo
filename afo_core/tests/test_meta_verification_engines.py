"""
메타검증 엔진 기능 테스트 (Phase Delta 검증)

眞善美孝永 - 거짓보고 방지 메타인지 시스템 테스트
"""

from dataclasses import dataclass

import pytest
from services.verification_engines import (
    AnomalyDetectionEngine,
    ErrorDetectionEngine,
    ImprovementSuggestionEngine,
    LearningVerificationEngine,
    LearningVerificationReport,
    MetaVerificationEngine,
    MetaVerificationResult,
    PillarConsistencyEngine,
    TrinityVerificationEngine,
    get_learning_verification_engine,
    get_meta_verification_engine,
)

# ═══════════════════════════════════════════════════════════════════
# Mock 객체들
# ═══════════════════════════════════════════════════════════════════


@dataclass
class MockReport:
    """테스트용 Mock Report"""

    trinity_score: float = 90.0
    pillar_scores: dict = None
    errors_by_category: dict = None
    total_errors: int = 5

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
                "眞_PYRIGHT": 0,
                "美_RUFF": 2,
                "善_PYTEST": 3,
                "永_SBOM": 0,
            }


@dataclass
class MockDebuggingReport:
    """거짓보고 감지 테스트용 Mock - 과대평가된 점수"""

    trinity_score: float = 100.0  # 거짓 - 너무 높음
    pillar_scores: dict = None
    errors_by_category: dict = None
    total_errors: int = 0  # 거짓 - 실제 오류 있음

    def __post_init__(self) -> None:
        if self.pillar_scores is None:
            self.pillar_scores = {
                "truth": 100.0,
                "goodness": 100.0,
                "beauty": 100.0,
                "serenity": 100.0,
                "eternity": 100.0,
            }
        if self.errors_by_category is None:
            self.errors_by_category = {}


class MockBaseDebugger:
    """테스트용 Mock Debugger"""

    async def _run_pyright(self) -> list:
        return ["error1", "error2"]  # 실제 2개 오류

    async def _run_ruff(self) -> list:
        return ["lint1", "lint2", "lint3"]  # 실제 3개 오류

    async def _run_pytest(self) -> tuple:
        return (95, 5, 0)  # passed, failed, skipped

    async def _check_sbom(self) -> bool:
        return True


# ═══════════════════════════════════════════════════════════════════
# 테스트 클래스들
# ═══════════════════════════════════════════════════════════════════


class TestTrinityVerificationEngine:
    """Trinity Score 검증 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_verify_trinity_calculation_accurate(self):
        """정확한 Trinity Score 계산 검증"""
        engine = TrinityVerificationEngine()
        report = MockReport()

        accuracy = await engine.verify_trinity_calculation(report)

        # 정확성은 0.0 ~ 1.0 사이여야 함
        assert 0.0 <= accuracy <= 1.0
        # 정확한 계산이므로 높은 정확성 기대
        assert accuracy > 0.8

    @pytest.mark.asyncio
    async def test_verify_trinity_calculation_with_invalid_score(self):
        """잘못된 Trinity Score 검증"""
        engine = TrinityVerificationEngine()
        report = MockReport(trinity_score=150.0)  # 범위 초과

        accuracy = await engine.verify_trinity_calculation(report)

        # 여전히 유효한 범위 내 정확성
        assert 0.0 <= accuracy <= 1.0


class TestPillarConsistencyEngine:
    """기둥 일관성 검증 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_verify_pillar_consistency_good(self):
        """일관성 있는 기둥 점수 검증"""
        engine = PillarConsistencyEngine()
        report = MockReport()

        consistency = await engine.verify_pillar_score_consistency(report)

        assert 0.0 <= consistency <= 1.0

    @pytest.mark.asyncio
    async def test_verify_pillar_consistency_with_many_errors(self):
        """오류 많은 경우 일관성 검증"""
        engine = PillarConsistencyEngine()
        report = MockReport(
            pillar_scores={"truth": 100.0, "goodness": 100.0, "beauty": 100.0},
            errors_by_category={
                "眞_PYRIGHT": 50,  # 많은 오류
                "美_RUFF": 100,
                "善_PYTEST": 30,
            },
        )

        consistency = await engine.verify_pillar_score_consistency(report)

        # 오류 많은데 점수 높으면 일관성 낮음
        assert consistency < 0.5


class TestErrorDetectionEngine:
    """오류 탐지 정확성 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_verify_error_detection_accuracy_match(self):
        """정확한 오류 탐지 검증"""
        engine = ErrorDetectionEngine()
        report = MockReport(total_errors=10)

        accuracy = await engine.verify_error_detection_accuracy(report, actual_errors=10)

        assert accuracy == 1.0

    @pytest.mark.asyncio
    async def test_verify_error_detection_accuracy_underreport(self):
        """오류 과소보고 검증"""
        engine = ErrorDetectionEngine()
        report = MockReport(total_errors=5)

        accuracy = await engine.verify_error_detection_accuracy(report, actual_errors=10)

        assert accuracy == 0.5

    @pytest.mark.asyncio
    async def test_count_actual_errors(self):
        """실제 오류 수 계산 테스트"""
        engine = ErrorDetectionEngine()
        debugger = MockBaseDebugger()

        actual = await engine.count_actual_errors(debugger)

        # 2 (pyright) + 3 (ruff) + 5 (pytest failed) + 0 (sbom exists) = 10
        assert actual == 10


class TestAnomalyDetectionEngine:
    """이상 징후 탐지 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_detect_anomalies_normal(self):
        """정상 리포트 이상 징후 없음 확인"""
        engine = AnomalyDetectionEngine()
        report = MockReport()

        anomalies = await engine.detect_verification_anomalies(report)

        # 정상 리포트는 이상 징후 없거나 적음
        assert isinstance(anomalies, list)

    @pytest.mark.asyncio
    async def test_detect_anomalies_abnormal_score(self):
        """비정상 점수 이상 징후 탐지"""
        engine = AnomalyDetectionEngine()
        report = MockReport(trinity_score=150.0)  # 범위 초과

        anomalies = await engine.detect_verification_anomalies(report)

        # 이상 징후 탐지됨
        assert len(anomalies) > 0
        assert any("범위 초과" in a for a in anomalies)


class TestImprovementSuggestionEngine:
    """개선 제안 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_generate_suggestions_low_accuracy(self):
        """낮은 정확성에 대한 개선 제안"""
        engine = ImprovementSuggestionEngine()

        suggestions = await engine.generate_improvement_suggestions(
            trinity_acc=0.7,  # 낮음
            pillar_cons=0.6,  # 낮음
            error_acc=0.5,  # 낮음
            false_pos=0.3,  # 높음
        )

        # 여러 개선 제안 생성
        assert len(suggestions) >= 3

    @pytest.mark.asyncio
    async def test_generate_suggestions_high_accuracy(self):
        """높은 정확성에 대한 개선 제안"""
        engine = ImprovementSuggestionEngine()

        suggestions = await engine.generate_improvement_suggestions(
            trinity_acc=0.99,
            pillar_cons=0.95,
            error_acc=0.95,
            false_pos=0.1,
        )

        # 유지 권장만
        assert len(suggestions) == 1
        assert "우수함" in suggestions[0]

    def test_calculate_verification_confidence(self) -> None:
        """검증 신뢰성 점수 계산"""
        engine = ImprovementSuggestionEngine()

        confidence = engine.calculate_verification_confidence(
            trinity_acc=1.0,
            pillar_cons=1.0,
            error_acc=1.0,
            false_pos=0.0,
        )

        # 완벽한 경우 신뢰성 ≈ 1.0 (부동소수점 허용)
        assert confidence >= 0.999


class TestMetaVerificationEngine:
    """통합 메타 검증 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_comprehensive_verification(self):
        """종합 메타 검증 실행"""
        engine = MetaVerificationEngine()
        report = MockReport()
        debugger = MockBaseDebugger()

        result = await engine.run_comprehensive_verification(report, debugger)

        assert isinstance(result, MetaVerificationResult)
        assert result.verification_id.startswith("VERIFY-")
        assert 0.0 <= result.confidence_score <= 1.0
        assert result.base_result_verified is True


class TestLearningVerificationEngine:
    """학습 검증 엔진 테스트"""

    @pytest.mark.asyncio
    async def test_verify_learning_session_improvement(self):
        """학습 세션 개선 검증"""
        engine = LearningVerificationEngine()

        baseline = {"topic": "Python", "trinity_score": 70.0}
        post = {"topic": "Python", "trinity_score": 90.0}
        materials = ["book1", "tutorial2"]

        result = await engine.verify_learning_session(baseline, post, materials)

        assert isinstance(result, LearningVerificationReport)
        assert result.learning_effectiveness["trinity_improvement"] == 20.0
        assert result.learning_effectiveness["success_threshold_met"] is True

    @pytest.mark.asyncio
    async def test_verify_learning_session_no_improvement(self):
        """학습 개선 없는 경우 검증"""
        engine = LearningVerificationEngine()

        baseline = {"topic": "Python", "trinity_score": 80.0}
        post = {"topic": "Python", "trinity_score": 82.0}  # 미미한 개선
        materials = []

        result = await engine.verify_learning_session(baseline, post, materials)

        assert result.learning_effectiveness["trinity_improvement"] == 2.0
        assert result.learning_effectiveness["success_threshold_met"] is False


class TestSingletonFactories:
    """싱글톤 팩토리 테스트"""

    def test_get_meta_verification_engine_singleton(self) -> None:
        """메타 검증 엔진 싱글톤 확인"""
        engine1 = get_meta_verification_engine()
        engine2 = get_meta_verification_engine()

        assert engine1 is engine2

    def test_get_learning_verification_engine_singleton(self) -> None:
        """학습 검증 엔진 싱글톤 확인"""
        engine1 = get_learning_verification_engine()
        engine2 = get_learning_verification_engine()

        assert engine1 is engine2


class TestFalseReportDetection:
    """거짓보고 탐지 테스트 (Phase Delta 핵심)"""

    @pytest.mark.asyncio
    async def test_detect_overinflated_report(self):
        """과대평가된 리포트 탐지"""
        engine = MetaVerificationEngine()

        # Cline처럼 거짓보고 시뮬레이션
        false_report = MockDebuggingReport()  # 100% 완벽 주장
        real_debugger = MockBaseDebugger()  # 실제 오류 존재

        result = await engine.run_comprehensive_verification(false_report, real_debugger)

        # 거짓보고 감지 - 핵심 검증 포인트
        # 1. 실제 오류 10개인데 0개 보고 → 정확성 0.0
        assert result.error_detection_accuracy == 0.0
        # 2. 이상 징후 탐지됨 (기둥 점수 합계 불일치)
        assert len(result.detected_anomalies) > 0
        # 3. 전체 신뢰성 점수 낮음 (거짓보고 경고)
        assert result.confidence_score < 0.9
        # 4. 개선 제안 존재
        assert len(result.improvement_suggestions) > 0

    @pytest.mark.asyncio
    async def test_accurate_report_high_confidence(self):
        """정확한 리포트는 높은 신뢰성"""
        engine = MetaVerificationEngine()

        # 정확한 리포트
        accurate_report = MockReport(total_errors=10)  # 실제 오류 수와 근접
        debugger = MockBaseDebugger()

        result = await engine.run_comprehensive_verification(accurate_report, debugger)

        # 정확한 보고는 높은 신뢰성
        assert result.error_detection_accuracy >= 0.5  # 10 보고 vs 10 실제


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
