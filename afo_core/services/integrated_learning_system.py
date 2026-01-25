# Trinity Score: 98.0 (Integrated Learning System - Complete Wisdom)
"""
통합 학습 모니터링 시스템 (Integrated Learning System)

옵시디언 사서 + LangSmith 선생의 완벽한 협력 시스템
Context7 기반 완전한 지피지기 및 학습 모니터링 구현

역할:
- 옵시디언 사서와 LangSmith 선생의 통합 오케스트레이션 (孝 - Serenity)
- Context7 지식 베이스와 실시간 모니터링의 완벽한 결합 (眞善美永 - Complete Trinity)
"""

import asyncio
import logging
import uuid
from typing import Any

from AFO.services.learning_types import (
    ComprehensiveAssessment,
    LearnerConfig,
    LearningAnalytics,
    LearningSessionResult,
    LearningStep,
    MonitoringResult,
    StepExecutionResult,
    SystemInitStatus,
    SystemStatusResponse,
)

logger = logging.getLogger(__name__)


class IntegratedLearningSystem:
    """통합 학습 모니터링 시스템 - 옵시디언 사서 + LangSmith 선생"""

    def __init__(self) -> None:
        self.obsidian_librarian = None
        self.langsmith_mentor = None
        self.context7_service = None
        self.active_sessions: dict[str, dict[str, Any]] = {}
        self.system_status = "initializing"

    async def initialize_system(self) -> SystemInitStatus:
        """통합 시스템 초기화"""
        try:
            # 옵시디언 사서 초기화
            from AFO.services.obsidian_librarian import initialize_obsidian_librarian

            librarian_status = await initialize_obsidian_librarian()

            # LangSmith 선생 초기화
            from AFO.services.langsmith_mentor import initialize_langsmith_mentor

            mentor_status = await initialize_langsmith_mentor()

            # Context7 서비스 연결
            from AFO.services.context7_service import get_context7_instance

            self.context7_service = get_context7_instance()

            # 컴포넌트 연결
            from AFO.services.obsidian_librarian import get_obsidian_librarian

            self.obsidian_librarian = await get_obsidian_librarian()

            from AFO.services.langsmith_mentor import get_langsmith_mentor

            self.langsmith_mentor = await get_langsmith_mentor()

            self.system_status = "active"

            system_status = {
                "status": "fully_integrated",
                "obsidian_librarian": librarian_status,
                "langsmith_mentor": mentor_status,
                "context7_connected": self.context7_service is not None,
                "integration_level": "complete",
            }

            logger.info("🎉 통합 학습 모니터링 시스템 완전 초기화 성공!")
            logger.info(
                f"   옵시디언 사서: {'연결됨' if librarian_status.get('status') == 'initialized' else '오류'}"
            )
            logger.info(
                f"   LangSmith 선생: {'연결됨' if mentor_status.get('status') == 'initialized' else '오류'}"
            )
            logger.info(f"   Context7 지식베이스: {'연결됨' if self.context7_service else '오류'}")

            return system_status

        except Exception as e:
            self.system_status = "failed"
            logger.error(f"통합 시스템 초기화 실패: {e}")
            return {"status": "failed", "error": str(e)}

    async def conduct_comprehensive_learning_session(
        self, topic: str, learner_config: LearnerConfig | None = None
    ) -> LearningSessionResult:
        """완전한 학습 세션 수행 - 옵시디언 사서 + LangSmith 선생의 협력"""

        session_id = f"learning_session_{uuid.uuid4().hex[:8]}"
        start_time = asyncio.get_event_loop().time()

        try:
            # 학습자 설정 기본값
            learner_config = learner_config or {}
            learner_level = learner_config.get("level", "intermediate")
            _focus_areas = learner_config.get("focus_areas", ["truth", "goodness", "beauty"])

            logger.info(f"🚀 학습 세션 시작: {topic} (레벨: {learner_level})")

            # === Phase 1: 옵시디언 사서 - 학습 자료 준비 ===
            logger.info("📚 Phase 1: 옵시디언 사서 - 학습 자료 준비")
            learning_path = await self.obsidian_librarian.generate_learning_path(
                topic, learner_level=learner_level
            )

            learning_materials = learning_path.get("learning_path", [])
            logger.info(f"   준비된 학습 단계: {len(learning_materials)}개")

            # === Phase 2: LangSmith 선생 - 사전 모니터링 ===
            logger.info("👨‍🏫 Phase 2: LangSmith 선생 - 사전 모니터링")
            baseline_monitoring = await self.langsmith_mentor.monitor_execution(session_id)

            # === Phase 3: 단계별 학습 실행 ===
            logger.info("🎯 Phase 3: 단계별 학습 실행")

            execution_results = []
            step_monitoring = []

            for step_idx, step in enumerate(learning_materials):
                step_name = step.get("phase", f"Step {step_idx + 1}")
                logger.info(f"   {step_idx + 1}. {step_name} 실행 중...")

                # 각 단계별 실행
                step_result = await self._execute_learning_step(step, topic, session_id, step_idx)
                execution_results.append(step_result)

                # 단계별 모니터링
                step_analysis = await self.langsmith_mentor.monitor_execution(
                    f"{session_id}_step_{step_idx}"
                )
                step_monitoring.append(step_analysis)

                # 단계 성공률 확인
                success_rate = step_analysis.get("performance_analysis", {}).get("success_rate", 0)
                if success_rate < 0.7:
                    logger.warning(f"   ⚠️ {step_name} 낮은 성공률: {success_rate:.1%}")
                else:
                    logger.info(f"   ✅ {step_name} 성공: {success_rate:.1%}")

            # === Phase 4: LangSmith 선생 - 종합 모니터링 및 분석 ===
            logger.info("📊 Phase 4: LangSmith 선생 - 종합 모니터링 및 분석")
            final_analysis = await self.langsmith_mentor.monitor_execution(session_id)

            # === Phase 5: 학습 성과 종합 평가 ===
            logger.info("🏆 Phase 5: 학습 성과 종합 평가")
            comprehensive_assessment = self._assess_comprehensive_learning(
                baseline_monitoring,
                final_analysis,
                learning_materials,
                execution_results,
                step_monitoring,
            )

            # === Phase 6: 옵시디언 사서 - 학습 결과 기록 ===
            logger.info("📝 Phase 6: 옵시디언 사서 - 학습 결과 기록")
            _recording_result = await self.obsidian_librarian.record_learning_session(
                {
                    "topic": topic,
                    "trace_id": session_id,
                    "materials_used": learning_materials,
                    "execution_result": {
                        "success": comprehensive_assessment.get("overall_success", False),
                        "steps_completed": len(execution_results),
                        "avg_success_rate": comprehensive_assessment.get(
                            "avg_step_success_rate", 0
                        ),
                    },
                    "performance_analysis": final_analysis,
                    "assessment": comprehensive_assessment,
                }
            )

            # === Phase 7: 최종 결과 정리 ===
            end_time = asyncio.get_event_loop().time()
            session_duration = end_time - start_time

            final_result = {
                "session_id": session_id,
                "topic": topic,
                "learner_config": learner_config,
                "duration_seconds": session_duration,
                "learning_path": learning_path,
                "execution_results": execution_results,
                "baseline_monitoring": baseline_monitoring,
                "final_analysis": final_analysis,
                "comprehensive_assessment": comprehensive_assessment,
                "recommendations": final_analysis.get("recommendations", []),
                "next_learning_suggestions": self._generate_next_learning_suggestions(
                    comprehensive_assessment, topic, learner_level
                ),
            }

            # 세션 저장
            self.active_sessions[session_id] = {
                "topic": topic,
                "start_time": start_time,
                "end_time": end_time,
                "assessment": comprehensive_assessment,
                "final_result": final_result,
            }

            logger.info("🎊 학습 세션 완료!")
            logger.info(f"   총 소요시간: {session_duration:.1f}초")
            logger.info(f"   최종 등급: {comprehensive_assessment.get('overall_grade', 'N/A')}")
            logger.info(
                f"   Trinity Score 개선: {comprehensive_assessment.get('trinity_improvement', 0):.1f}점"
            )

            return final_result

        except Exception as e:
            logger.error(f"학습 세션 실패: {e}")
            return {"error": f"학습 세션 실패: {e}", "session_id": session_id}

    async def _execute_learning_step(
        self, step: LearningStep, topic: str, session_id: str, step_idx: int
    ) -> StepExecutionResult:
        """개별 학습 단계 실행"""
        try:
            step_name = step.get("phase", f"Step {step_idx + 1}")
            materials = step.get("materials", [])

            # Chancellor Graph를 통한 학습 실행
            from AFO.chancellor_graph import chancellor_graph

            step_prompt = f"""
학습 단계: {step_name}
주제: {topic}
학습 자료: {", ".join([m.get("title", "") for m in materials])}

이 학습 자료를 기반으로 다음을 수행하세요:
1. 핵심 개념 이해
2. 실전 적용 사례 학습
3. 관련 모범 사례 확인
"""

            step_result = await chancellor_graph.invoke(
                step_prompt,
                headers={
                    "x-afo-learning-session": "true",
                    "x-afo-learning-step": str(step_idx),
                    "x-afo-session-id": session_id,
                },
            )

            return {
                "step_index": step_idx,
                "step_name": step_name,
                "materials_count": len(materials),
                "execution_result": step_result,
                "success": step_result.get("success", False),
            }

        except Exception as e:
            logger.error(f"학습 단계 실행 실패: {e}")
            return {
                "step_index": step_idx,
                "step_name": step.get("phase", f"Step {step_idx + 1}"),
                "error": str(e),
                "success": False,
            }

    def _assess_comprehensive_learning(
        self,
        baseline: MonitoringResult,
        final: MonitoringResult,
        materials: list[LearningStep],
        executions: list[StepExecutionResult],
        step_monitoring: list[MonitoringResult],
    ) -> ComprehensiveAssessment:
        """종합 학습 성과 평가"""

        # Trinity Score 개선도
        baseline_score = baseline.get("trinity_score", 0)
        final_score = final.get("trinity_score", 0)
        trinity_improvement = final_score - baseline_score

        # 단계별 성공률
        step_success_rates = [
            monitoring.get("performance_analysis", {}).get("success_rate", 0)
            for monitoring in step_monitoring
        ]
        avg_step_success_rate = (
            sum(step_success_rates) / len(step_success_rates) if step_success_rates else 0
        )

        # 자료 활용도
        materials_used = sum(len(step.get("materials", [])) for step in materials)
        materials_effective = materials_used > 0

        # 실행 성공도
        execution_success = avg_step_success_rate > 0.7

        # 종합 등급 계산
        overall_grade = self._calculate_overall_learning_grade(
            trinity_improvement,
            materials_effective,
            execution_success,
            avg_step_success_rate,
        )

        # 학습 강점/약점 분석
        strengths, weaknesses = self._analyze_learning_profile(
            materials, executions, step_monitoring
        )

        return {
            "baseline_trinity_score": baseline_score,
            "final_trinity_score": final_score,
            "trinity_improvement": trinity_improvement,
            "avg_step_success_rate": avg_step_success_rate,
            "materials_effective": materials_effective,
            "execution_success": execution_success,
            "overall_success": execution_success and materials_effective,
            "overall_grade": overall_grade,
            "learning_strengths": strengths,
            "learning_weaknesses": weaknesses,
            "materials_utilization": materials_used,
            "steps_completed": len(executions),
            "assessment_timestamp": asyncio.get_event_loop().time(),
        }

    def _calculate_overall_learning_grade(
        self,
        trinity_improvement: float,
        materials_effective: bool,
        execution_success: bool,
        avg_success_rate: float,
    ) -> str:
        """종합 학습 등급 계산"""
        score = 0

        # Trinity Score 개선도 (40점 만점)
        if trinity_improvement > 20:
            score += 40
        elif trinity_improvement > 15:
            score += 35
        elif trinity_improvement > 10:
            score += 25
        elif trinity_improvement > 5:
            score += 15
        elif trinity_improvement > 0:
            score += 5

        # 자료 활용도 (20점)
        if materials_effective:
            score += 20

        # 실행 성공도 (25점)
        success_score = int(avg_success_rate * 25)
        score += success_score

        # 일관성 보너스 (15점)
        if execution_success and materials_effective and trinity_improvement > 0:
            score += 15

        # 등급 결정
        if score >= 90:
            return "S (완벽한 학습 마스터리)"
        elif score >= 80:
            return "A+ (탁월한 학습 성취)"
        elif score >= 70:
            return "A (우수한 학습 성취)"
        elif score >= 60:
            return "B+ (양호한 학습 성취)"
        elif score >= 50:
            return "B (기초적인 학습 성취)"
        elif score >= 40:
            return "C (추가 학습 필요)"
        else:
            return "D (학습 재시작 권장)"

    def _analyze_learning_profile(
        self,
        materials: list[LearningStep],
        executions: list[StepExecutionResult],
        monitoring: list[MonitoringResult],
    ) -> tuple[list[str], list[str]]:
        """학습 프로필 분석 (강점/약점)"""
        strengths = []
        weaknesses = []

        # Trinity 카테고리별 분석
        trinity_focus = {}
        for material_group in materials:
            for material in material_group.get("materials", []):
                category = material.get("trinity_category", "unknown")
                trinity_focus[category] = trinity_focus.get(category, 0) + 1

        # 가장 많이 학습한 카테고리 = 강점
        if trinity_focus:
            top_category = max(trinity_focus.items(), key=lambda x: x[1])
            category_names = {
                "truth": "기술적 확실성 (眞)",
                "goodness": "안정성과 신뢰성 (善)",
                "beauty": "사용성 및 디자인 (美)",
                "serenity": "조화와 프로세스 (孝)",
                "eternity": "지속성과 유지보수 (永)",
            }
            strengths.append(f"{category_names.get(top_category[0], top_category[0])} 분야 강점")

        # 실행 성공률 분석
        success_rates = [
            m.get("performance_analysis", {}).get("success_rate", 0) for m in monitoring
        ]
        avg_success = sum(success_rates) / len(success_rates) if success_rates else 0

        if avg_success > 0.8:
            strengths.append("높은 실행 성공률")
        elif avg_success < 0.6:
            weaknesses.append("실행 성공률 향상 필요")

        # 학습 자료 활용도
        total_materials = sum(len(step.get("materials", [])) for step in materials)
        if total_materials > 10:
            strengths.append("광범위한 학습 자료 활용")
        elif total_materials < 3:
            weaknesses.append("더 다양한 학습 자료 탐색 필요")

        return strengths, weaknesses

    def _generate_next_learning_suggestions(
        self, assessment: ComprehensiveAssessment, current_topic: str, learner_level: str
    ) -> list[str]:
        """다음 학습 제안 생성"""
        suggestions = []

        grade = assessment.get("overall_grade", "")
        weaknesses = assessment.get("learning_weaknesses", [])

        # 등급 기반 제안
        if "S" in grade or "A+" in grade:
            suggestions.append(
                f"🎉 축하합니다! {current_topic} 마스터리 달성. 다음 단계 주제로 도전해보세요."
            )
            if learner_level == "intermediate":
                suggestions.append("Advanced 레벨로 상승하여 더 깊이 있는 학습을 시도해보세요.")
            elif learner_level == "advanced":
                suggestions.append("멘토링이나 새로운 분야 개척을 고려해보세요.")
        elif "A" in grade:
            suggestions.append(
                f"잘했습니다! {current_topic}에 대한 이해도가 높습니다. 실전 적용을 강화해보세요."
            )
        elif "B" in grade:
            suggestions.append(
                f"{current_topic}에 대한 기초 지식이 구축되었습니다. 심화 학습을 진행해보세요."
            )
        elif "C" in grade:
            suggestions.append(
                f"{current_topic}에 대한 추가 학습이 필요합니다. 기초 개념부터 다시 복습해보세요."
            )
        else:
            suggestions.append(
                f"{current_topic} 학습을 처음부터 체계적으로 진행하는 것을 권장합니다."
            )

        # 약점 기반 제안
        for weakness in weaknesses:
            if "실행 성공률" in weakness:
                suggestions.append("실전 적용 연습을 통해 실행 능력을 향상시키세요.")
            elif "학습 자료" in weakness:
                suggestions.append("더 다양한 자료源을 활용하여 폭넓은 시각을 기르세요.")
            elif "시간" in weakness:
                suggestions.append("집중 학습 시간을 늘리거나 효율적인 학습 방법을 찾아보세요.")

        # Trinity Score 기반 제안
        improvement = assessment.get("trinity_improvement", 0)
        if improvement > 15:
            suggestions.append(
                "Trinity Score가 크게 향상되었습니다! 자신감을 가지고 다음 도전에 임하세요."
            )
        elif improvement < 5:
            suggestions.append("Trinity Score 개선을 위해 반복 학습과 실전 적용을 강화해보세요.")

        return suggestions

    async def get_system_status(self) -> SystemStatusResponse:
        """통합 시스템 상태 조회"""
        try:
            librarian_status = (
                await self.obsidian_librarian.get_librarian_status()
                if self.obsidian_librarian
                else {"error": "not connected"}
            )
            mentor_status = (
                await self.langsmith_mentor.get_mentor_status()
                if self.langsmith_mentor
                else {"error": "not connected"}
            )

            return {
                "system_status": self.system_status,
                "active_sessions": len(self.active_sessions),
                "obsidian_librarian": librarian_status,
                "langsmith_mentor": mentor_status,
                "context7_connected": self.context7_service is not None,
                "integration_health": (
                    "excellent" if self.system_status == "active" else "degraded"
                ),
            }
        except Exception as e:
            return {"error": f"시스템 상태 조회 실패: {e}"}

    def get_learning_analytics(self) -> LearningAnalytics:
        """학습 분석 데이터 조회"""
        if not self.active_sessions:
            return {"message": "활성 학습 세션이 없습니다."}

        sessions = list(self.active_sessions.values())

        # 평균 성과 계산
        avg_improvement = sum(
            s["assessment"].get("trinity_improvement", 0) for s in sessions
        ) / len(sessions)
        avg_success_rate = sum(
            s["assessment"].get("avg_step_success_rate", 0) for s in sessions
        ) / len(sessions)

        # 가장 성공적인 세션
        best_session = max(sessions, key=lambda s: s["assessment"].get("final_trinity_score", 0))

        # 학습 패턴 분석
        grade_distribution = {}
        for session in sessions:
            grade = session["assessment"].get("overall_grade", "Unknown")
            grade_distribution[grade] = grade_distribution.get(grade, 0) + 1

        return {
            "total_sessions": len(sessions),
            "avg_trinity_improvement": round(avg_improvement, 1),
            "avg_success_rate": round(avg_success_rate, 3),
            "best_session": {
                "topic": best_session["topic"],
                "grade": best_session["assessment"].get("overall_grade"),
                "improvement": best_session["assessment"].get("trinity_improvement", 0),
            },
            "grade_distribution": grade_distribution,
            "recent_topics": [s["topic"] for s in sessions[-5:]],
        }


# 싱글톤 인스턴스
integrated_learning_system = IntegratedLearningSystem()


async def get_integrated_learning_system() -> IntegratedLearningSystem:
    """통합 학습 시스템 인스턴스 조회 (싱글톤)"""
    return integrated_learning_system


async def initialize_integrated_learning_system() -> SystemInitStatus:
    """통합 학습 모니터링 시스템 초기화"""
    return await integrated_learning_system.initialize_system()
