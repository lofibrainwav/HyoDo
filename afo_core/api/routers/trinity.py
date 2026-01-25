# Trinity Score: 95.0 (Established by Chancellor)
"""
Trinity Router
Phase 66+: Trinity Score API (Soul System - 魂)
眞善美孝永 5기둥 점수 조회 및 계산
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from starlette.requests import Request

from AFO.domain.metrics.trinity_manager import trinity_manager
from AFO.utils.standard_shield import shield

router = APIRouter()


class TrinityScoreResponse(BaseModel):
    """Trinity Score 응답 (Phase 69 Extended)"""

    status: str = "healthy"
    # Make fields optional or use extra for flexibility, or define strict schema
    global_metrics: dict[str, Any]
    agents: dict[str, dict[str, Any]]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


@router.get("/health")
@shield(pillar="善", log_error=True, reraise=False)
async def trinity_health(request: Request) -> dict[str, Any]:
    """Trinity (Soul) 상태 조회"""
    return {
        "status": "healthy",
        "message": "Trinity Score Engine Operational (Phase 69)",
        "pillars": ["眞", "善", "美", "孝", "永"],
        "agents": list(trinity_manager.agent_deltas.keys()),
    }


@router.get("/")
@shield(pillar="善", log_error=True, reraise=False)
async def get_trinity_status(request: Request) -> dict[str, Any]:
    """현재 Trinity Score 상태 조회 (Global + Agents)"""
    all_metrics = trinity_manager.get_all_metrics()
    return {
        "status": "healthy",
        "global_metrics": all_metrics["global"],
        "agents": all_metrics["agents"],
        "timestamp": datetime.now().isoformat(),
    }


@router.get("/current")
@shield(pillar="善", log_error=True, reraise=False)
async def get_current_score(request: Request) -> dict[str, Any]:
    """현재 점수 조회 (Global Summary)"""
    metrics = trinity_manager.get_current_metrics()
    return {
        "score": round(metrics.trinity_score * 100, 2),
        "decision": "AUTO_RUN" if metrics.trinity_score >= 0.9 else "ASK",
        "balance": metrics.balance_status,
        "metrics": metrics.to_dict(),
    }
