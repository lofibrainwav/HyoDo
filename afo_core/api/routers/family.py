from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from AFO.utils.standard_shield import shield
from application.family.service import family_service

router = APIRouter(prefix="/api/family", tags=["Family Hub (L4)"])


@shield(pillar="善")
@router.get("/health")
async def health_check():
    """Health check for Family Hub."""
    return {"status": "healthy", "service": "family-hub"}


class DashboardResponse(BaseModel):
    hero_status: dict[str, Any]
    active_quests: list[dict[str, Any]]
    homework_pending: int


@shield(pillar="善")
@router.get("/dashboard/{user_id}", response_model=DashboardResponse)
async def get_family_dashboard(user_id: str):
    """
    aggregated view for Family Hub Dashboard.
    returns Hero Status + Active Quests + Homework Count.
    """
    try:
        data = await family_service.get_dashboard_data(user_id)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@shield(pillar="善")
@router.post("/quests/{quest_id}/approve")
async def approve_quest(quest_id: str, parent_id: str):
    """
    Parent approves a quest completion.
    """
    success = await family_service.approve_quest(quest_id, parent_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to approve quest")

    return {"status": "approved", "quest_id": quest_id}
