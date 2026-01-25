# Trinity Score: 95.0 (Established by Chancellor)
"""
Scholar Utilities - Collaboration, Metrics, and Auto-Optimization

학자 협업 시스템, 성능 모니터링, 자동 최적화 엔진.
model_routing.py에서 분리된 유틸리티 모듈.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "ScholarCollaboration",
    "ScholarMetrics",
    "AutoOptimizationEngine",
    "scholar_collaboration",
    "scholar_metrics",
    "auto_optimizer",
]


# ============================================================================
# Scholar Collaboration System (학자 협업 시스템)
# ============================================================================


class ScholarCollaboration:
    """학자 간 협업 및 Trinity Score 기반 메커니즘"""

    def __init__(self) -> None:
        self.scholar_expertise: dict[str, list[str]] = {
            "허준 (Heo Jun)": ["chat", "emotion", "ux", "design", "creativity", "beauty"],
            "정약용 (Jeong Yak-yong)": ["code", "backend", "algorithms", "implementation", "logic"],
            "류성룡 (Ryu Seong-ryong)": [
                "reasoning",
                "analysis",
                "review",
                "security",
                "complexity",
            ],
        }
        self.collaboration_patterns: dict[str, list[str]] = {
            "code_review": ["류성룡 (Ryu Seong-ryong)", "정약용 (Jeong Yak-yong)"],
            "complex_ui": ["허준 (Heo Jun)", "류성룡 (Ryu Seong-ryong)"],
            "full_stack": ["정약용 (Jeong Yak-yong)", "허준 (Heo Jun)", "류성룡 (Ryu Seong-ryong)"],
        }

    def get_collaboration_recommendation(
        self, primary_scholar: str, task_complexity: str, trinity_score: float
    ) -> dict[str, Any]:
        """협업 추천 생성"""
        recommendation: dict[str, Any] = {
            "primary": primary_scholar,
            "collaborators": [],
            "reasoning": "단일 학자 처리로 충분",
            "confidence": 0.8,
        }

        if task_complexity == "complex" or trinity_score < 75.0:
            if primary_scholar == "류성룡 (Ryu Seong-ryong)":
                recommendation["collaborators"] = ["정약용 (Jeong Yak-yong)"]
                recommendation["reasoning"] = "복잡한 추론 작업에 구현 전문가 협업 필요"
                recommendation["confidence"] = 0.9
            elif primary_scholar == "정약용 (Jeong Yak-yong)":
                recommendation["collaborators"] = ["류성룡 (Ryu Seong-ryong)"]
                recommendation["reasoning"] = "코드 구현에 검토 및 보안 전문가 협업 필요"
                recommendation["confidence"] = 0.85
            elif primary_scholar == "허준 (Heo Jun)" and trinity_score < 75.0:
                recommendation["collaborators"] = ["류성룡 (Ryu Seong-ryong)"]
                recommendation["reasoning"] = "UX 작업에 분석 및 검증 전문가 협업 필요"
                recommendation["confidence"] = 0.9

        return recommendation

    def get_expertise_overlap(self, scholar1: str, scholar2: str) -> list[str]:
        """두 학자의 전문성 중복 영역 반환"""
        exp1 = set(self.scholar_expertise.get(scholar1, []))
        exp2 = set(self.scholar_expertise.get(scholar2, []))
        return list(exp1 & exp2)

    def get_complementary_expertise(self, scholar1: str, scholar2: str) -> list[str]:
        """두 학자의 상호 보완적 전문성 반환"""
        exp1 = set(self.scholar_expertise.get(scholar1, []))
        exp2 = set(self.scholar_expertise.get(scholar2, []))
        return list(exp1 ^ exp2)


# ============================================================================
# Scholar Performance Monitoring (학자 성능 모니터링)
# ============================================================================


class ScholarMetrics:
    """학자 성능 메트릭 수집 및 분석"""

    def __init__(self) -> None:
        self.response_times: dict[str, list[float]] = {}
        self.response_lengths: dict[str, list[int]] = {}
        self.quality_scores: dict[str, list[float]] = {}
        self.task_counts: dict[str, int] = {}
        self.error_counts: dict[str, int] = {}

    def record_response(
        self,
        scholar: str,
        response_time: float,
        response_length: int,
        quality_score: float | None = None,
    ) -> None:
        """학자 응답 기록"""
        if scholar not in self.response_times:
            self.response_times[scholar] = []
        self.response_times[scholar].append(response_time)

        if scholar not in self.response_lengths:
            self.response_lengths[scholar] = []
        self.response_lengths[scholar].append(response_length)

        if quality_score is not None:
            if scholar not in self.quality_scores:
                self.quality_scores[scholar] = []
            self.quality_scores[scholar].append(quality_score)

        self.task_counts[scholar] = self.task_counts.get(scholar, 0) + 1

    def record_error(self, scholar: str) -> None:
        """학자 오류 기록"""
        self.error_counts[scholar] = self.error_counts.get(scholar, 0) + 1

    def get_performance_report(self, scholar: str) -> dict[str, Any]:
        """학자 성능 리포트 생성"""
        times = self.response_times.get(scholar, [])
        lengths = self.response_lengths.get(scholar, [])
        qualities = self.quality_scores.get(scholar, [])

        return {
            "scholar": scholar,
            "total_tasks": self.task_counts.get(scholar, 0),
            "error_count": self.error_counts.get(scholar, 0),
            "avg_response_time": sum(times) / len(times) if times else 0,
            "avg_response_length": sum(lengths) / len(lengths) if lengths else 0,
            "avg_quality_score": sum(qualities) / len(qualities) if qualities else None,
            "error_rate": self.error_counts.get(scholar, 0)
            / max(self.task_counts.get(scholar, 0), 1),
        }

    def get_all_scholars_report(self) -> dict[str, Any]:
        """모든 학자 성능 리포트"""
        scholars = set(self.task_counts.keys()) | set(self.error_counts.keys())
        return {scholar: self.get_performance_report(scholar) for scholar in scholars}


# ============================================================================
# Auto-Optimization System (자동 최적화 시스템)
# ============================================================================


class AutoOptimizationEngine:
    """머신러닝 기반 패턴 학습 및 자동 최적화 시스템"""

    def __init__(self) -> None:
        self.performance_history: dict[str, list[dict[str, Any]]] = {}
        self.pattern_effectiveness: dict[str, float] = {}
        self.threshold_adjustments: dict[str, list[float]] = {}
        self.learning_rate = 0.1
        self.min_samples_for_learning = 10

    def record_performance_data(
        self,
        scholar: str,
        task_type: str,
        trinity_score: float,
        response_quality: float,
        response_time: float,
        was_escalated: bool,
        final_score: float,
    ) -> None:
        """성능 데이터 기록 및 학습"""
        key = f"{scholar}_{task_type}"

        if key not in self.performance_history:
            self.performance_history[key] = []

        self.performance_history[key].append(
            {
                "trinity_score": trinity_score,
                "response_quality": response_quality,
                "response_time": response_time,
                "was_escalated": was_escalated,
                "final_score": final_score,
                "timestamp": "2026-01-22T00:32:00Z",
            }
        )

        if len(self.performance_history[key]) >= self.min_samples_for_learning:
            self._learn_patterns(key)

    def _learn_patterns(self, key: str) -> None:
        """패턴 학습 및 임계값 최적화"""
        history = self.performance_history[key]

        escalated_data = [h for h in history if h["was_escalated"]]
        non_escalated_data = [h for h in history if not h["was_escalated"]]

        if escalated_data and non_escalated_data:
            escalated_avg = sum(h["final_score"] for h in escalated_data) / len(escalated_data)
            non_escalated_avg = sum(h["final_score"] for h in non_escalated_data) / len(
                non_escalated_data
            )
            escalation_effect = escalated_avg - non_escalated_avg

            self.pattern_effectiveness[key] = escalation_effect

            if escalation_effect > 5.0:
                self._adjust_threshold(key, escalation_effect)

    def _adjust_threshold(self, key: str, effect_size: float) -> None:
        """임계값 자동 조정"""
        if key not in self.threshold_adjustments:
            self.threshold_adjustments[key] = []

        adjustment = effect_size * self.learning_rate

        if self.threshold_adjustments[key]:
            prev_adjustment = self.threshold_adjustments[key][-1]
            adjustment = (prev_adjustment + adjustment) / 2

        self.threshold_adjustments[key].append(adjustment)

    def get_optimized_threshold(self, scholar: str, task_type: str, base_threshold: float) -> float:
        """학습된 데이터를 기반으로 최적화된 임계값 반환"""
        key = f"{scholar}_{task_type}"

        if self.threshold_adjustments.get(key):
            latest_adjustment = self.threshold_adjustments[key][-1]
            optimized = base_threshold + latest_adjustment
            return max(70.0, min(95.0, optimized))

        return base_threshold

    def get_pattern_insights(self) -> dict[str, Any]:
        """패턴 분석 인사이트 제공"""
        insights: dict[str, Any] = {
            "effective_patterns": {},
            "ineffective_patterns": {},
            "threshold_adjustments": dict(self.threshold_adjustments),
            "learning_progress": {},
        }

        for key, effect in self.pattern_effectiveness.items():
            if effect > 3.0:
                insights["effective_patterns"][key] = effect
            elif effect < -1.0:
                insights["ineffective_patterns"][key] = effect

        for key in self.performance_history:
            insights["learning_progress"][key] = {
                "samples": len(self.performance_history[key]),
                "ready_for_learning": len(self.performance_history[key])
                >= self.min_samples_for_learning,
                "effectiveness": self.pattern_effectiveness.get(key, 0.0),
            }

        return insights

    def predict_optimal_strategy(
        self,
        scholar: str,
        task_type: str,
        current_trinity: float,
        task_complexity: str,
        base_threshold: float | None = None,
    ) -> dict[str, Any]:
        """최적 전략 예측

        Args:
            scholar: 학자 이름
            task_type: 작업 유형
            current_trinity: 현재 Trinity Score
            task_complexity: 작업 복잡도
            base_threshold: 기본 임계값 (None이면 90.0 사용)
        """
        key = f"{scholar}_{task_type}"
        threshold = base_threshold if base_threshold is not None else 90.0
        optimized_threshold = self.get_optimized_threshold(scholar, task_type, threshold)

        prediction: dict[str, Any] = {
            "recommended_threshold": optimized_threshold,
            "should_escalate": current_trinity < optimized_threshold,
            "confidence": min(0.9, len(self.performance_history.get(key, [])) / 20.0),
            "reasoning": "기본 임계값 사용",
        }

        if key in self.pattern_effectiveness:
            effect = self.pattern_effectiveness[key]
            if effect > 5.0:
                prediction["reasoning"] = f"학습 데이터 기반: 에스컬레이션 효과 +{effect:.1f}점"
            elif effect < -2.0:
                prediction["reasoning"] = f"학습 데이터 기반: 에스컬레이션 비효과적 {effect:.1f}점"

        if task_complexity == "complex":
            prediction["recommended_threshold"] -= 5.0
            prediction["should_escalate"] = current_trinity < prediction["recommended_threshold"]

        return prediction


# 글로벌 인스턴스
scholar_collaboration = ScholarCollaboration()
scholar_metrics = ScholarMetrics()
auto_optimizer = AutoOptimizationEngine()
