# Trinity Score: 95.0 (Established by Chancellor)
"""
Feedback Loop Manager

피드백 루프 관리 클래스. sharing_system_full.py에서 추출됨.
비동기 피드백 분석, 패턴 학습, 자동 최적화.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .collaboration_analysis import calculate_variance

if TYPE_CHECKING:
    from .models import TrinityScoreUpdate
    from .optimizer import TrinityScoreOptimizer

logger = logging.getLogger(__name__)


class FeedbackLoopManager:
    """피드백 루프 관리자"""

    def __init__(
        self,
        optimization_engine: TrinityScoreOptimizer,
        cleanup_interval: int = 300,
    ) -> None:
        self.optimization_engine = optimization_engine
        self.cleanup_interval = cleanup_interval
        self.feedback_tasks: dict[str, asyncio.Task[None]] = {}
        self.feedback_loops_active = 0

    def should_start_feedback_loop(
        self,
        session_id: str,
        score_history: dict[str, list[TrinityScoreUpdate]],
    ) -> bool:
        """피드백 루프 시작 필요성 판단"""
        if session_id not in score_history:
            return False

        recent_updates = [
            u
            for u in score_history[session_id]
            if (datetime.now() - datetime.fromisoformat(u.timestamp)).seconds < 300
        ]  # 최근 5분

        # 최근 업데이트가 많으면 피드백 루프 시작
        return len(recent_updates) >= 5

    async def start_feedback_loop(
        self,
        session_id: str,
        score_pools: dict[str, dict[str, float]],
        score_history: dict[str, list[TrinityScoreUpdate]],
    ) -> None:
        """피드백 루프 시작"""
        if session_id in self.feedback_tasks:
            return  # 이미 실행 중

        feedback_task = asyncio.create_task(
            self._run_feedback_loop(session_id, score_pools, score_history)
        )
        self.feedback_tasks[session_id] = feedback_task
        self.feedback_loops_active += 1

        logger.info(f"Feedback loop started for session: {session_id}")

    async def _run_feedback_loop(
        self,
        session_id: str,
        score_pools: dict[str, dict[str, float]],
        score_history: dict[str, list[TrinityScoreUpdate]],
    ) -> None:
        """피드백 루프 실행"""
        try:
            while True:
                await asyncio.sleep(60)  # 1분마다 실행

                # 세션이 여전히 활성인지 확인
                if session_id not in score_pools:
                    break

                # 피드백 분석 및 최적화
                feedback_result = await self.analyze_feedback_and_optimize(
                    session_id, score_pools, score_history
                )

                # 최적화 적용
                if feedback_result.get("optimization_applied", False):
                    logger.info(f"Feedback optimization applied for session: {session_id}")

                # 수렴 상태 확인
                if feedback_result.get("convergence_achieved", False):
                    logger.info(f"Convergence achieved for session: {session_id}")
                    break

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in feedback loop for {session_id}: {e}")
        finally:
            # 태스크 정리
            if session_id in self.feedback_tasks:
                del self.feedback_tasks[session_id]
                self.feedback_loops_active -= 1

    async def analyze_feedback_and_optimize(
        self,
        session_id: str,
        score_pools: dict[str, dict[str, float]],
        score_history: dict[str, list[TrinityScoreUpdate]],
    ) -> dict[str, Any]:
        """피드백 분석 및 최적화"""
        if session_id not in score_pools or session_id not in score_history:
            return {"error": "Session data not found"}

        current_scores = score_pools[session_id]
        recent_history = score_history[session_id][-10:]  # 최근 10개 업데이트

        # 피드백 패턴 분석
        pattern_analysis = self.analyze_feedback_patterns(recent_history)

        # 최적화 필요성 판단
        needs_optimization = self.assess_optimization_need(pattern_analysis, current_scores)

        result: dict[str, Any] = {
            "pattern_analysis": pattern_analysis,
            "needs_optimization": needs_optimization,
            "optimization_applied": False,
            "convergence_achieved": False,
        }

        if needs_optimization:
            # 최적화 실행
            optimization_result = await self.optimization_engine.apply_feedback_optimization(
                session_id, current_scores, pattern_analysis
            )

            if optimization_result.get("success"):
                result["optimization_applied"] = True

                # 새로운 점수 적용
                updated_scores = optimization_result.get("updated_scores", {})
                score_pools[session_id].update(updated_scores)

        # 수렴 상태 확인
        convergence_status = self._check_convergence(current_scores)
        result["convergence_achieved"] = convergence_status == "converged"

        return result

    def analyze_feedback_patterns(
        self,
        recent_updates: list[TrinityScoreUpdate],
    ) -> dict[str, Any]:
        """피드백 패턴 분석"""
        if not recent_updates:
            return {"error": "No recent updates"}

        return {
            "update_frequency": len(recent_updates),
            "average_change": sum(abs(u.new_score - u.previous_score) for u in recent_updates)
            / len(recent_updates),
            "collaboration_trend": sum(u.collaboration_impact for u in recent_updates)
            / len(recent_updates),
            "agent_participation": len({u.agent_type for u in recent_updates}),
            "most_active_agent": max(
                {u.agent_type for u in recent_updates},
                key=lambda x: sum(1 for u in recent_updates if u.agent_type == x),
            ),
        }

    def assess_optimization_need(
        self,
        pattern_analysis: dict[str, Any],
        current_scores: dict[str, float],
    ) -> bool:
        """최적화 필요성 평가"""
        # 점수 분산이 큰 경우
        score_variance = calculate_variance(list(current_scores.values()))
        if score_variance > 0.2:
            return True

        # 업데이트 빈도가 낮은 경우
        update_frequency = pattern_analysis.get("update_frequency", 0)
        if update_frequency < 2:
            return True

        # 협업 영향이 낮은 경우
        collaboration_trend = pattern_analysis.get("collaboration_trend", 0)
        return collaboration_trend < 0.3

    def _check_convergence(self, scores: dict[str, float]) -> str:
        """수렴 상태 확인"""
        variance = calculate_variance(list(scores.values()))

        if variance < 0.05:
            return "converged"
        elif variance < 0.15:
            return "converging"
        else:
            return "diverging"

    async def cleanup_expired_feedback_loops(
        self,
        score_pools: dict[str, dict[str, float]],
        score_history: dict[str, list[TrinityScoreUpdate]],
    ) -> None:
        """만료된 피드백 루프 정리"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)

                expired_sessions = []

                for session_id in list(self.feedback_tasks.keys()):
                    # 세션이 존재하지 않거나 오래된 경우
                    if session_id not in score_pools:
                        expired_sessions.append(session_id)
                    elif score_history.get(session_id):
                        last_update = max(
                            datetime.fromisoformat(u.timestamp)
                            for u in score_history[session_id][-1:]
                        )
                        if (datetime.now() - last_update).seconds > 3600:  # 1시간 이상 비활성
                            expired_sessions.append(session_id)

                    # 태스크가 이미 완료된 경우
                    if session_id in self.feedback_tasks and self.feedback_tasks[session_id].done():
                        expired_sessions.append(session_id)

                # 만료된 태스크 정리
                for session_id in expired_sessions:
                    if session_id in self.feedback_tasks:
                        task = self.feedback_tasks[session_id]
                        if not task.done():
                            task.cancel()
                        del self.feedback_tasks[session_id]

                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired feedback loops")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feedback loop cleanup: {e}")

    async def stop_all(self) -> None:
        """모든 피드백 태스크 중지"""
        for task_name, task in self.feedback_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self.feedback_tasks.clear()
        self.feedback_loops_active = 0


__all__ = [
    "FeedbackLoopManager",
]
