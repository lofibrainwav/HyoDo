"""Trinity Score Sharing Service Package.

에이전트 간의 Trinity Score 공유, 분석 및 동기화 서비스.
협업 최적화를 통해 전체 시스템의 眞善美 균형을 유지함.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .analysis import analyze_score_distribution, calculate_collaboration_intensity
from .sync import broadcast_score_update, synchronise_scores


class TrinityScoreSharingSystem:
    """Trinity Score 공유 및 협업 최적화 시스템 (Facade)."""

    def __init__(self) -> None:
        self.sessions_data: dict[str, dict[str, Any]] = {}
        self.optimization_history: dict[str, list] = {}
        self.is_running: bool = False
        self.logger = logging.getLogger(__name__)

    @property
    def score_pools(self) -> dict[str, dict[str, Any]]:
        """레거시 테스트 호환성을 위한 별칭."""
        return self.sessions_data

    def start(self) -> None:
        """시스템을 시작합니다."""
        self.is_running = True
        self.logger.info("TrinityScoreSharingSystem started")

    def stop(self) -> None:
        """시스템을 중지합니다."""
        self.is_running = False
        self.logger.info("TrinityScoreSharingSystem stopped")

    async def share_trinity_score(
        self,
        agent_type: str,
        session_id: str,
        new_score: float,
        change_reason: str,
        contributing_factors: dict[str, float],
    ) -> dict[str, Any]:
        """실시간으로 점수를 공유하고 브로드캐스트합니다."""
        if session_id not in self.sessions_data:
            self.sessions_data[session_id] = {}

        self.sessions_data[session_id][agent_type] = {
            "score": new_score,
            "reason": change_reason,
            "updated_at": datetime.now().isoformat(),
        }

        broadcast_score_update(session_id, agent_type, new_score)

        return {"success": True, "session_id": session_id}

    async def get_collaborative_trinity_score(
        self, session_id: str, agent_type: str, include_optimization: bool = True
    ) -> float:
        """세션 내 협업 시너지가 반영된 최종 점수를 계산합니다."""
        session_scores = {k: v["score"] for k, v in self.sessions_data.get(session_id, {}).items()}
        if not session_scores:
            return 0.0

        dist = analyze_score_distribution(session_scores)
        return dist.get("average", 0.0)

    def get_sharing_stats(self) -> dict[str, Any]:
        """시스템 전체 공유 통계를 반환합니다."""
        return {
            "active_sessions": len(self.sessions_data),
            "total_agents_sharing": sum(len(s) for s in self.sessions_data.values()),
            "timestamp": datetime.now().isoformat(),
        }


__all__ = ["TrinityScoreSharingSystem"]
