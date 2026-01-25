import logging

from fastapi import APIRouter

from AFO.utils.standard_shield import shield

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/v")
async def probe_version():
    return {"version": "micro-v1"}


@router.get("/fail")
@shield(default_return={"error": "shielded_gracefully"})
async def trigger_failure():
    raise ValueError("Microscopic Logic Test: Failure Injection")
