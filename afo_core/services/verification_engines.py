"""
Verification Engines - 메타인지 검증 엔진 모음

Phase Delta: 거짓보고 방지 메타인지 검증 시스템
독립적 검증 로직들을 모듈화하여 재사용성과 유지보수성 향상
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from AFO.utils.standard_shield import shield

# ═══════════════════════════════════════════════════════════════════
# 데이터 모델 (Data Models)
# ═══════════════════════════════════════════════════════════════════


@dataclass
class MetaVerificationResult:
    """메타 검증 결과"""

    verification_id: str
    timestamp: datetime
    base_result_verified: bool
    trinity_calculation_accuracy: float  # 0.0 ~ 1.0
    pillar_score_consistency: float  # 0.0 ~ 1.0
    error_detection_accuracy: float  # 0.0 ~ 1.0
    false_positive_rate: float  # 0.0 ~ 1.0
    confidence_score: float  # 0.0 ~ 1.0
    detected_anomalies: list[str] = field(default_factory=list)
    improvement_suggestions: list[str] = field(default_factory=list)


@dataclass
class MetaDebuggingReport:
    """메타 디버깅 종합 리포트"""

    meta_report_id: str
    base_report: Any  # DebuggingReport (순환 import 방지)
    meta_verification: MetaVerificationResult
    learning_insights: dict[str, Any]
    system_improvements: list[str]
    next_cycle_optimizations: dict[str, Any]
    overall_meta_confidence: float


@dataclass
class LearningVerificationReport:
    """학습 검증 리포트"""

    session_id: str
    topic: str
    baseline_assessment: dict[str, Any]
    learning_effectiveness: dict[str, Any]
    pattern_analysis: dict[str, Any]
    confidence_score: float
    recommendations: list[str]


# ═══════════════════════════════════════════════════════════════════
# 검증 엔진 (Verification Engines)
# ═══════════════════════════════════════════════════════════════════


class TrinityVerificationEngine:
    """
    Trinity Score 검증 엔진
    SSOT 가중치 기반 정확성 검증
    """

    EXPECTED_WEIGHTS = {
        "truth": 0.35,
        "goodness": 0.35,
        "beauty": 0.20,
        "serenity": 0.08,
        "eternity": 0.02,
    }

    @shield(default_return=0.0, pillar="眞")
    async def verify_trinity_calculation(self, report: Any) -> float:
        """Trinity Score 계산 정확성 검증"""

        # 실제 계산된 점수들
        actual_scores = getattr(report, "pillar_scores", {})

        # 수동 Trinity Score 재계산
        manual_trinity = (
            actual_scores.get("truth", 0) * self.EXPECTED_WEIGHTS["truth"]
            + actual_scores.get("goodness", 0) * self.EXPECTED_WEIGHTS["goodness"]
            + actual_scores.get("beauty", 0) * self.EXPECTED_WEIGHTS["beauty"]
            + actual_scores.get("serenity", 0) * self.EXPECTED_WEIGHTS["serenity"]
            + actual_scores.get("eternity", 0) * self.EXPECTED_WEIGHTS["eternity"]
        ) / 100.0  # 백분율로 변환

        reported_trinity = getattr(report, "trinity_score", 0) / 100.0  # 백분율 → 소수점

        # 정확성 계산 (1.0 = 완벽 일치)
        accuracy = 1.0 - abs(manual_trinity - reported_trinity)

        return max(0.0, min(1.0, accuracy))


class PillarConsistencyEngine:
    """
    기둥 점수 일관성 검증 엔진
    오류 수와 점수의 상관관계 검증
    """

    PILLAR_MAPPINGS = {
        "truth": "眞_PYRIGHT",
        "beauty": "美_RUFF",
        "goodness": "善_PYTEST",
        "eternity": "永_SBOM",
    }

    @shield(default_return=0.0, pillar="眞")
    async def verify_pillar_score_consistency(self, report: Any) -> float:
        """기둥 점수 일관성 검증"""

        consistency_score = 1.0

        pillar_scores = getattr(report, "pillar_scores", {})
        errors_by_category = getattr(report, "errors_by_category", {})

        for pillar_name, error_category in self.PILLAR_MAPPINGS.items():
            pillar_score = pillar_scores.get(pillar_name, 0)
            error_count = errors_by_category.get(error_category, 0)

            # 점수가 높을수록 오류가 적어야 함 (역상관관계)
            expected_score = max(0.0, 100.0 - (error_count * 5))  # 오류 20개 = 0점

            consistency = 1.0 - abs(pillar_score - expected_score) / 100.0
            consistency_score = min(consistency_score, consistency)

        return consistency_score


class ErrorDetectionEngine:
    """
    오류 탐지 정확성 검증 엔진
    보고된 오류 vs 실제 오류 비교
    """

    async def verify_error_detection_accuracy(self, report: Any, actual_errors: int) -> float:
        """오류 탐지 정확성 검증"""

        total_reported_errors = getattr(report, "total_errors", 0)

        if actual_errors == 0:
            return 1.0 if total_reported_errors == 0 else 0.0

        # 정확성 = min(보고된 오류, 실제 오류) / max(보고된 오류, 실제 오류)
        accuracy = min(total_reported_errors, actual_errors) / max(
            total_reported_errors, actual_errors
        )

        return accuracy

    async def count_actual_errors(self, base_debugger: Any) -> int:
        """실제 오류 수 계산 (독립적 검증)"""

        error_counts = []

        # Pyright 오류 재계산
        pyright_errors = await base_debugger._run_pyright()
        error_counts.append(len(pyright_errors))

        # Ruff 오류 재계산
        ruff_errors = await base_debugger._run_ruff()
        error_counts.append(len(ruff_errors))

        # pytest 결과 재계산
        _, failed, _ = await base_debugger._run_pytest()
        error_counts.append(failed)

        # SBOM 상태 재확인
        sbom_exists = await base_debugger._check_sbom()
        error_counts.append(0 if sbom_exists else 1)

        return sum(error_counts)


class FalsePositiveAnalysisEngine:
    """
    거짓 양성률 분석 엔진
    보고된 오류의 품질 평가
    """

    async def analyze_false_positive_rate(self, report: Any) -> float:
        """거짓 양성률 분석"""

        total_reported = getattr(report, "total_errors", 0)
        if total_reported == 0:
            return 0.0

        # 보수적 추정: 보고된 오류의 10-20%는 거짓 양성일 수 있음
        estimated_false_positives = total_reported * 0.15

        return min(1.0, estimated_false_positives / total_reported)


class AnomalyDetectionEngine:
    """
    이상 징후 탐지 엔진
    검증 결과의 비정상 패턴 식별
    """

    async def detect_verification_anomalies(self, report: Any) -> list[str]:
        """검증 이상 징후 탐지"""

        anomalies = []

        trinity_score = getattr(report, "trinity_score", 0)

        # Trinity Score 비정상
        if trinity_score < 0 or trinity_score > 100:
            anomalies.append(f"Trinity Score 범위 초과: {trinity_score}")

        # 기둥 점수 합계 검증
        pillar_scores = getattr(report, "pillar_scores", {})
        total_pillar_score = sum(pillar_scores.values())
        if abs(total_pillar_score - trinity_score) > 10:
            anomalies.append(f"기둥 점수 합계 불일치: {total_pillar_score} vs {trinity_score}")

        # 오류 수와 점수의 상관관계 검증
        total_errors = getattr(report, "total_errors", 0)
        for pillar, score in pillar_scores.items():
            if pillar in ["truth", "beauty", "goodness"] and score > 80 and total_errors > 10:
                anomalies.append(f"{pillar} 점수가 높지만 오류가 많음: {score}% / {total_errors}개")

        return anomalies


class ImprovementSuggestionEngine:
    """
    개선 제안 엔진
    검증 결과를 기반으로 개선 방향 제안
    """

    async def generate_improvement_suggestions(
        self, trinity_acc: float, pillar_cons: float, error_acc: float, false_pos: float
    ) -> list[str]:
        suggestions = []

        if trinity_acc < 0.95:
            suggestions.append("Trinity Score 계산 알고리즘 개선 필요")

        if pillar_cons < 0.9:
            suggestions.append("기둥 점수와 오류 수 간 일관성 로직 개선")

        if error_acc < 0.9:
            suggestions.append("오류 탐지 정확성 향상을 위한 추가 검증 계층 도입")

        if false_pos > 0.2:
            suggestions.append("거짓 양성률 감소를 위한 필터링 로직 개선")

        if not suggestions:
            suggestions.append("현재 메타 검증 정확성이 우수함 - 유지")

        return suggestions

    def calculate_verification_confidence(
        self, trinity_acc: float, pillar_cons: float, error_acc: float, false_pos: float
    ) -> float:
        """검증 신뢰성 점수 계산"""

        # 가중치 기반 신뢰성 계산
        confidence = (
            trinity_acc * 0.4  # Trinity 계산 정확성 (40%)
            + pillar_cons * 0.3  # 기둥 일관성 (30%)
            + error_acc * 0.2  # 오류 탐지 정확성 (20%)
            + (1.0 - false_pos) * 0.1  # 거짓 음성 방지 (10%)
        )

        return confidence


# ═══════════════════════════════════════════════════════════════════
# 통합 검증 엔진 (Integrated Verification Engine)
# ═══════════════════════════════════════════════════════════════════


class MetaVerificationEngine:
    """
    메타 검증 엔진 - 모든 검증 로직 통합
    Phase Delta: 거짓보고 방지 메타인지 검증 시스템의 핵심
    """

    def __init__(self) -> None:
        self.trinity_engine = TrinityVerificationEngine()
        self.consistency_engine = PillarConsistencyEngine()
        self.error_engine = ErrorDetectionEngine()
        self.false_positive_engine = FalsePositiveAnalysisEngine()
        self.anomaly_engine = AnomalyDetectionEngine()
        self.improvement_engine = ImprovementSuggestionEngine()

    async def run_comprehensive_verification(
        self, report: Any, base_debugger: Any
    ) -> MetaVerificationResult:
        """종합 메타 검증 실행"""

        verification_id = f"VERIFY-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 1. Trinity Score 계산 검증
        trinity_accuracy = await self.trinity_engine.verify_trinity_calculation(report)

        # 2. 기둥 점수 일관성 검증
        pillar_consistency = await self.consistency_engine.verify_pillar_score_consistency(report)

        # 3. 오류 탐지 정확성 검증
        actual_errors = await self.error_engine.count_actual_errors(base_debugger)
        error_accuracy = await self.error_engine.verify_error_detection_accuracy(
            report, actual_errors
        )

        # 4. 거짓 양성률 분석
        false_positive_rate = await self.false_positive_engine.analyze_false_positive_rate(report)

        # 5. 이상 징후 탐지
        anomalies = await self.anomaly_engine.detect_verification_anomalies(report)

        # 6. 개선 제안 생성
        suggestions = await self.improvement_engine.generate_improvement_suggestions(
            trinity_accuracy, pillar_consistency, error_accuracy, false_positive_rate
        )

        # 7. 종합 신뢰성 점수 계산
        confidence_score = self.improvement_engine.calculate_verification_confidence(
            trinity_accuracy, pillar_consistency, error_accuracy, false_positive_rate
        )

        return MetaVerificationResult(
            verification_id=verification_id,
            timestamp=datetime.now(),
            base_result_verified=True,  # 기본 검증은 항상 실행됨
            trinity_calculation_accuracy=trinity_accuracy,
            pillar_score_consistency=pillar_consistency,
            error_detection_accuracy=error_accuracy,
            false_positive_rate=false_positive_rate,
            confidence_score=confidence_score,
            detected_anomalies=anomalies,
            improvement_suggestions=suggestions,
        )


# ═══════════════════════════════════════════════════════════════════
# 학습 검증 엔진 (Learning Verification Engine)
# ═══════════════════════════════════════════════════════════════════


class LearningVerificationEngine:
    """
    학습 검증 엔진
    학습 세션의 효과성과 패턴 분석
    """

    def __init__(self) -> None:
        self.verification_patterns: dict[str, Any] = {}

    async def verify_learning_session(
        self, baseline_assessment: dict, post_assessment: dict, materials_used: list
    ) -> LearningVerificationReport:
        session_id = f"LEARN_VERIFY-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 학습 효과성 분석
        effectiveness = await self._analyze_learning_effectiveness(
            baseline_assessment, post_assessment
        )

        # 패턴 분석
        patterns = await self._analyze_learning_patterns(
            materials_used, baseline_assessment, post_assessment
        )

        # 신뢰성 점수 계산
        confidence = self._calculate_learning_confidence(effectiveness, patterns)

        # 개선 제안
        recommendations = await self._generate_learning_recommendations(effectiveness, patterns)

        return LearningVerificationReport(
            session_id=session_id,
            topic=baseline_assessment.get("topic", "unknown"),
            baseline_assessment=baseline_assessment,
            learning_effectiveness=effectiveness,
            pattern_analysis=patterns,
            confidence_score=confidence,
            recommendations=recommendations,
        )

    async def _analyze_learning_effectiveness(self, baseline: dict, post: dict) -> dict[str, Any]:
        baseline_score = baseline.get("trinity_score", 0)
        post_score = post.get("trinity_score", 0)
        improvement = post_score - baseline_score

        return {
            "baseline_trinity_score": baseline_score,
            "post_trinity_score": post_score,
            "trinity_improvement": improvement,
            "improvement_rate": (improvement / max(baseline_score, 1) if baseline_score > 0 else 0),
            "success_threshold_met": improvement > 5,  # 최소 개선 임계값
        }

    async def _analyze_learning_patterns(
        self, materials: list, baseline: dict, post: dict
    ) -> dict[str, Any]:
        patterns = {
            "materials_effectiveness": len(materials) > 0,
            "consistent_improvement": False,
            "pattern_strength": "weak",
        }

        # 개선 일관성 분석
        if len(self.verification_patterns) >= 3:
            recent_improvements = [
                p.get("trinity_improvement", 0)
                for p in list(self.verification_patterns.values())[-3:]
            ]
            patterns["consistent_improvement"] = all(imp > 0 for imp in recent_improvements)

        # 패턴 강도 평가
        improvement = post.get("trinity_score", 0) - baseline.get("trinity_score", 0)
        if improvement > 15:
            patterns["pattern_strength"] = "strong"
        elif improvement > 10:
            patterns["pattern_strength"] = "moderate"

        return patterns

    def _calculate_learning_confidence(self, effectiveness: dict, patterns: dict) -> float:
        """학습 신뢰성 점수 계산"""

        score = 0.5  # 기본 점수

        # 효과성 기반 점수
        improvement = effectiveness.get("trinity_improvement", 0)
        if improvement > 15:
            score += 0.3
        elif improvement > 10:
            score += 0.2
        elif improvement > 5:
            score += 0.1

        # 패턴 기반 점수
        if patterns.get("consistent_improvement"):
            score += 0.2

        if patterns.get("pattern_strength") == "strong":
            score += 0.1
        elif patterns.get("pattern_strength") == "moderate":
            score += 0.05

        return min(1.0, score)

    async def _generate_learning_recommendations(
        self, effectiveness: dict, patterns: dict
    ) -> list[str]:
        recommendations = []

        improvement = effectiveness.get("trinity_improvement", 0)

        if improvement < 5:
            recommendations.append("학습 방법을 다양화하여 더 효과적인 접근 시도")
        elif improvement > 15:
            recommendations.append("현재 학습 방법 유지 및 강화")

        if not patterns.get("consistent_improvement"):
            recommendations.append("일관된 학습 패턴 구축을 위해 정기적 세션 유지")

        if not recommendations:
            recommendations.append("현재 학습 접근법이 효과적임 - 계속 유지")

        return recommendations


# ═══════════════════════════════════════════════════════════════════
# 팩토리 클래스 (Factory Classes)
# ═══════════════════════════════════════════════════════════════════


class VerificationEngineFactory:
    """검증 엔진 팩토리"""

    @staticmethod
    def create_meta_engine() -> MetaVerificationEngine:
        """메타 검증 엔진 생성"""
        return MetaVerificationEngine()

    @staticmethod
    def create_learning_engine() -> LearningVerificationEngine:
        """학습 검증 엔진 생성"""
        return LearningVerificationEngine()


# 싱글톤 인스턴스
_meta_engine = None
_learning_engine = None


def get_meta_verification_engine() -> MetaVerificationEngine:
    """메타 검증 엔진 싱글톤"""
    global _meta_engine
    if _meta_engine is None:
        _meta_engine = VerificationEngineFactory.create_meta_engine()
    return _meta_engine


def get_learning_verification_engine() -> LearningVerificationEngine:
    """학습 검증 엔진 싱글톤"""
    global _learning_engine
    if _learning_engine is None:
        _learning_engine = VerificationEngineFactory.create_learning_engine()
    return _learning_engine
