# Trinity Score: 95.0 (LangSmith Mentor - Learning Master)
"""
LangSmith 선생 시스템 (LangSmith Mentor System)

AFO 왕국의 모니터링 및 학습 마스터
실시간 실행 추적 및 학습 가이드 시스템

역할:
- 모든 실행 모니터링 및 추적 (眞 - Truth)
- 성능 분석 및 최적화 제안 (善 - Goodness)
- 학습 패턴 분석 및 피드백 (美 - Beauty)
- Trinity Score 기반 교육 시스템 (孝永 - Serenity & Eternity)
"""

import asyncio
import logging
import os
from typing import Any

from AFO.chancellor_graph import chancellor_graph
from AFO.services.langsmith_types import (
    LearningAssessment,
    LearningHistory,
    LearningSessionResult,
    MentorInitStatus,
    MentorStatus,
    MonitoringAnalysis,
    PerformanceAnalysis,
)

logger = logging.getLogger(__name__)


class LangSmithMentor:
    """LangSmith 선생 - 모니터링 및 학습 마스터"""

    def __init__(self) -> None:
        self.langsmith_client = self._initialize_langsmith()
        self.chancellor_graph = chancellor_graph
        self.obsidian_librarian = None
        self.project_name = "AFO_Kingdom_Chancellor"
        self.learning_sessions: dict[str, dict[str, Any]] = {}

    def _initialize_langsmith(self) -> Any | None:
        """LangSmith 클라이언트 초기화"""
        try:
            # LangSmith 라이브러리 import 시도
            import langsmith

            client = langsmith.Client(
                api_key=os.getenv("LANGCHAIN_API_KEY"),
                api_url=os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com"),
            )

            logger.info("✅ LangSmith 클라이언트 초기화 성공")
            return client

        except ImportError:
            logger.warning("⚠️ LangSmith 라이브러리가 설치되지 않음 - 모의 모드 사용")
            return None
        except Exception as e:
            logger.error(f"LangSmith 초기화 실패: {e}")
            return None

    async def initialize_mentor(self) -> MentorInitStatus:
        """선생 시스템 초기화"""
        try:
            # 옵시디언 사서 연결
            from AFO.services.obsidian_librarian import get_obsidian_librarian

            self.obsidian_librarian = await get_obsidian_librarian()

            status = {
                "status": "initialized",
                "langsmith_available": self.langsmith_client is not None,
                "obsidian_librarian_connected": self.obsidian_librarian is not None,
                "project_name": self.project_name,
            }

            logger.info(f"✅ LangSmith 선생 초기화 완료: {status}")
            return status

        except Exception as e:
            logger.error(f"LangSmith 선생 초기화 실패: {e}")
            return {"status": "failed", "error": str(e)}

    async def monitor_execution(self, trace_id: str) -> MonitoringAnalysis:
        """실행 모니터링 및 분석"""
        try:
            if not self.langsmith_client:
                # 모의 모드: 기본 분석 결과 반환
                return await self._mock_monitoring_analysis(trace_id)

            # 실제 LangSmith API 호출
            runs = self.langsmith_client.list_runs(
                project_name=self.project_name, filter=f"trace_id:{trace_id}"
            )

            # 실행 데이터 분석
            performance_analysis = self._analyze_performance(list(runs))
            learning_insights = self._extract_learning_insights(list(runs))
            recommendations = self._generate_recommendations(
                performance_analysis, learning_insights
            )

            # Trinity Score 계산
            trinity_score = self._calculate_execution_trinity_score(list(runs))

            result = {
                "trace_id": trace_id,
                "performance_analysis": performance_analysis,
                "learning_insights": learning_insights,
                "recommendations": recommendations,
                "trinity_score": trinity_score,
                "monitoring_mode": "real",
            }

            logger.info(f"✅ 실행 모니터링 완료: {trace_id} (Trinity Score: {trinity_score:.1f})")
            return result

        except Exception as e:
            logger.error(f"실행 모니터링 실패: {e}")
            return await self._mock_monitoring_analysis(trace_id)

    async def _mock_monitoring_analysis(self, trace_id: str) -> MonitoringAnalysis:
        """모의 모드 모니터링 분석"""
        # 기본 성능 메트릭 생성
        import random

        base_score = random.uniform(70, 95)
        execution_time = random.uniform(0.5, 5.0)
        success_rate = random.uniform(0.8, 1.0)

        # Trinity Score 계산
        trinity_score = self._calculate_mock_trinity_score(base_score, execution_time, success_rate)

        return {
            "trace_id": trace_id,
            "performance_analysis": {
                "avg_execution_time": execution_time,
                "success_rate": success_rate,
                "total_runs": random.randint(5, 20),
                "performance_trend": "stable",
            },
            "learning_insights": [
                "실행 패턴 분석 중",
                "성능 메트릭 수집 중",
                "학습 데이터 축적 중",
            ],
            "recommendations": [
                "LangSmith 라이브러리 설치 권장",
                "실시간 모니터링 활성화",
                "성능 최적화 고려",
            ],
            "trinity_score": trinity_score,
            "monitoring_mode": "mock",
        }

    def _analyze_performance(self, runs: list[Any]) -> PerformanceAnalysis:
        """성능 분석"""
        if not runs:
            return {"error": "No runs to analyze"}

        execution_times = []
        success_count = 0
        total_runs = len(runs)

        for run in runs:
            # LangSmith run 객체에서 데이터 추출
            if hasattr(run, "execution_time") and run.execution_time:
                execution_times.append(run.execution_time)

            if hasattr(run, "success") and run.success:
                success_count += 1

        # 기본 메트릭 계산
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0
        success_rate = success_count / total_runs if total_runs > 0 else 0

        # 성능 추세 분석
        performance_trend = self._calculate_performance_trend(execution_times)

        return {
            "avg_execution_time": avg_execution_time,
            "success_rate": success_rate,
            "total_runs": total_runs,
            "performance_trend": performance_trend,
            "execution_time_range": {
                "min": min(execution_times) if execution_times else 0,
                "max": max(execution_times) if execution_times else 0,
            },
        }

    def _calculate_performance_trend(self, execution_times: list[float]) -> str:
        """성능 추세 계산"""
        if len(execution_times) < 3:
            return "insufficient_data"

        # 최근 절반과 이전 절반 비교
        midpoint = len(execution_times) // 2
        recent_times = execution_times[midpoint:]
        older_times = execution_times[:midpoint]

        recent_avg = sum(recent_times) / len(recent_times)
        older_avg = sum(older_times) / len(older_times)

        if recent_avg < older_avg * 0.9:
            return "improving"
        elif recent_avg > older_avg * 1.1:
            return "degrading"
        else:
            return "stable"

    def _extract_learning_insights(self, runs: list[Any]) -> list[str]:
        """학습 인사이트 추출"""
        insights = []

        if len(runs) < 3:
            return ["데이터 부족으로 학습 인사이트 생성 불가"]

        # 성공/실패 패턴 분석
        successful_runs = [r for r in runs if getattr(r, "success", False)]
        failed_runs = [r for r in runs if not getattr(r, "success", True)]

        if successful_runs:
            success_patterns = self._find_success_patterns(successful_runs)
            insights.append(f"성공 패턴: {', '.join(success_patterns[:3])}")

        if failed_runs:
            failure_patterns = self._find_failure_patterns(failed_runs)
            insights.append(f"실패 패턴: {', '.join(failure_patterns[:3])}")

        # 실행 빈도 분석
        if len(runs) >= 5:
            insights.append(self._analyze_execution_frequency(runs))

        # 개선 추세 분석
        improvement_trend = self._analyze_improvement_trend(runs)
        if improvement_trend:
            insights.append(improvement_trend)

        return insights or ["학습 패턴 분석 중"]

    def _find_success_patterns(self, runs: list[Any]) -> list[str]:
        """성공 패턴 찾기"""
        patterns = []

        # 실행 시간 패턴
        execution_times = [
            getattr(r, "execution_time", 0) for r in runs if getattr(r, "execution_time", 0) > 0
        ]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            if avg_time < 2.0:
                patterns.append("빠른 실행")
            elif avg_time > 10.0:
                patterns.append("복잡한 처리")

        # 입력 크기 패턴 (추정)
        if len(runs) > 5:
            patterns.append("일관된 입력 처리")

        return patterns or ["패턴 분석 중"]

    def _find_failure_patterns(self, runs: list[Any]) -> list[str]:
        """실패 패턴 찾기"""
        patterns = []

        # 에러 타입 분석 (가능한 경우)
        error_types = []
        for run in runs:
            if hasattr(run, "error") and run.error:
                error_type = str(type(run.error).__name__)
                error_types.append(error_type)

        if error_types:
            most_common_error = max(set(error_types), key=error_types.count)
            patterns.append(f"흔한 에러: {most_common_error}")

        # 시간 패턴
        execution_times = [getattr(r, "execution_time", 0) for r in runs]
        if execution_times and max(execution_times) > 30:
            patterns.append("타임아웃倾向")

        return patterns or ["실패 패턴 분석 중"]

    def _analyze_execution_frequency(self, runs: list[Any]) -> str:
        """실행 빈도 분석"""
        if len(runs) < 2:
            return "실행 빈도 분석을 위한 데이터 부족"

        # 타임스탬프 기반 빈도 계산
        timestamps = []
        for run in runs:
            if hasattr(run, "start_time") and run.start_time:
                timestamps.append(run.start_time)
            elif hasattr(run, "created_at") and run.created_at:
                timestamps.append(run.created_at)

        if len(timestamps) >= 2:
            timestamps.sort()
            intervals = []
            for i in range(1, len(timestamps)):
                interval = timestamps[i] - timestamps[i - 1]
                if interval.total_seconds() > 0:
                    intervals.append(interval.total_seconds())

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval < 3600:  # 1시간 이내
                    return "활발한 반복 실행"
                elif avg_interval < 86400:  # 1일 이내
                    return "일일 실행 패턴"
                else:
                    return "간헐적 실행"

        return "실행 빈도 패턴 분석 중"

    def _analyze_improvement_trend(self, runs: list[Any]) -> str:
        """개선 추세 분석"""
        if len(runs) < 5:
            return ""

        # 성공률 추세
        recent_runs = runs[-5:]
        earlier_runs = runs[:-5] if len(runs) > 5 else []

        if earlier_runs:
            recent_success_rate = sum(1 for r in recent_runs if getattr(r, "success", False)) / len(
                recent_runs
            )
            earlier_success_rate = sum(
                1 for r in earlier_runs if getattr(r, "success", False)
            ) / len(earlier_runs)

            if recent_success_rate > earlier_success_rate + 0.1:
                return "성공률 향상 추세"
            elif recent_success_rate < earlier_success_rate - 0.1:
                return "성공률 저하 추세"

        return "성공률 안정적"

    def _generate_recommendations(
        self, performance: PerformanceAnalysis, insights: list[str]
    ) -> list[str]:
        """개선 권고사항 생성"""
        recommendations = []

        # 성능 기반 권고
        avg_time = performance.get("avg_execution_time", 0)
        if avg_time > 10:
            recommendations.append("실행 시간 최적화 고려 (현재 평균 10초 초과)")
        elif avg_time > 30:
            recommendations.append("⚠️ 긴 실행 시간: 성능 병목 분석 필요")

        success_rate = performance.get("success_rate", 0)
        if success_rate < 0.8:
            recommendations.append("성공률 향상 필요 (현재 80% 미만)")
        elif success_rate < 0.9:
            recommendations.append("성공률 추가 개선 가능")

        # 인사이트 기반 권고
        for insight in insights:
            if "실패 패턴" in insight:
                recommendations.append("식별된 실패 패턴 해결 방안 모색")
            if "성공률 향상" in insight:
                recommendations.append("현재 개선 추세 유지 및 확대")
            if "빠른 실행" in insight:
                recommendations.append("효율적인 실행 패턴 유지")

        # 일반 권고
        if not recommendations:
            recommendations.append("LangSmith 실시간 모니터링 활성화 권장")
            recommendations.append("성능 메트릭 정기 검토")

        return recommendations

    def _calculate_execution_trinity_score(self, runs: list[Any]) -> float:
        """실행 기반 Trinity Score 계산"""
        if not runs:
            return 0.0

        # 眞 (Truth) - 기술적 성공률: 35%
        success_count = sum(1 for r in runs if getattr(r, "success", False))
        truth_score = (success_count / len(runs)) * 35

        # 善 (Goodness) - 안정성: 35%
        # 실행 시간 일관성 기반
        execution_times = [
            getattr(r, "execution_time", 5) for r in runs if getattr(r, "execution_time", 0) > 0
        ]
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            # 평균 대비 편차가 적을수록 높은 점수
            if avg_time > 0:
                variances = [abs(t - avg_time) / avg_time for t in execution_times]
                avg_variance = sum(variances) / len(variances)
                goodness_score = max(0, (1 - avg_variance) * 35)
            else:
                goodness_score = 17.5  # 중간 점수
        else:
            goodness_score = 17.5

        # 美 (Beauty) - 효율성: 20%
        # 실행 시간 기반 (30초 이내 완료 시 최대 점수)
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            beauty_score = max(0, (30 - avg_time) / 30 * 20)
        else:
            beauty_score = 10

        # 孝 (Serenity) - 일관성: 8%
        # 성공률 기반
        success_rate = success_count / len(runs) if runs else 0
        serenity_score = success_rate * 8

        # 永 (Eternity) - 지속성: 2%
        # 기본 점수
        eternity_score = 2.0

        total_score = truth_score + goodness_score + beauty_score + serenity_score + eternity_score
        return min(100.0, total_score)

    def _calculate_mock_trinity_score(
        self, base_score: float, execution_time: float, success_rate: float
    ) -> float:
        """모의 모드 Trinity Score 계산"""
        # 기본 점수를 기반으로 각 기둥 점수 계산
        truth_score = success_rate * 35
        goodness_score = (1 - min(execution_time / 10, 1)) * 35  # 실행 시간이 짧을수록 높음
        beauty_score = min(base_score / 100 * 20, 20)
        serenity_score = success_rate * 8
        eternity_score = 2.0

        return truth_score + goodness_score + beauty_score + serenity_score + eternity_score

    async def conduct_learning_session(self, topic: str, trace_id: str) -> LearningSessionResult:
        """학습 세션 수행"""
        try:
            # 학습 자료 준비 (옵시디언 사서)
            learning_materials = []
            if self.obsidian_librarian:
                learning_path = await self.obsidian_librarian.generate_learning_path(topic)
                learning_materials = learning_path.get("learning_path", [])

            # 사전 모니터링
            baseline_monitoring = await self.monitor_execution(trace_id)

            # Chancellor Graph 실행
            execution_result = await self.chancellor_graph.invoke(
                f"Learn and apply: {topic}", headers={"x-afo-learning-session": "true"}
            )

            # 사후 모니터링
            post_execution_analysis = await self.monitor_execution(trace_id)

            # 학습 성과 평가
            learning_assessment = self._assess_learning_outcome(
                baseline_monitoring, post_execution_analysis, learning_materials
            )

            # 학습 세션 기록 (옵시디언)
            if self.obsidian_librarian:
                await self.obsidian_librarian.record_learning_session(
                    {
                        "topic": topic,
                        "trace_id": trace_id,
                        "materials_used": learning_materials,
                        "execution_result": execution_result,
                        "performance_analysis": post_execution_analysis,
                        "assessment": learning_assessment,
                    }
                )

            # 세션 저장
            self.learning_sessions[trace_id] = {
                "topic": topic,
                "timestamp": asyncio.get_event_loop().time(),
                "materials": learning_materials,
                "baseline": baseline_monitoring,
                "execution": execution_result,
                "analysis": post_execution_analysis,
                "assessment": learning_assessment,
            }

            return {
                "session_id": trace_id,
                "topic": topic,
                "learning_materials": learning_materials,
                "execution_result": execution_result,
                "performance_analysis": post_execution_analysis,
                "learning_assessment": learning_assessment,
                "recommendations": post_execution_analysis.get("recommendations", []),
            }

        except Exception as e:
            logger.error(f"학습 세션 수행 실패: {e}")
            return {"error": f"학습 세션 실패: {e}"}

    def _assess_learning_outcome(
        self,
        baseline: MonitoringAnalysis,
        post: MonitoringAnalysis,
        materials: list[dict[str, Any]],
    ) -> LearningAssessment:
        """학습 성과 평가"""
        baseline_score = baseline.get("trinity_score", 0)
        post_score = post.get("trinity_score", 0)
        improvement = post_score - baseline_score

        materials_effective = len(materials) > 0
        execution_success = post.get("performance_analysis", {}).get("success_rate", 0) > 0.7

        assessment = {
            "baseline_trinity_score": baseline_score,
            "post_trinity_score": post_score,
            "improvement": improvement,
            "materials_effectiveness": materials_effective,
            "execution_success": execution_success,
            "overall_grade": self._calculate_learning_grade(
                improvement, materials_effective, execution_success
            ),
        }

        return assessment

    def _calculate_learning_grade(
        self, improvement: float, materials_effective: bool, execution_success: bool
    ) -> str:
        """학습 등급 계산"""
        score = 0

        if improvement > 15:
            score += 40  # 큰 개선
        elif improvement > 10:
            score += 30  # 중간 개선
        elif improvement > 5:
            score += 20  # 소폭 개선
        elif improvement > 0:
            score += 10  # 약간 개선

        if materials_effective:
            score += 30  # 자료 효과적 활용

        if execution_success:
            score += 30  # 실행 성공

        if score >= 80:
            return "A+ (탁월한 학습)"
        elif score >= 70:
            return "A (우수한 학습)"
        elif score >= 60:
            return "B+ (양호한 학습)"
        elif score >= 50:
            return "B (기초적인 학습)"
        elif score >= 40:
            return "C (추가 학습 필요)"
        else:
            return "D (학습 재시작 권장)"

    async def get_mentor_status(self) -> MentorStatus:
        """선생 시스템 상태 조회"""
        return {
            "status": "active",
            "langsmith_connected": self.langsmith_client is not None,
            "obsidian_librarian_connected": self.obsidian_librarian is not None,
            "active_learning_sessions": len(self.learning_sessions),
            "project_name": self.project_name,
        }

    def get_learning_history(self) -> LearningHistory:
        """학습 히스토리 조회"""
        return {
            "total_sessions": len(self.learning_sessions),
            "recent_sessions": list(self.learning_sessions.keys())[-5:],  # 최근 5개
            "session_details": self.learning_sessions,
        }


# 싱글톤 인스턴스
langsmith_mentor = LangSmithMentor()


async def get_langsmith_mentor() -> LangSmithMentor:
    """LangSmith 선생 인스턴스 조회 (싱글톤)"""
    return langsmith_mentor


async def initialize_langsmith_mentor() -> MentorInitStatus:
    """LangSmith 선생 시스템 초기화"""
    try:
        return await langsmith_mentor.initialize_mentor()
    except Exception as e:
        logger.error(f"LangSmith 선생 초기화 실패: {e}")
        return {"status": "failed", "error": str(e)}
