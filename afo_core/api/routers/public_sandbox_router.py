import logging

from fastapi import APIRouter, HTTPException

from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/sandbox", tags=["Public Sandbox"])


@shield(pillar="善")
@router.get("/validate")
async def public_validation_mock():
    """
    Mock endpoint for external entities to validate the kingdom's reliability index.
    In 14-B, this provides a safe, read-only view of the civilization metrics.
    """
    return {
        "verified_by": "AFO Sovereign Audit",
        "reliability_index": 0.982,
        "governance_status": "ACTIVE",
        "civilization_phase": "14-B: Preparation",
        "external_exposure": "LOCKED",
    }


@shield(pillar="善")
@router.get("/rules")
async def get_public_constitution():
    """Returns the Public Constitution summarized for external transparency."""
    return {
        "motto": "Provable Progress, Absolute Serenity",
        "pillars": ["Truth", "Goodness", "Beauty", "Serenity", "Eternity"],
        "compliance": "Human-in-the-Loop Governance",
    }
