from __future__ import annotations

from typing import Any

from fastapi import APIRouter

# Trinity Score: 90.0 (Established by Chancellor)


router = APIRouter(prefix="/api/family", tags=["Family"])


@router.get("/health")
async def family_health() -> dict[str, Any]:
    return {"status": "healthy", "mode": "stateless"}
