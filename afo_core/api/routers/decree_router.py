import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from AFO.evolution.dgm_engine import EvolutionMetadata, dgm_engine
from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evolution/decrees", tags=["Royal Decrees"])


class DecreeAction(BaseModel):
    action: str  # SEAL, VETO
    reason: str | None = None


@shield(pillar="善")
@router.get("/", response_model=list[EvolutionMetadata])
async def list_decrees(status: str = "PENDING"):
    """List evolution proposals (decrees) filtered by status."""
    history = dgm_engine.chronicle.get_history()
    return [h for h in history if h.decree_status == status]


@shield(pillar="善")
@router.post("/{run_id}/seal")
async def seal_decree(run_id: str):
    """
    Formally approve (SEAL) an evolution proposal.
    In WET mode, this would trigger the actual code deployment.
    """
    success = dgm_engine.chronicle.update_decree_status(run_id, "APPROVED")
    if not success:
        raise HTTPException(status_code=404, detail="Decree not found")

    logger.info(f"👑 Royal Decree SEALED for run_id: {run_id}. Execution pending WET deployment.")
    return {
        "status": "SEALED",
        "run_id": run_id,
        "message": "The Commander has sealed this decree.",
    }


@shield(pillar="善")
@router.post("/{run_id}/veto")
async def veto_decree(run_id: str, reason: str | None = None):
    """Formally reject (VETO) an evolution proposal."""
    success = dgm_engine.chronicle.update_decree_status(run_id, "REJECTED")
    if not success:
        raise HTTPException(status_code=404, detail="Decree not found")

    logger.info(f"🛡️ Royal Decree VETOED for run_id: {run_id}. Reason: {reason or 'None'}")
    return {
        "status": "VETOED",
        "run_id": run_id,
        "message": "The Commander has vetoed this decree.",
    }
