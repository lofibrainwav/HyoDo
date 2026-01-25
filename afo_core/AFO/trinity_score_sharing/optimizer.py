"""Trinity Score Optimizer

Trinity Score 최적화 알고리즘 및 전략 구현.
"""

from typing import Any

from .models import TrinityScoreUpdate


class TrinityScoreOptimizer:
    """Trinity Score 최적화 엔진"""

    def __init__(self) -> None:
        self.optimization_algorithms = {
            "collaborative_boosting": self._collaborative_boosting,
            "consensus_driven": self._consensus_driven,
            "performance_based": self._performance_based,
        }

    async def optimize_scores(
        self,
        current_scores: dict[str, float],
        score_history: list[TrinityScoreUpdate],
        session_id: str,
    ) -> dict[str, Any]:
        """점수 최적화 실행"""

        # 최적화 전략 선택
        strategy = self._select_optimization_strategy(current_scores, score_history)

        # 최적화 실행
        optimization_result = await self.optimization_algorithms[strategy](
            current_scores, score_history, session_id
        )

        return {
            "success": True,  # For test compatibility
            "strategy": strategy,  # Alias for tests
            "strategy_used": strategy,
            "optimization_result": optimization_result,
            "optimized_scores": optimization_result.get("optimized_scores", {}),
            "adjustments": optimization_result.get("adjustments", {}),
            "confidence_level": self._calculate_optimization_confidence(optimization_result),
        }

    def _select_optimization_strategy(
        self, scores: dict[str, float], history: list[TrinityScoreUpdate]
    ) -> str:
        """최적화 전략 선택"""

        # 점수 분산 분석
        variance = sum(
            (score - sum(scores.values()) / len(scores)) ** 2 for score in scores.values()
        ) / len(scores)

        # 협업 이벤트 분석
        collaboration_events = sum(1 for update in history if update.collaboration_impact > 0.5)

        if variance > 0.2:  # 높은 분산
            return "consensus_driven"
        elif collaboration_events > len(history) * 0.7:  # 높은 협업
            return "collaborative_boosting"
        else:
            return "performance_based"

    async def _collaborative_boosting(
        self, scores: dict[str, float], history: list[TrinityScoreUpdate], session_id: str
    ) -> dict[str, Any]:
        """협업 부스팅 최적화"""

        optimized_scores = scores.copy()

        # 협업이 활발한 Agent에게 보너스
        for agent_type in scores.keys():
            agent_collaboration = sum(
                update.collaboration_impact for update in history if update.agent_type == agent_type
            )

            # 협업 점수에 따른 보너스 (최대 +0.05)
            bonus = min(agent_collaboration * 0.01, 0.05)
            optimized_scores[agent_type] = min(1.0, scores[agent_type] + bonus)

        return {
            "optimized_scores": optimized_scores,
            "adjustments": {
                agent: optimized_scores[agent] - scores[agent] for agent in scores.keys()
            },
            "reason": "Collaborative performance boosting",
        }

    async def _consensus_driven(
        self, scores: dict[str, float], history: list[TrinityScoreUpdate], session_id: str
    ) -> dict[str, Any]:
        """합의 기반 최적화"""

        optimized_scores = scores.copy()

        # 평균 점수 계산
        avg_score = sum(scores.values()) / len(scores)

        # 평균에서 벗어난 점수들을 평균으로 끌어당김
        for agent_type in scores.keys():
            deviation = scores[agent_type] - avg_score
            adjustment = -deviation * 0.3  # 30% 조정

            optimized_scores[agent_type] = max(0.0, min(1.0, scores[agent_type] + adjustment))

        return {
            "optimized_scores": optimized_scores,
            "adjustments": {
                agent: optimized_scores[agent] - scores[agent] for agent in scores.keys()
            },
            "reason": "Consensus-driven score alignment",
        }

    async def _performance_based(
        self, scores: dict[str, float], history: list[TrinityScoreUpdate], session_id: str
    ) -> dict[str, Any]:
        """성능 기반 최적화"""

        optimized_scores = scores.copy()

        # 최근 성과 기반 조정
        recent_updates = history[-10:]  # 최근 10개 업데이트

        for agent_type in scores.keys():
            agent_recent_updates = [
                update for update in recent_updates if update.agent_type == agent_type
            ]

            if agent_recent_updates:
                # 최근 변화 추세 분석
                changes = [
                    update.new_score - update.previous_score for update in agent_recent_updates
                ]
                avg_change = sum(changes) / len(changes)

                # 긍정적 추세면 약간의 보너스
                if avg_change > 0.01:
                    bonus = min(avg_change * 0.5, 0.03)
                    optimized_scores[agent_type] = min(1.0, scores[agent_type] + bonus)

        return {
            "optimized_scores": optimized_scores,
            "adjustments": {
                agent: optimized_scores[agent] - scores[agent] for agent in scores.keys()
            },
            "reason": "Performance-based trend optimization",
        }

    async def apply_feedback_optimization(
        self, session_id: str, current_scores: dict[str, float], pattern_analysis: dict[str, Any]
    ) -> dict[str, Any]:
        """피드백 기반 최적화 적용"""

        # 패턴 기반 최적화 전략 선택
        strategy = "performance_based"  # 기본값

        update_frequency = pattern_analysis.get("update_frequency", 0)
        collaboration_trend = pattern_analysis.get("collaboration_trend", 0)

        if update_frequency > 10 and collaboration_trend > 0.6:
            strategy = "collaborative_boosting"
        elif update_frequency < 5:
            strategy = "consensus_driven"

        # 최적화 실행
        optimization_result = await self.optimization_algorithms[strategy](
            current_scores,
            [],
            session_id,  # 빈 히스토리
        )

        return {
            "success": True,
            "strategy": strategy,
            "strategy_used": strategy,
            "updated_scores": optimization_result["optimized_scores"],
            "adjustments": optimization_result["adjustments"],
            "optimization_result": optimization_result,
            "pattern_analysis": pattern_analysis,
        }

    def _calculate_optimization_confidence(self, optimization_result: dict[str, Any]) -> float:
        """최적화 신뢰도 계산"""

        adjustments = optimization_result.get("adjustments", {})
        total_adjustment = sum(abs(adj) for adj in adjustments.values())

        # 조정량이 적을수록 신뢰도가 높음 (급격한 변화는 불안정)
        if total_adjustment < 0.05:
            return 0.95
        elif total_adjustment < 0.1:
            return 0.85
        elif total_adjustment < 0.2:
            return 0.75
        else:
            return 0.65
