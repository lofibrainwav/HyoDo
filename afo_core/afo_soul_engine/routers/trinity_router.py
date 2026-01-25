from __future__ import annotations

from typing import Any

from fastapi import APIRouter

# Trinity Score: 90.0 (Established by Chancellor)


router = APIRouter(prefix="/api/trinity", tags=["Trinity"])


@router.get("/health")
async def trinity_health() -> dict[str, Any]:
    return {"status": "healthy", "message": "Trinity router online"}
