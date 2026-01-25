# Trinity Score: 90.0 (Established by Chancellor)
"""
Client Stats Router - Data Driven Model
Phase: Eliminating Hardcoding & Syncing Live Demo

Redis 기반 Client Stats 관리로 하드코딩 제거 및 실시간 업데이트 지원.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import redis
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from AFO.config.settings import get_settings
from AFO.utils.standard_shield import shield

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/client-stats", tags=["Client Stats"])

# Redis Key Constants (SSOT)
REDIS_KEY_PREFIX = "client:stats:"
REDIS_KEY_DEPENDENCY_COUNT = f"{REDIS_KEY_PREFIX}dependency_count"
REDIS_KEY_LANGGRAPH_ACTIVE = f"{REDIS_KEY_PREFIX}langgraph_active"
REDIS_KEY_TOTAL_DEPENDENCIES = f"{REDIS_KEY_PREFIX}total_dependencies"

# Default Values (Fallback when Redis unavailable)
DEFAULT_DEPENDENCY_COUNT = 42
DEFAULT_LANGGRAPH_ACTIVE = True
DEFAULT_TOTAL_DEPENDENCIES = 42


class ClientStatsUpdate(BaseModel):
    """Client Stats 업데이트 요청 모델"""

    dependency_count: int | None = Field(None, ge=0, description="의존성 개수")
    langgraph_active: bool | None = Field(None, description="LangGraph 활성 상태")
    total_dependencies: int | None = Field(None, ge=0, description="전체 의존성 개수")


class ClientStatsResponse(BaseModel):
    """Client Stats 응답 모델"""

    dependency_count: int = Field(..., description="의존성 개수")
    langgraph_active: bool = Field(..., description="LangGraph 활성 상태")
    total_dependencies: int = Field(..., description="전체 의존성 개수")
    source: str = Field(..., description="데이터 소스 (redis/fallback)")
    timestamp: str = Field(..., description="조회 시간")


def _get_redis_client() -> redis.Redis | None:
    """Redis 클라이언트 생성 (Lazy Loading with Timeout)"""
    try:
        settings = get_settings()
        redis_url = settings.get_redis_url()
        client: redis.Redis = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        return client
    except Exception as e:
        logger.warning("Redis connection failed in Client Stats: %s", e)
        return None


def get_client_stats() -> dict[str, Any]:
    """
    Redis에서 Client Stats 조회 (Fallback 포함)

    Returns:
        dict with dependency_count, langgraph_active, total_dependencies, source
    """
    redis_client = _get_redis_client()

    if redis_client:
        try:
            # Redis에서 값 조회
            dependency_count_raw = redis_client.get(REDIS_KEY_DEPENDENCY_COUNT)
            langgraph_active_raw = redis_client.get(REDIS_KEY_LANGGRAPH_ACTIVE)
            total_dependencies_raw = redis_client.get(REDIS_KEY_TOTAL_DEPENDENCIES)

            # 값이 없으면 기본값 설정 후 반환
            if dependency_count_raw is None:
                redis_client.set(REDIS_KEY_DEPENDENCY_COUNT, DEFAULT_DEPENDENCY_COUNT)
                dependency_count = DEFAULT_DEPENDENCY_COUNT
            else:
                dependency_count = int(dependency_count_raw)

            if langgraph_active_raw is None:
                redis_client.set(REDIS_KEY_LANGGRAPH_ACTIVE, "true")
                langgraph_active = DEFAULT_LANGGRAPH_ACTIVE
            else:
                langgraph_active = langgraph_active_raw.lower() == "true"

            if total_dependencies_raw is None:
                redis_client.set(REDIS_KEY_TOTAL_DEPENDENCIES, DEFAULT_TOTAL_DEPENDENCIES)
                total_dependencies = DEFAULT_TOTAL_DEPENDENCIES
            else:
                total_dependencies = int(total_dependencies_raw)

            return {
                "dependency_count": dependency_count,
                "langgraph_active": langgraph_active,
                "total_dependencies": total_dependencies,
                "source": "redis",
            }
        except Exception as e:
            logger.error("Failed to get client stats from Redis: %s", e)

    # Fallback to defaults
    return {
        "dependency_count": DEFAULT_DEPENDENCY_COUNT,
        "langgraph_active": DEFAULT_LANGGRAPH_ACTIVE,
        "total_dependencies": DEFAULT_TOTAL_DEPENDENCIES,
        "source": "fallback",
    }


def update_client_stats(updates: dict[str, Any]) -> bool:
    """
    Redis에 Client Stats 업데이트

    Args:
        updates: 업데이트할 키-값 쌍

    Returns:
        성공 여부
    """
    redis_client = _get_redis_client()

    if not redis_client:
        logger.error("Cannot update client stats: Redis unavailable")
        return False

    try:
        if "dependency_count" in updates and updates["dependency_count"] is not None:
            redis_client.set(REDIS_KEY_DEPENDENCY_COUNT, updates["dependency_count"])

        if "langgraph_active" in updates and updates["langgraph_active"] is not None:
            value = "true" if updates["langgraph_active"] else "false"
            redis_client.set(REDIS_KEY_LANGGRAPH_ACTIVE, value)

        if "total_dependencies" in updates and updates["total_dependencies"] is not None:
            redis_client.set(REDIS_KEY_TOTAL_DEPENDENCIES, updates["total_dependencies"])

        logger.info("Client stats updated: %s", updates)
        return True
    except Exception as e:
        logger.error("Failed to update client stats: %s", e)
        return False


@shield(pillar="美")
@router.get("", response_model=ClientStatsResponse)
async def get_stats() -> ClientStatsResponse:
    """
    현재 Client Stats 조회

    Redis에서 실시간 값을 조회하고, 연결 실패 시 기본값 반환.
    """
    stats = get_client_stats()
    return ClientStatsResponse(
        dependency_count=stats["dependency_count"],
        langgraph_active=stats["langgraph_active"],
        total_dependencies=stats["total_dependencies"],
        source=stats["source"],
        timestamp=datetime.now().isoformat(),
    )


@shield(pillar="美")
@router.put("", response_model=ClientStatsResponse)
async def update_stats(update: ClientStatsUpdate) -> ClientStatsResponse:
    """
    Client Stats 업데이트 (실시간 조정)

    Dashboard에서 실시간으로 값을 조정할 수 있도록 지원.
    """
    updates = update.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")

    success = update_client_stats(updates)

    if not success:
        raise HTTPException(status_code=503, detail="Redis unavailable")

    # 업데이트 후 최신 값 반환
    stats = get_client_stats()
    return ClientStatsResponse(
        dependency_count=stats["dependency_count"],
        langgraph_active=stats["langgraph_active"],
        total_dependencies=stats["total_dependencies"],
        source=stats["source"],
        timestamp=datetime.now().isoformat(),
    )


@shield(pillar="美")
@router.post("/reset")
async def reset_stats() -> dict[str, Any]:
    """
    Client Stats를 기본값으로 리셋
    """
    success = update_client_stats(
        {
            "dependency_count": DEFAULT_DEPENDENCY_COUNT,
            "langgraph_active": DEFAULT_LANGGRAPH_ACTIVE,
            "total_dependencies": DEFAULT_TOTAL_DEPENDENCIES,
        }
    )

    if not success:
        raise HTTPException(status_code=503, detail="Redis unavailable")

    return {
        "message": "Client stats reset to defaults",
        "defaults": {
            "dependency_count": DEFAULT_DEPENDENCY_COUNT,
            "langgraph_active": DEFAULT_LANGGRAPH_ACTIVE,
            "total_dependencies": DEFAULT_TOTAL_DEPENDENCIES,
        },
        "timestamp": datetime.now().isoformat(),
    }
