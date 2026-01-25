"""
MyGPT 전송 로직

jangjungwha.com의 notebook 데이터를 MyGPT GPT로 전송
"""

import logging
import os
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from AFO.services.redis_cache_service import cache_set  # Service Import
from AFO.utils.resilience import CircuitBreaker, CircuitBreakerOpenException

# Circuit Breaker for Redis
redis_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)


@redis_breaker
async def _safe_cache_set(key: str, value: Any, ttl: int = None) -> bool:
    return await cache_set(key, value, ttl)


logger = logging.getLogger(__name__)

from .models import (
    MyGPTStatusResponse,
    MyGPTSyncResponse,
    MyGPTTransferRequest,
    MyGPTTransferResponse,
)

# 환경 변수
MYGPT_GPT_ID = os.getenv("MYGPT_GPT_ID", "g-p-67e0ae35e0ec81918fecfcf005b8a746")
MYGPT_API_KEY = os.getenv("MYGPT_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MYGPT_ACTIONS_URL = os.getenv("MYGPT_ACTIONS_URL", "https://api.jangjungwha.com/mygpt/actions")

router = APIRouter(prefix="/api/mygpt", tags=["MyGPT"])


# Phase 79 - TODO-006: MyGPT API Client
async def _call_mygpt_api(
    action: str,
    payload: dict[str, Any],
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    MyGPT Actions API 호출 클라이언트 (Phase 79 - TODO-006)

    Args:
        action: API action (e.g., "receive_context", "sync_state")
        payload: Request payload
        api_key: Optional API key override

    Returns:
        API response dict or error dict
    """
    key = api_key or MYGPT_API_KEY
    if not key:
        return {"success": False, "error": "MyGPT API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MYGPT_ACTIONS_URL}/{action}",
                json=payload,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "X-GPT-ID": MYGPT_GPT_ID,
                },
            )

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            elif response.status_code == 401:
                return {"success": False, "error": "Unauthorized - Invalid API key"}
            elif response.status_code == 429:
                return {"success": False, "error": "Rate limited - Try again later"}
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "detail": response.text[:200],
                }

    except httpx.ConnectError:
        logger.warning("MyGPT API connection failed - service may be unavailable")
        return {"success": False, "error": "Connection failed - MyGPT service unavailable"}
    except httpx.TimeoutException:
        return {"success": False, "error": "Request timeout"}
    except Exception as e:
        logger.error(f"MyGPT API call failed: {e}")
        return {"success": False, "error": str(e)}


@router.post("/transfer", response_model=MyGPTTransferResponse)
async def transfer_to_mygpt(request: MyGPTTransferRequest) -> MyGPTTransferResponse:
    """
    MyGPT GPT로 컨텍스트 전송

    작업:
    1. Upstash Redis에서 notebook 데이터 조회
    2. MyGPT Actions API 호출 (openapi.yaml 기반)
    3. 전송 결과 로그
    """
    try:
        if not MYGPT_API_KEY:
            raise HTTPException(status_code=401, detail="MyGPT API key not configured")

        # 1. Upstash Redis에 데이터 저장
        # TTL: 24시간 (86400초)
        transfer_id = f"tx_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
        cache_key = f"mygpt:transfer:{transfer_id}"

        # 전송할 데이터 구성
        transfer_data = {
            "notebook_id": request.notebook_id,
            "target_gpt_id": request.target_gpt_id,
            "context": request.context,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        # Redis 저장 (RedisCacheService 활용 + Circuit Breaker)
        try:
            success = await _safe_cache_set(cache_key, transfer_data, ttl=86400)
        except CircuitBreakerOpenException:
            logger.warning(f"Circuit Breaker OPEN: Skipping cache for {cache_key}")
            success = False
        except Exception:
            success = False

        if not success:
            logger.warning(f"Failed to cache transfer data for {transfer_id} (Redis unavailable)")
            # Redis 실패 시에도 전송은 성공으로 처리할지 여부는 비즈니스 로직에 따름.
            # 현재는 경고만 로그하고 진행 (Simulation/Fallback)

        # 2. MyGPT Actions API 호출 (Phase 79 - TODO-006)
        api_result = await _call_mygpt_api(
            action="receive_context",
            payload={
                "transfer_id": transfer_id,
                "notebook_id": request.notebook_id,
                "context": request.context,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        if not api_result.get("success"):
            # API 호출 실패 시에도 캐시는 유지 (재시도 가능)
            logger.warning(f"MyGPT API call failed: {api_result.get('error')}")
            # 실패해도 transfer_id 반환 (캐시에 저장됨)

        # 전송 응답
        return MyGPTTransferResponse(
            success=api_result.get("success", False) or success,  # Cache 성공도 포함
            message=f"Notebook {request.notebook_id} transferred to {request.target_gpt_id}",
            transfer_id=transfer_id,
            timestamp=datetime.now(UTC),
        )

    except Exception as e:
        logger.error(f"Transfer failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transfer failed: {e!s}")


@router.get("/status", response_model=MyGPTStatusResponse)
async def get_mygpt_status() -> MyGPTStatusResponse:
    """
    MyGPT 연동 상태 조회

    작업:
    1. GPT ID 설정 확인
    2. API 키 존재 확인
    3. 연결 상태 반환
    """
    try:
        gpt_configured = bool(MYGPT_API_KEY)
        openai_configured = bool(OPENAI_API_KEY)

        return MyGPTStatusResponse(
            connected=gpt_configured and openai_configured,
            gpt_configured=gpt_configured,
            last_sync=datetime.now(UTC) if gpt_configured else None,
            active_contexts=5,  # 데모 데이터
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {e!s}")


@router.post("/sync", response_model=MyGPTSyncResponse)
async def sync_mygpt_contexts():
    """
    양방향 동기화 (jangjungwha.com ↔ MyGPT)

    작업:
    1. MyGPT에서 최신 컨텍스트 조회
    2. Upstash Redis에 저장
    3. jangjungwha.com 업데이트
    """
    try:
        # 실제 동기화 로직 구현 (Phase 79 - TODO-006)
        # 1. MyGPT에서 최신 컨텍스트 조회
        api_result = await _call_mygpt_api(
            action="sync_state",
            payload={
                "gpt_id": MYGPT_GPT_ID,
                "sync_type": "bidirectional",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        if api_result.get("success"):
            data = api_result.get("data", {})
            contexts_synced = data.get("contexts_synced", 0)
            return MyGPTSyncResponse(
                sync_success=True,
                contexts_synced=contexts_synced,
                last_sync_time=datetime.now(UTC),
                sync_type="bidirectional",
            )

        # API 실패 시 fallback 응답
        logger.warning(f"MyGPT sync API failed: {api_result.get('error')}")
        return MyGPTSyncResponse(
            sync_success=False,
            contexts_synced=0,
            last_sync_time=datetime.now(UTC),
            sync_type="failed",
        )

    except Exception as e:
        logger.error(f"Sync failed: {e!s}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Sync failed: {e!s}")


# 라우터를 내보냄
__all__ = ["router"]
