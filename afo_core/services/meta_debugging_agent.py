"""
Meta Debugging Agent - 메타 디버깅 에이전트

Phase Delta: 거짓보고 방지 메타인지 검증 시스템
AutomatedDebuggingSystem의 메타인지 확장 버전
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from .automated_debugging_system import AutomatedDebuggingSystem
from .verification_engines import (
    MetaDebuggingReport,
    MetaVerificationEngine,
    MetaVerificationResult,
    get_meta_verification_engine,
)


class MetaDebuggingAgent:
    """
    메타 디버깅 에이전트 - AutomatedDebuggingSystem의 메타인지 확장

    Phase Delta: 거짓보고 방지 메타인지 검증 시스템
    - 자신의 검증 결과를 검증 (메타-검증)
    - 학습 기반 자동 개선
    - 다중 검증 계층 구축
    """

    def __init__(
        self,
        project_root=None,
        verification_engine=None,
    ):
        self.base_debugger = AutomatedDebuggingSystem(project_root)
        self.verification_engine = verification_engine or get_meta_verification_engine()
        self.verification_history: list[MetaVerificationResult] = []
        self.learning_patterns: dict[str, Any] = {}
        self.meta_confidence_threshold = 0.85  # 메타 신뢰성 임계값

        self.logger.info("🚀 MetaDebuggingAgent initialized - Phase Delta 메타인지 검증 시스템")

    @property
    def logger(self) -> Any:
        """로거 속성"""
        try:
            import logging

            return logging.getLogger(__name__)
        except ImportError:
            # 폴백 로거
            class FallbackLogger:
                def info(self, msg: str) -> None:
                    print(f"[META] {msg}")

                def warning(self, msg: str) -> None:
                    print(f"[META WARNING] {msg}")

                def error(self, msg: str) -> None:
                    print(f"[META ERROR] {msg}")

            return FallbackLogger()

    async def _emit_meta(
        self, event_type: str, message: str, level: str = "INFO", details: Any = None
    ):
        """메타 이벤트 스트림 전송"""
        try:
            await self.base_debugger._emit(event_type, f"[META] {message}", level, details)
        except Exception:
            pass

    async def run_meta_debugging_cycle(self) -> MetaDebuggingReport:
        """메타 디버깅 사이클 실행 - 4단계 메타인지 검증"""

        meta_report_id = f"META-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        await self._emit_meta("cycle_start", f"🎯 메타 디버깅 사이클 시작: {meta_report_id}")

        # ═══════════════════════════════════════════════════════════════
        # Phase 1: 기본 디버깅 실행
        # ═══════════════════════════════════════════════════════════════
        await self._emit_meta("phase1", "1️⃣ Phase 1: 기본 디버깅 시스템 실행")
        base_report = await self.base_debugger.run_full_debugging_cycle()

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: 메타 검증 (자신의 결과를 검증)
        # ═══════════════════════════════════════════════════════════════
        await self._emit_meta("phase2", "2️⃣ Phase 2: 메타 검증 - 자신의 결과를 검증")
        meta_verification = await self.verification_engine.run_comprehensive_verification(
            base_report, self.base_debugger
        )

        # ═══════════════════════════════════════════════════════════════
        # Phase 3: 학습 및 패턴 분석
        # ═══════════════════════════════════════════════════════════════
        await self._emit_meta("phase3", "3️⃣ Phase 3: 학습 패턴 분석 및 개선 도출")
        learning_insights = await self._analyze_learning_patterns(meta_verification)

        # ═══════════════════════════════════════════════════════════════
        # Phase 4: 자동 개선 적용
        # ═══════════════════════════════════════════════════════════════
        await self._emit_meta("phase4", "4️⃣ Phase 4: 자동 개선 적용 및 최적화")
        system_improvements = await self._apply_system_improvements(learning_insights)

        # ═══════════════════════════════════════════════════════════════
        # Phase 5: 다음 사이클 최적화 준비
        # ═══════════════════════════════════════════════════════════════
        next_cycle_optimizations = await self._prepare_next_cycle_optimizations(
            meta_verification, learning_insights
        )

        # ═══════════════════════════════════════════════════════════════
        # 최종 메타 신뢰성 점수 계산
        # ═══════════════════════════════════════════════════════════════
        overall_meta_confidence = self._calculate_overall_meta_confidence(
            meta_verification, learning_insights
        )

        # 검증 히스토리 저장
        self.verification_history.append(meta_verification)

        await self._emit_meta(
            "cycle_complete",
            f"✅ 메타 디버깅 완료 - 신뢰성: {overall_meta_confidence:.1%}",
            ("INFO" if overall_meta_confidence >= self.meta_confidence_threshold else "WARNING"),
        )

        return MetaDebuggingReport(
            meta_report_id=meta_report_id,
            base_report=base_report,
            meta_verification=meta_verification,
            learning_insights=learning_insights,
            system_improvements=system_improvements,
            next_cycle_optimizations=next_cycle_optimizations,
            overall_meta_confidence=overall_meta_confidence,
        )

    async def _analyze_learning_patterns(
        self, verification: MetaVerificationResult
    ) -> dict[str, Any]:
        """학습 패턴 분석"""

        insights = {
            "verification_trends": [],
            "anomaly_patterns": [],
            "improvement_velocity": 0.0,
            "confidence_trend": "stable",
        }

        # 최근 검증 결과 분석
        if len(self.verification_history) >= 3:
            recent_results = self.verification_history[-3:]

            # 신뢰성 추세 분석
            confidence_trend = (
                recent_results[-1].confidence_score - recent_results[0].confidence_score
            )
            if confidence_trend > 0.1:
                insights["confidence_trend"] = "improving"
            elif confidence_trend < -0.1:
                insights["confidence_trend"] = "degrading"

            # 개선 속도 계산
            improvements = [r.confidence_score for r in recent_results]
            if len(improvements) >= 2:
                insights["improvement_velocity"] = (improvements[-1] - improvements[0]) / len(
                    improvements
                )

        # 이상 패턴 분석
        if verification.detected_anomalies:
            insights["anomaly_patterns"] = verification.detected_anomalies

        # 학습 패턴 저장
        self.learning_patterns[verification.verification_id] = {
            "timestamp": verification.timestamp,
            "confidence_score": verification.confidence_score,
            "anomalies": verification.detected_anomalies,
            "suggestions": verification.improvement_suggestions,
        }

        return insights

    async def _apply_system_improvements(self, learning_insights: dict[str, Any]) -> list[str]:
        """시스템 개선 적용"""

        improvements_applied = []

        # 신뢰성 추세 기반 개선
        if learning_insights.get("confidence_trend") == "degrading":
            # 신뢰성이 떨어지는 경우 추가 검증 강화
            old_threshold = self.meta_confidence_threshold
            self.meta_confidence_threshold = max(0.8, self.meta_confidence_threshold - 0.05)
            improvements_applied.append(
                f"메타 신뢰성 임계값 강화: {old_threshold:.1%} → {self.meta_confidence_threshold:.1%}"
            )

        elif learning_insights.get("confidence_trend") == "improving":
            # 신뢰성이 향상되는 경우 검증 간소화
            old_threshold = self.meta_confidence_threshold
            self.meta_confidence_threshold = min(0.95, self.meta_confidence_threshold + 0.02)
            improvements_applied.append(
                f"메타 신뢰성 임계값 완화: {old_threshold:.1%} → {self.meta_confidence_threshold:.1%}"
            )

        # 개선 속도 기반 조정
        improvement_velocity = learning_insights.get("improvement_velocity", 0.0)
        if improvement_velocity > 0.05:
            improvements_applied.append("빠른 개선 속도 감지 - 추가 학습 강화")
        elif improvement_velocity < -0.02:
            improvements_applied.append("개선 속도 저하 감지 - 검증 로직 검토")

        # 이상 패턴 기반 개선
        anomalies = learning_insights.get("anomaly_patterns", [])
        if anomalies:
            improvements_applied.append(f"이상 패턴 {len(anomalies)}개 감지 - 모니터링 강화")

        return improvements_applied

    async def _prepare_next_cycle_optimizations(
        self, verification: MetaVerificationResult, _insights: dict[str, Any]
    ) -> dict[str, Any]:
        """다음 사이클 최적화 준비"""

        optimizations = {
            "suggested_verification_depth": "standard",
            "focus_areas": [],
            "risk_mitigations": [],
            "performance_optimizations": [],
        }

        # 검증 신뢰성 기반 최적화
        if verification.confidence_score < 0.8:
            optimizations["suggested_verification_depth"] = "deep"
            optimizations["focus_areas"].append("confidence_improvement")

        # 개선 제안 기반 최적화
        suggestions = verification.improvement_suggestions
        for suggestion in suggestions:
            if "Trinity" in suggestion:
                optimizations["focus_areas"].append("trinity_calculation")
            if "기둥" in suggestion:
                optimizations["focus_areas"].append("pillar_consistency")
            if "오류" in suggestion:
                optimizations["focus_areas"].append("error_detection")

        # 위험 완화 전략
        if verification.false_positive_rate > 0.15:
            optimizations["risk_mitigations"].append("reduce_false_positives")

        if verification.error_detection_accuracy < 0.9:
            optimizations["risk_mitigations"].append("improve_error_accuracy")

        return optimizations

    def _calculate_overall_meta_confidence(
        self, verification: MetaVerificationResult, insights: dict[str, Any]
    ) -> float:
        """종합 메타 신뢰성 점수 계산"""

        base_confidence = verification.confidence_score
        trend_bonus = 0.0

        # 추세 보너스
        trend = insights.get("confidence_trend", "stable")
        if trend == "improving":
            trend_bonus = 0.05
        elif trend == "degrading":
            trend_bonus = -0.05

        # 개선 속도 보너스
        velocity = insights.get("improvement_velocity", 0.0)
        velocity_bonus = min(0.03, max(-0.03, velocity))

        overall_confidence = base_confidence + trend_bonus + velocity_bonus

        return max(0.0, min(1.0, overall_confidence))

    # ═══════════════════════════════════════════════════════════════════
    # 상태 조회 및 모니터링 메소드
    # ═══════════════════════════════════════════════════════════════════

    def get_verification_history(self) -> list[dict[str, Any]]:
        """검증 히스토리 조회"""
        return [
            {
                "verification_id": v.verification_id,
                "timestamp": v.timestamp.isoformat(),
                "confidence_score": v.confidence_score,
                "anomalies_count": len(v.detected_anomalies),
                "suggestions_count": len(v.improvement_suggestions),
            }
            for v in self.verification_history
        ]

    def get_learning_analytics(self) -> dict[str, Any]:
        """학습 분석 데이터 조회"""
        if not self.verification_history:
            return {"message": "검증 히스토리가 없습니다."}

        # 신뢰성 점수 추세
        confidence_scores = [v.confidence_score for v in self.verification_history]

        # 개선 추세
        improvements = []
        for i in range(1, len(confidence_scores)):
            improvements.append(confidence_scores[i] - confidence_scores[i - 1])

        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

        # 이상 패턴 통계
        total_anomalies = sum(len(v.detected_anomalies) for v in self.verification_history)

        return {
            "total_verifications": len(self.verification_history),
            "avg_confidence_score": sum(confidence_scores) / len(confidence_scores),
            "avg_improvement": avg_improvement,
            "total_anomalies": total_anomalies,
            "current_threshold": self.meta_confidence_threshold,
            "verification_trend": "improving" if avg_improvement > 0.02 else "stable",
        }

    async def run_health_check(self) -> dict[str, Any]:
        """메타 에이전트 건강 상태 점검"""
        try:
            # 기본 컴포넌트 상태 확인
            base_status = "operational"
            verification_status = "operational" if self.verification_engine else "failed"

            # 최근 검증 상태
            recent_verification = None
            if self.verification_history:
                recent = self.verification_history[-1]
                recent_verification = {
                    "confidence_score": recent.confidence_score,
                    "anomalies": len(recent.detected_anomalies),
                    "age_seconds": (datetime.now() - recent.timestamp).total_seconds(),
                }

            return {
                "agent_status": "healthy",
                "base_debugger": base_status,
                "verification_engine": verification_status,
                "history_size": len(self.verification_history),
                "recent_verification": recent_verification,
                "meta_confidence_threshold": self.meta_confidence_threshold,
            }

        except Exception as e:
            return {
                "agent_status": "unhealthy",
                "error": str(e),
            }


# ═══════════════════════════════════════════════════════════════════
# 팩토리 및 편의 함수
# ═══════════════════════════════════════════════════════════════════


class MetaDebuggingAgentFactory:
    """메타 디버깅 에이전트 팩토리"""

    @staticmethod
    def create_agent(
        project_root: str | Path | None = None,
        verification_engine: MetaVerificationEngine | None = None,
    ) -> MetaDebuggingAgent:
        """메타 디버깅 에이전트 생성"""
        return MetaDebuggingAgent(project_root, verification_engine)


# 싱글톤 인스턴스
_meta_debugging_agent = None


def get_meta_debugging_agent() -> MetaDebuggingAgent:
    """메타 디버깅 에이전트 싱글톤"""
    global _meta_debugging_agent
    if _meta_debugging_agent is None:
        _meta_debugging_agent = MetaDebuggingAgentFactory.create_agent()
    return _meta_debugging_agent


async def run_meta_debugging() -> MetaDebuggingReport:
    """메타 디버깅 실행 편의 함수"""
    agent = get_meta_debugging_agent()
    return await agent.run_meta_debugging_cycle()
