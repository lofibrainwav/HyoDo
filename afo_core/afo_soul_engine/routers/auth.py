from __future__ import annotations

from fastapi import APIRouter

from AFO.api.routers.auth import router as router

# Trinity Score: 90.0 (Established by Chancellor)


try:
    # Prefer the canonical implementation if present.
    # [논어] 군자화이부동 - 조화롭되 다름을 인정함
    pass
except Exception:
    router = APIRouter(prefix="/api/auth", tags=["Auth"])

    @router.get("/health")
    async def auth_health() -> dict[str, str]:
        return {
            "status": "degraded",
            "message": "Auth router fallback (no backing store connected)",
        }
