# Trinity Score: 90.0 (Established by Chancellor)
"""
Root Router
Phase 2 리팩토링: Root 엔드포인트 분리
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def read_root() -> dict[str, str]:
    """
    루트 엔드포인트 - API 정보 반환
    """
    return {
        "name": "AFO Kingdom Soul Engine API",
        "version": "6.3.0",
        "description": "眞善美孝永 (Truth, Goodness, Beauty, Serenity, Eternity)",
        "status": "running",
    }


# api_server.py의 read_root_legacy에서 사용하기 위해 함수 export
__all__ = ["read_root", "router"]
