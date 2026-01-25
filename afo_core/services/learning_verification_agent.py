"""
Learning Verification Agent - 학습 검증 에이전트

Phase Delta: 거짓보고 방지 메타인지 검증 시스템
IntegratedLearningSystem의 메타인지 확장 버전
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .integrated_learning_system import IntegratedLearningSystem
from .verification_engines import (
    LearningVerificationEngine,
    LearningVerificationReport,
    get_learning_verification_engine,
)


class LearningVerificationAgent:
    """
    학습 검증 에이전트 - IntegratedLearningSystem의 메타인지 확장

    Phase Delta: 거짓보고 방지 메타인지 검증 시스템
    - 학습 세션의 효과성과 진정성을 검증
    - 학습 패턴 분석 및 메타-평가
    - 거짓보고 패턴 탐지 및 방지
    """

    def __init__(
        self,
        base_learner=None,
        verification_engine=None,
    ):
        self.base_learner = base_learner or IntegratedLearningSystem()
        self.verification_engine = verification_engine or get_learning_verification_engine()
        self.learning_history: list[LearningVerificationReport] = []
        self.verification_patterns: dict[str, Any] = {}
        self.learning_confidence_threshold = 0.8  # 학습 신뢰성 임계값

        self.logger.info("🚀 LearningVerificationAgent initialized - Phase Delta 학습 검증 시스템")

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
                    print(f"[LEARN_VERIFY] {msg}")

                def warning(self, msg: str) -> None:
                    print(f"[LEARN_VERIFY WARNING] {msg}")

                def error(self, msg: str) -> None:
                    print(f"[LEARN_VERIFY ERROR] {msg}")

            return FallbackLogger()

    async def _emit_learning_event(
        self, event_type: str, message: str, level: str = "INFO", details: Any = None
    ):
        """학습 이벤트 스트림 전송"""
        try:
            event = {
                "source": "LEARNING_VERIFICATION_AGENT",
                "type": f"learning_{event_type}",
                "message": message,
                "level": level,
                "details": details,
                "timestamp": datetime.now().isoformat(),
            }
            # 학습 시스템 이벤트로 전송 시도
            try:
                from AFO.api.routes.debugging_stream import broadcast_debugging_event

                await broadcast_debugging_event(event)
            except ImportError:
                pass
        except Exception:
            pass

    async def conduct_meta_learning_session(
        self, topic: str, learner_config: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """메타 학습 세션 수행 - 학습 결과를 메타-분석"""

        session_id = f"META_LEARN-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        await self._emit_learning_event("session_start", f"🎓 메타 학습 세션 시작: {topic}")

        # ═══════════════════════════════════════════════════════════════
        # Phase 1: 기본 학습 세션 실행
        # ═══════════════════════════════════════════════════════════════
        await self._emit_learning_event("phase1", "1️⃣ Phase 1: 기본 학습 시스템 실행")
        base_session = await self.base_learner.conduct_comprehensive_learning_session(
            topic, learner_config
        )

        # ═══════════════════════════════════════════════════════════════
        # Phase 2: 학습 결과 메타 검증
        # ═══════════════════════════════════════════════════════════════
        await self._emit_learning_event("phase2", "2️⃣ Phase 2: 학습 결과 메타 검증")
        learning_verification = await self._verify_learning_session(
            base_session["baseline_monitoring"],
            base_session["final_analysis"],
            base_session["learning_path"].get("learning_path", []),
        )

        # ═══════════════════════════════════════════════════════════════
        # Phase 3: 학습 패턴 및 효과성 분석
        # ═══════════════════════════════════════════════════════════════
        await self._emit_learning_event("phase3", "3️⃣ Phase 3: 학습 패턴 및 효과성 분석")
        pattern_analysis = await self._analyze_learning_patterns(
            base_session, learning_verification
        )

        # ═══════════════════════════════════════════════════════════════
        # Phase 4: 거짓보고 패턴 탐지
        # ═══════════════════════════════════════════════════════════════
        await self._emit_learning_event("phase4", "4️⃣ Phase 4: 거짓보고 패턴 탐지 및 방지")
        false_reporting_analysis = await self._detect_false_reporting_patterns(
            base_session, learning_verification
        )

        # ═══════════════════════════════════════════════════════════════
        # Phase 5: 학습 개선 및 최적화 제안
        # ═══════════════════════════════════════════════════════════════
        await self._emit_learning_event("phase5", "5️⃣ Phase 5: 학습 개선 및 최적화 제안")
        improvements = await self._generate_learning_improvements(
            learning_verification, pattern_analysis, false_reporting_analysis
        )

        # ═══════════════════════════════════════════════════════════════
        # 최종 메타 학습 신뢰성 점수 계산
        # ═══════════════════════════════════════════════════════════════
        overall_learning_confidence = self._calculate_overall_learning_confidence(
            learning_verification, pattern_analysis, false_reporting_analysis
        )

        # 검증 히스토리 저장
        self.learning_history.append(learning_verification)

        await self._emit_learning_event(
            "session_complete",
            f"✅ 메타 학습 세션 완료 - 신뢰성: {overall_learning_confidence:.1%}",
            (
                "INFO"
                if overall_learning_confidence >= self.learning_confidence_threshold
                else "WARNING"
            ),
        )

        # 종합 결과 반환
        return {
            "session_id": session_id,
            "topic": topic,
            "base_session": base_session,
            "learning_verification": learning_verification,
            "pattern_analysis": pattern_analysis,
            "false_reporting_analysis": false_reporting_analysis,
            "improvements": improvements,
            "overall_learning_confidence": overall_learning_confidence,
            "recommendations": learning_verification.recommendations,
        }

    async def _verify_learning_session(
        self, baseline_assessment: dict, post_assessment: dict, materials_used: list
    ) -> LearningVerificationReport:
        """학습 세션 메타 검증"""

        return await self.verification_engine.verify_learning_session(
            baseline_assessment, post_assessment, materials_used
        )

    async def _analyze_learning_patterns(
        self, base_session: dict, verification: LearningVerificationReport
    ) -> dict[str, Any]:
        """학습 패턴 심층 분석"""

        patterns = {
            "consistency_patterns": [],
            "improvement_trajectory": [],
            "knowledge_retention": [],
            "skill_application": [],
            "meta_learning_capacity": [],
        }

        # 일관성 패턴 분석
        execution_results = base_session.get("execution_results", [])
        if execution_results:
            success_rates = [
                result.get("success", False)
                for result in execution_results
                if isinstance(result, dict)
            ]

            if len(success_rates) >= 3:
                # 성공률 변동성 분석
                avg_success = sum(success_rates) / len(success_rates)
                variance = sum((rate - avg_success) ** 2 for rate in success_rates) / len(
                    success_rates
                )

                if variance < 0.1:
                    patterns["consistency_patterns"].append("높은 일관성: 안정적인 학습 성과")
                elif variance > 0.3:
                    patterns["consistency_patterns"].append("낮은 일관성: 불안정한 학습 성과")

        # 개선 궤적 분석
        improvement = verification.learning_effectiveness.get("trinity_improvement", 0)

        if improvement > 10:
            patterns["improvement_trajectory"].append("급격한 개선: 빠른 학습 진전")
        elif improvement > 5:
            patterns["improvement_trajectory"].append("점진적 개선: 안정적인 학습 진전")
        elif improvement > 0:
            patterns["improvement_trajectory"].append("약한 개선: 추가 학습 필요")
        else:
            patterns["improvement_trajectory"].append("개선 부재: 학습 전략 재검토 필요")

        # 지식 보존 분석
        materials_count = len(base_session.get("learning_path", {}).get("learning_path", []))
        if materials_count > 0:
            utilization_rate = len(execution_results) / materials_count
            if utilization_rate > 0.8:
                patterns["knowledge_retention"].append("높은 활용도: 학습 자료 효과적 활용")
            elif utilization_rate < 0.5:
                patterns["knowledge_retention"].append("낮은 활용도: 학습 자료 추가 탐색 필요")

        # 메타 학습 능력 분석
        confidence_score = verification.confidence_score
        if confidence_score > 0.9:
            patterns["meta_learning_capacity"].append("높은 메타 인지: 스스로 학습 능력 탁월")
        elif confidence_score > 0.7:
            patterns["meta_learning_capacity"].append("적정 메타 인지: 학습 능력 양호")
        else:
            patterns["meta_learning_capacity"].append("메타 인지 강화 필요: 학습 능력 개발 필요")

        return patterns

    async def _detect_false_reporting_patterns(
        self, base_session: dict, verification: LearningVerificationReport
    ) -> dict[str, Any]:
        """거짓보고 패턴 탐지 및 분석"""

        false_patterns = {
            "detected_patterns": [],
            "risk_level": "low",
            "confidence_manipulation": [],
            "result_inflation": [],
            "pattern_manipulation": [],
        }

        # 1. 신뢰성 조작 패턴 탐지
        baseline_score = verification.baseline_assessment.get("trinity_score", 0)
        post_score = verification.learning_effectiveness.get("post_trinity_score", 0)

        # 비현실적인 개선 (예: 0점 → 100점 급격한 상승)
        if baseline_score < 20 and post_score > 80:
            false_patterns["confidence_manipulation"].append("비현실적 개선: 과도한 성과 과장 의심")
            false_patterns["detected_patterns"].append("confidence_inflation")

        # 2. 결과 부풀리기 패턴 탐지
        execution_results = base_session.get("execution_results", [])
        reported_success_rate = verification.learning_effectiveness.get("avg_step_success_rate", 0)

        if execution_results:
            actual_successes = sum(
                1
                for result in execution_results
                if isinstance(result, dict) and result.get("success", False)
            )
            actual_success_rate = actual_successes / len(execution_results)

            # 보고된 성공률이 실제보다 20% 이상 높음
            if reported_success_rate > actual_success_rate + 0.2:
                false_patterns["result_inflation"].append(
                    "성공률 과장: 보고된 성공률이 실제보다 높음"
                )
                false_patterns["detected_patterns"].append("success_rate_inflation")

        # 3. 패턴 조작 탐지
        materials_used = len(base_session.get("learning_path", {}).get("learning_path", []))

        # 학습 자료 없이 높은 성과 (패턴 조작 의심)
        if materials_used == 0 and post_score > baseline_score + 10:
            false_patterns["pattern_manipulation"].append("패턴 조작: 학습 자료 없이 과도한 개선")
            false_patterns["detected_patterns"].append("material_manipulation")

        # 위험 수준 평가
        pattern_count = len(false_patterns["detected_patterns"])
        if pattern_count >= 3:
            false_patterns["risk_level"] = "high"
        elif pattern_count >= 2:
            false_patterns["risk_level"] = "medium"
        elif pattern_count >= 1:
            false_patterns["risk_level"] = "low"

        return false_patterns

    async def _generate_learning_improvements(
        self,
        verification: LearningVerificationReport,
        patterns: dict,
        false_reporting: dict,
    ) -> list[str]:
        """학습 개선 및 최적화 제안 생성"""

        improvements = []

        # 기본 검증 기반 개선
        confidence_score = verification.confidence_score
        if confidence_score < 0.7:
            improvements.append("학습 신뢰성 강화: 기초 개념 복습 및 실습 강화")
        elif confidence_score > 0.9:
            improvements.append("고급 학습 도입: 심화 주제 및 복합 문제 해결")

        # 패턴 기반 개선
        consistency_patterns = patterns.get("consistency_patterns", [])
        improvement_trajectory = patterns.get("improvement_trajectory", [])

        for pattern in consistency_patterns:
            if "높은 일관성" in pattern:
                improvements.append("일관성 유지: 현재 학습 리듬 유지")
            elif "낮은 일관성" in pattern:
                improvements.append("일관성 개선: 정기적 학습 스케줄 수립")

        for trajectory in improvement_trajectory:
            if "급격한 개선" in trajectory:
                improvements.append("지속성 확보: 개선 속도 유지 및 안정화")
            elif "약한 개선" in trajectory:
                improvements.append("학습 전략 조정: 다른 접근법 시도")

        # 거짓보고 방지 개선
        risk_level = false_reporting.get("risk_level", "low")
        if risk_level == "high":
            improvements.append("신뢰성 검증 강화: 학습 과정 투명성 제고")
        elif risk_level == "medium":
            improvements.append("자체 검증 실시: 학습 결과 스스로 검토")

        # 추가 개선 제안
        recommendations = verification.recommendations
        improvements.extend(recommendations)

        return improvements

    def _calculate_overall_learning_confidence(
        self,
        verification: LearningVerificationReport,
        patterns: dict,
        false_reporting: dict,
    ) -> float:
        """종합 학습 신뢰성 점수 계산"""

        # 기본 신뢰성 점수
        base_confidence = verification.confidence_score

        # 패턴 보너스
        pattern_bonus = 0.0
        consistency_patterns = patterns.get("consistency_patterns", [])
        if consistency_patterns:
            pattern_bonus += 0.05  # 일관성 패턴 존재 보너스

        improvement_trajectory = patterns.get("improvement_trajectory", [])
        strong_improvements = [t for t in improvement_trajectory if "급격한" in t or "점진적" in t]
        if strong_improvements:
            pattern_bonus += 0.05  # 긍정적 개선 궤적 보너스

        # 거짓보고 패널티
        false_penalty = 0.0
        risk_level = false_reporting.get("risk_level", "low")
        if risk_level == "high":
            false_penalty = -0.2
        elif risk_level == "medium":
            false_penalty = -0.1

        overall_confidence = base_confidence + pattern_bonus + false_penalty

        return max(0.0, min(1.0, overall_confidence))

    # ═══════════════════════════════════════════════════════════════════
    # 상태 조회 및 모니터링 메소드
    # ═══════════════════════════════════════════════════════════════════

    def get_learning_history(self) -> list[dict[str, Any]]:
        """학습 검증 히스토리 조회"""
        return [
            {
                "session_id": v.session_id,
                "topic": v.topic,
                "timestamp": v.baseline_assessment.get("assessment_timestamp", ""),
                "confidence_score": v.confidence_score,
                "improvement": v.learning_effectiveness.get("trinity_improvement", 0),
                "recommendations_count": len(v.recommendations),
            }
            for v in self.learning_history
        ]

    def get_learning_analytics(self) -> dict[str, Any]:
        """학습 분석 데이터 조회"""
        if not self.learning_history:
            return {"message": "학습 검증 히스토리가 없습니다."}

        # 신뢰성 점수 추세
        confidence_scores = [v.confidence_score for v in self.learning_history]

        # 개선 추세
        improvements = [
            v.learning_effectiveness.get("trinity_improvement", 0) for v in self.learning_history
        ]

        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0

        # 학습 효과성 통계
        strong_improvements = sum(1 for imp in improvements if imp > 10)
        weak_improvements = sum(1 for imp in improvements if imp < 5)

        return {
            "total_sessions": len(self.learning_history),
            "avg_confidence_score": avg_confidence,
            "avg_improvement": avg_improvement,
            "strong_improvements": strong_improvements,
            "weak_improvements": weak_improvements,
            "learning_effectiveness": (
                "excellent"
                if avg_improvement > 10
                else "good"
                if avg_improvement > 5
                else "needs_improvement"
            ),
            "current_threshold": self.learning_confidence_threshold,
        }

    async def run_health_check(self) -> dict[str, Any]:
        """학습 검증 에이전트 건강 상태 점검"""
        try:
            # 기본 컴포넌트 상태 확인
            base_status = "operational"
            verification_status = "operational" if self.verification_engine else "failed"

            # 최근 학습 세션 상태
            recent_session = None
            if self.learning_history:
                recent = self.learning_history[-1]
                recent_session = {
                    "confidence_score": recent.confidence_score,
                    "improvement": recent.learning_effectiveness.get("trinity_improvement", 0),
                    "age_seconds": (
                        datetime.now()
                        - datetime.fromisoformat(
                            recent.baseline_assessment.get(
                                "assessment_timestamp", datetime.now().isoformat()
                            )
                        )
                    ).total_seconds(),
                }

            return {
                "agent_status": "healthy",
                "base_learner": base_status,
                "verification_engine": verification_status,
                "history_size": len(self.learning_history),
                "recent_session": recent_session,
                "learning_confidence_threshold": self.learning_confidence_threshold,
            }

        except Exception as e:
            return {
                "agent_status": "unhealthy",
                "error": str(e),
            }


# ═══════════════════════════════════════════════════════════════════
# 팩토리 및 편의 함수
# ═══════════════════════════════════════════════════════════════════


class LearningVerificationAgentFactory:
    """학습 검증 에이전트 팩토리"""

    @staticmethod
    def create_agent(
        base_learner: IntegratedLearningSystem | None = None,
        verification_engine: LearningVerificationEngine | None = None,
    ) -> LearningVerificationAgent:
        """학습 검증 에이전트 생성"""
        return LearningVerificationAgent(base_learner, verification_engine)


# 싱글톤 인스턴스
_learning_verification_agent = None


def get_learning_verification_agent() -> LearningVerificationAgent:
    """학습 검증 에이전트 싱글톤"""
    global _learning_verification_agent
    if _learning_verification_agent is None:
        _learning_verification_agent = LearningVerificationAgentFactory.create_agent()
    return _learning_verification_agent


async def conduct_meta_learning_session(
    topic: str, learner_config: dict[str, Any] | None = None
) -> dict[str, Any]:
    """메타 학습 세션 편의 함수"""
    agent = get_learning_verification_agent()
    return await agent.conduct_meta_learning_session(topic, learner_config)
