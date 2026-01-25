import logging
import os

from fastapi import APIRouter, Depends, HTTPException

from AFO.evolution.dgm_engine import EvolutionMetadata, dgm_engine
from AFO.evolution.evolution_gate import EvolutionProposal, evolution_gate
from AFO.governance.kill_switch import sentry
from AFO.governance.persona_auth import persona_auth
from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/evolution",
    tags=["Evolution"],
    dependencies=[Depends(persona_auth.get_current_persona)],
)


@shield(pillar="善")
@router.post("/improve", response_model=EvolutionMetadata)
async def trigger_evolution(component: str = "core"):
    """
    Trigger a DGM self-improvement step for a specific component.
    Blocked by kill-switch if active.
    """
    if sentry.is_locked():
        raise HTTPException(status_code=403, detail="Civilization in lockdown. Access denied.")

    try:
        metadata = await dgm_engine.evolve_step(component=component)
        return metadata
    except Exception as e:
        logger.exception(f"Evolution step failed for {component}")
        raise HTTPException(status_code=500, detail=str(e))


@shield(pillar="善")
@router.post("/sovereignty/lock")
async def civilization_lock(reason: str = "Manual Trigger"):
    """Activate Emergency Kill-Switch."""
    sentry.lock(reason)
    return {"status": "LOCKED", "reason": reason}


@shield(pillar="善")
@router.post("/sovereignty/unlock")
async def civilization_unlock():
    """Restore Sovereignty."""
    sentry.unlock()
    return {"status": "UNLOCKED"}


@shield(pillar="善")
@router.get("/history", response_model=list[EvolutionMetadata])
async def get_evolution_history():
    """
    Retrieve the history of self-improvement generations.
    """
    if not os.path.exists(dgm_engine.metadata_path):
        return []

    history = []
    with open(dgm_engine.metadata_path) as f:
        for line in f:
            history.append(EvolutionMetadata.parse_raw(line))
    return history


@shield(pillar="善")
@router.post("/verify")
async def verify_evolution_proposal(proposal: EvolutionProposal):
    """
    Submit a proposed modification to Sima Yi's Shield for safety verification.
    """
    result = evolution_gate.verify_proposal(proposal)
    return result
