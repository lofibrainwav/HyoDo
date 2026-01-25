from __future__ import annotations

from fastapi import APIRouter

from AFO.api.routers.users import router as router

# Trinity Score: 90.0 (Established by Chancellor)


try:
    # [논어] 기소불욕물시어인 - 자신이 원치 않는 것 남에게 하지 말라
    pass
except Exception:
    router = APIRouter(prefix="/api/users", tags=["Users"])

    @router.get("/health")
    async def users_health() -> dict[str, str]:
        return {
            "status": "degraded",
            "message": "Users router fallback (no persistence connected)",
        }
