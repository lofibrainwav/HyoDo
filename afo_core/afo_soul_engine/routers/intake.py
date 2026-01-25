from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

# Trinity Score: 90.0 (Established by Chancellor)


router = APIRouter(prefix="/api/intake", tags=["Intake"])


class IntakeRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    source: str = Field(default="unknown")


@router.post("/ingest")
async def ingest(request: IntakeRequest) -> dict[str, Any]:
    """Stateless intake endpoint (persistence can be wired later)."""
    return {"status": "accepted", "source": request.source, "payload": request.payload}


@router.get("/health")
async def intake_health() -> dict[str, Any]:
    return {"status": "healthy", "mode": "stateless"}
