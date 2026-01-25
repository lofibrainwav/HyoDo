# Trinity Score: 90.0 (Established by Chancellor)
"""Edge Revalidation API Routes

眞 (Truth): Type-safe ISR revalidation
善 (Goodness): Rate-limited with proper error handling
美 (Beauty): Clean API design following REST conventions
孝 (Serenity): Non-blocking async operations
永 (Eternity): Audit trail for all revalidation requests

Author: AFO Kingdom Development Team
Date: 2025-12-24
"""

import asyncio
import logging
import os
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, BackgroundTasks, Header
from pydantic import BaseModel, Field

from AFO.utils.redis_connection import get_shared_async_redis_client

logger = logging.getLogger(__name__)

# Redis keys for tracking (Phase 79 - P79-001)
REDIS_KEY_LAST_SUCCESS = "afo:edge:revalidate:last_success"
REDIS_KEY_REQUESTS_TODAY = "afo:edge:revalidate:requests_today"
REDIS_KEY_REQUESTS_DATE = "afo:edge:revalidate:requests_date"

router = APIRouter(prefix="/edge", tags=["Edge Revalidation"])


# ============================================================================
# MODELS
# ============================================================================


class RevalidateRequest(BaseModel):
    """Request to trigger ISR revalidation"""

    fragment_key: str = Field(..., description="Fragment key to revalidate")
    path: str | None = Field(None, description="Optional path to revalidate")


class RevalidateResponse(BaseModel):
    """Response from revalidation request"""

    success: bool
    fragment_key: str
    revalidated_at: datetime
    vercel_status: int | None = None
    message: str


class RevalidateStatusResponse(BaseModel):
    """Current revalidation system status"""

    configured: bool
    revalidate_url: str | None = None
    last_success: datetime | None = None
    total_requests_today: int = 0


# ============================================================================
# REDIS TRACKING FUNCTIONS (Phase 79 - P79-001)
# ============================================================================


async def _record_revalidate_request(success: bool) -> None:
    """Record a revalidation request in Redis for tracking"""
    try:
        redis = await get_shared_async_redis_client()
        today = datetime.now(UTC).strftime("%Y-%m-%d")

        # Check if date changed, reset counter if so
        stored_date = await redis.get(REDIS_KEY_REQUESTS_DATE)
        if stored_date is None or stored_date.decode() != today:
            await redis.set(REDIS_KEY_REQUESTS_DATE, today)
            await redis.set(REDIS_KEY_REQUESTS_TODAY, 0)

        # Increment request counter
        await redis.incr(REDIS_KEY_REQUESTS_TODAY)

        # Record last success timestamp if successful
        if success:
            await redis.set(REDIS_KEY_LAST_SUCCESS, datetime.now(UTC).isoformat())

    except Exception as e:
        logger.warning(f"Failed to record revalidate request in Redis: {e}")


async def _get_tracking_stats() -> tuple[datetime | None, int]:
    """Get tracking statistics from Redis"""
    try:
        redis = await get_shared_async_redis_client()
        today = datetime.now(UTC).strftime("%Y-%m-%d")

        # Get last success timestamp
        last_success_str = await redis.get(REDIS_KEY_LAST_SUCCESS)
        last_success = None
        if last_success_str:
            last_success = datetime.fromisoformat(last_success_str.decode())

        # Get today's request count (reset if date changed)
        stored_date = await redis.get(REDIS_KEY_REQUESTS_DATE)
        if stored_date is None or stored_date.decode() != today:
            total_requests = 0
        else:
            count = await redis.get(REDIS_KEY_REQUESTS_TODAY)
            total_requests = int(count) if count else 0

        return last_success, total_requests

    except Exception as e:
        logger.warning(f"Failed to get tracking stats from Redis: {e}")
        return None, 0


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def trigger_vercel_revalidate(
    fragment_key: str, path: str | None = None
) -> tuple[bool, int, str]:
    """Trigger Vercel ISR revalidation via webhook

    Returns: (success, status_code, message)
    """
    revalidate_url = os.getenv("REVALIDATE_URL")
    revalidate_secret = os.getenv("REVALIDATE_SECRET")

    if not revalidate_url or not revalidate_secret:
        return False, 0, "REVALIDATE_URL or REVALIDATE_SECRET not configured"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{revalidate_url.rstrip('/')}/api/revalidate",
                headers={
                    "x-revalidate-secret": revalidate_secret,
                    "content-type": "application/json",
                },
                json={
                    "fragmentKey": fragment_key,
                    "path": path,
                },
            )

            if response.status_code == 200:
                return True, response.status_code, "Revalidation triggered successfully"
            else:
                return (
                    False,
                    response.status_code,
                    f"Vercel returned {response.status_code}",
                )

    except httpx.TimeoutException:
        return False, 0, "Request timed out"
    except Exception as e:
        logger.error(f"Revalidation failed: {e}")
        return False, 0, str(e)


# ============================================================================
# ENDPOINTS
# ============================================================================


@router.post("/revalidate", response_model=RevalidateResponse)
async def trigger_revalidation(
    request: RevalidateRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str | None = Header(None),
):
    """Trigger ISR revalidation for a specific fragment

    제갈량의 전략: 필요한 것만 갱신하여 효율 극대화
    """
    logger.info(f"Revalidation requested for fragment: {request.fragment_key}")

    success, status_code, message = await trigger_vercel_revalidate(
        request.fragment_key,
        request.path,
    )

    # Record request in Redis for tracking (Phase 79 - P79-001)
    await _record_revalidate_request(success)

    return RevalidateResponse(
        success=success,
        fragment_key=request.fragment_key,
        revalidated_at=datetime.now(UTC),
        vercel_status=status_code if status_code else None,
        message=message,
    )


@router.get("/revalidate/status", response_model=RevalidateStatusResponse)
async def get_revalidation_status():
    """Check revalidation system configuration status"""
    revalidate_url = os.getenv("REVALIDATE_URL")
    revalidate_secret = os.getenv("REVALIDATE_SECRET")

    configured = bool(revalidate_url and revalidate_secret)

    # Get tracking stats from Redis (Phase 79 - P79-001)
    last_success, total_requests = await _get_tracking_stats()

    return RevalidateStatusResponse(
        configured=configured,
        revalidate_url=revalidate_url if configured else None,
        last_success=last_success,
        total_requests_today=total_requests,
    )


@router.post("/revalidate/batch")
async def batch_revalidate(
    fragment_keys: list[str],
    background_tasks: BackgroundTasks,
):
    """Batch revalidation for multiple fragments

    사마의의 안정성: 순차 처리로 rate limit 회피
    """
    results = []

    for key in fragment_keys:
        success, status_code, message = await trigger_vercel_revalidate(key)
        results.append(
            {
                "fragment_key": key,
                "success": success,
                "status": status_code,
                "message": message,
            }
        )
        # Rate limit protection: 100ms delay between requests
        await asyncio.sleep(0.1)

    return {
        "total": len(fragment_keys),
        "successful": sum(1 for r in results if r["success"]),
        "results": results,
    }
