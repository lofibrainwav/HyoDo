# Trinity Score: 90.0 (Established by Chancellor)
"""
Health Check Router
Phase 2 리팩토링: Health 엔드포인트 분리
"""

from typing import Any

from fastapi import APIRouter

# Phase 2 리팩토링: 상대 import 사용
# Phase 2 리팩토링: 표준 import 사용
from AFO.services.database import get_db_connection
from AFO.utils.redis_connection import get_redis_url
from AFO.utils.standard_shield import shield

router = APIRouter(prefix="/health", tags=["Health"])

# Comprehensive Health Check 통합
try:
    from AFO.api.routes.comprehensive_health import (
        router as comprehensive_health_router,
    )
    # comprehensive_health_router는 이미 prefix="/api/health"를 가지고 있으므로
    # health_router에 직접 통합하면 경로가 중복될 수 있음
    # 대신 api_server.py에서 모드로 등록하는 것이 좋음
    # 여기서는 주석 처리하고 api_server.py에서 처리
    # router.include_router(comprehensive_health_router)
except ImportError:
    pass  # comprehensive_health가 없어도 기본 health check는 작동


@shield(pillar="善", log_error=True)
@router.get("")
async def health_check() -> dict[str, Any]:
    """
    시스템 건강 상태 체크 (11-Org Health Monitoring)
    Refactored to use centralized health_service.
    """
    from AFO.services.health_service import get_comprehensive_health

    return await get_comprehensive_health()


@shield(pillar="善", log_error=True)
@router.get("/ping")
async def health_ping() -> dict[str, str]:
    """
    경량 핑스체크 (로드밸런서/프로브용)
    전체 시스템 체크 없이 즉시 응답
    """
    return {"status": "ok", "service": "afo-kingdom"}
