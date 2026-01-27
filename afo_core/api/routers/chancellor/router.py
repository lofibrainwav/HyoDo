"""
Chancellor Router - API 엔드포인트
Phase 3: Chancellor Graph API 엔드포인트
LangGraph 기반 3책사 (Jang Yeong-sil/Yi Sun-sin/Shin Saimdang) 시스템
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from api.routers.chancellor.executors import execute_with_fallback
from api.routers.chancellor.helpers import (
    build_llm_context,
    determine_execution_mode,
    get_v2_settings,
)
from api.routers.chancellor.imports import (
    BASE_CONFIG,
    ChancellorInvokeRequest,
    ChancellorInvokeResponse,
    _get_cached_engine_status,
    _learning_loader_available,
    _rag_flag_available,
    _rag_shadow_available,
    _v2_runner_available,
    apply_learning_profile,
    chancellor_graph,
    get_learning_profile,
    get_rag_config,
    get_shadow_metrics,
    is_rag_shadow_enabled,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chancellor", tags=["Chancellor"])


# ═══════════════════════════════════════════════════════════════════════════════
# 엔진 상태 엔드포인트
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/engines")
async def chancellor_engines() -> dict[str, Any]:
    """
    Chancellor AI 엔진 설치 상태 확인 (캐시 최적화)

    Trinity Score: 眞 (Truth) - 정확한 라이브러리 상태
    """
    return {"installed": _get_cached_engine_status()}


# ═══════════════════════════════════════════════════════════════════════════════
# 메인 호출 엔드포인트
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/invoke")
async def invoke_chancellor(
    request: ChancellorInvokeRequest,
    http_request: Request,
) -> ChancellorInvokeResponse:
    """
    Chancellor Graph 호출 엔드포인트 (Strangler Fig 적용)

    Phase 24 Scaling:
    - X-AFO-Engine: v2 헤더 지원
    - Shadow 모드 자동 적용 (백그라운드 Diff)
    """
    try:
        headers = dict(http_request.headers)

        mode_used = determine_execution_mode(request)
        llm_context = build_llm_context(request)
        result = await execute_with_fallback(mode_used, request, llm_context, headers)

        # Pydantic Response Mapping
        if "response" in result and "result" not in result:
            result["result"] = result["response"]
        if "engine_used" not in result:
            result["engine_used"] = result.get("speaker", "Chancellor")
        if "execution_time" not in result:
            result["execution_time"] = 1.0
        if "mode" not in result:
            result["mode"] = mode_used

        return ChancellorInvokeResponse(**result)

    except HTTPException:
        raise
    except BaseException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chancellor Graph crashed: {type(e).__name__}: {e}",
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 헬스 체크 엔드포인트
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/health")
async def chancellor_health() -> dict[str, Any]:
    """Chancellor Graph 건강 상태 체크"""
    if chancellor_graph is None and not _v2_runner_available:
        return {
            "status": "unavailable",
            "message": "Chancellor Graph (V1/V2)가 초기화되지 않았습니다.",
        }

    try:
        return {
            "status": "healthy",
            "message": "Chancellor Graph 정상 작동 중",
            "strategists": ["Jang Yeong-sil", "Yi Sun-sin", "Shin Saimdang"],
        }
    except (ImportError, AttributeError, RuntimeError) as e:
        logger.error("Chancellor Graph 초기화 실패: %s", str(e))
        return {"status": "error", "message": f"Chancellor Graph 초기화 실패: {e!s}"}
    except Exception as e:
        logger.error("Chancellor Graph 초기화 실패 (예상치 못한 에러): %s", str(e))
        return {"status": "error", "message": f"Chancellor Graph 초기화 실패: {e!s}"}


@router.get("/learning/health")
async def learning_profile_health() -> dict[str, Any]:
    """Learning Profile Boot-Swap 상태 체크 (TICKET-007)"""
    if not _learning_loader_available:
        return {
            "status": "unavailable",
            "message": "Learning profile loader가 초기화되지 않았습니다.",
            "available": False,
        }

    try:
        profile = get_learning_profile()
        response = profile.to_dict()
        effective_config = apply_learning_profile(
            BASE_CONFIG,
            profile.data.get("overrides", {}),
        )
        response["effective_config"] = effective_config
        return response
    except Exception as e:
        logger.error("Learning profile health check failed: %s", str(e))
        return {
            "status": "error",
            "message": f"Learning profile health check failed: {e!s}",
            "available": False,
        }


@router.get("/rag/shadow/health")
async def rag_shadow_health() -> dict[str, Any]:
    """RAG Shadow + Flag 모드 상태 체크 (TICKET-008)"""
    response: dict[str, Any] = {
        "shadow": {"available": False, "enabled": False},
        "flag": {"available": False, "enabled": False, "config": None},
        "overall_status": "partial",
    }

    # Shadow 모드 상태
    if _rag_shadow_available:
        try:
            shadow_enabled = is_rag_shadow_enabled()
            response["shadow"] = {"available": True, "enabled": shadow_enabled}

            if shadow_enabled:
                metrics = await get_shadow_metrics(limit=50)
                response["shadow"]["metrics"] = metrics
        except Exception as e:
            logger.error("RAG Shadow health check failed: %s", str(e))
            response["shadow"]["error"] = str(e)

    # Flag 모드 상태
    if _rag_flag_available:
        try:
            config = get_rag_config()
            response["flag"] = {
                "available": True,
                "enabled": config["flag_enabled"] == "1",
                "config": config,
            }
        except Exception as e:
            logger.error("RAG Flag health check failed: %s", str(e))
            response["flag"]["error"] = str(e)

    # 전체 상태 결정
    shadow_ok = response["shadow"]["available"] and response["shadow"]["enabled"]
    flag_ok = response["flag"]["available"]

    if shadow_ok and flag_ok:
        response["overall_status"] = "enabled"
        response["message"] = "RAG Shadow + Flag 모드 정상 작동 중"
    elif shadow_ok or flag_ok:
        response["overall_status"] = "partial"
        response["message"] = "RAG 모드 부분 활성화됨"
    else:
        response["overall_status"] = "disabled"
        response["message"] = "RAG 모드 비활성화됨"

    return response


# ═══════════════════════════════════════════════════════════════════════════════
# V2 라우팅 상태 엔드포인트 (Phase 23-24)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/v2/status")
async def v2_routing_status() -> dict[str, Any]:
    """
    Chancellor V2 라우팅 상태 확인 (Phase 23-24).

    Returns:
        V2 라우팅 설정 및 가용성 정보
    """
    settings = get_v2_settings()

    return {
        "v2_available": _v2_runner_available,
        "settings": {
            "enabled": settings["enabled"],
            "header_routing": settings["header_routing"],
            "canary_percent": settings["canary_percent"],
            "shadow_mode": settings["shadow_mode"],
            "fallback_to_v1": settings["fallback_to_v1"],
        },
        "routing_modes": {
            "header": "X-AFO-Engine 헤더 (v1, v2, shadow)",
            "canary": f"{settings['canary_percent']}% 트래픽이 V2로 라우팅됨",
            "shadow": "V2 백그라운드 실행, V1 응답 반환" if settings["shadow_mode"] else "비활성화",
        },
        "usage": {
            "force_v2": "curl -H 'X-AFO-Engine: v2' ...",
            "force_v1": "curl -H 'X-AFO-Engine: v1' ...",
            "shadow_test": "curl -H 'X-AFO-Engine: shadow' ...",
        },
    }
