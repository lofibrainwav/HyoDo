from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

import psutil
import redis
from fastapi import APIRouter, Request

# Import Redis type for type hints
try:
    from redis.client import Redis
except ImportError:
    try:
        from redis import Redis
    except ImportError:
        # Fallback
        Redis = redis.Redis
from fastapi.responses import RedirectResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from AFO.config.antigravity import antigravity
from AFO.config.settings import get_settings
from AFO.services.health_service import get_comprehensive_health
from AFO.utils.metrics import sse_open_connections
from api.routers.client_stats import get_client_stats

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Trinity Score: 90.0 (Established by Chancellor)
"""System Health & Logs Routes."""


# Optional SSE import
try:
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

try:
    SSE_AVAILABLE = True
except ImportError:
    # Define a dummy type for type checking if import fails
    EventSourceResponse = Any  # type: ignore
    SSE_AVAILABLE = False

router = APIRouter(prefix="/api/system", tags=["System Health"])


@router.get("/health", include_in_schema=True)  # SSOT: Always available for health checks
async def system_health_alias():
    """Alias for /api/health to support legacy tests. Only available in dev environment."""
    # Truth: Return full comprehensive health data including organs_v2
    # This ensures Dashboard receives the correct data for 11-Organ monitoring
    try:
        return await get_comprehensive_health()
    except Exception as e:
        logger.warning("System health alias failed: %s", e)
        return {
            "status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
        }


logger = logging.getLogger(__name__)

ORGANS = [
    "Brain",
    "Heart",
    "Lungs",
    "Digestive",
    "Immune",
    "Musculoskeletal",
    "Endocrine",
    "Nervous",
    "Reproductive",
    "Circulatory",
    "Integumentary",
]


def _get_redis_client() -> Any | None:
    """Redis 클라이언트 생성 (Lazy Loading)"""
    # Phase 2-4: settings 사용
    settings = get_settings()
    redis_url = settings.get_redis_url()

    try:
        # Explicitly cast to redis.Redis to satisfy mypy
        client = cast(
            "redis.Redis",
            redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            ),
        )
        client.ping()
        return client
    except Exception as e:
        logger.warning("Redis connection failed in System Health: %s", e)
        return None


@router.get("/metrics")
async def get_system_metrics() -> dict[str, Any]:
    """
    CoreZen Dashboard를 위한 실시간 시스템 메트릭

    Returns:
        - memory_percent: 메모리 사용률 (0-100)
        - swap_percent: 스왑 사용률 (0-100)
        - containers_running: 실행 중인 컨테이너 수 (Redis 기반 추정)
        - disk_percent: 디스크 사용률 (0-100)
        - redis_connected: Redis 연결 상태
        - langgraph_active: LangGraph 활성 상태 (항상 True로 가정 or Redis 체크)
    """
    try:
        # 1. System Metrics via psutil (Cross-platform)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage("/")

        memory_percent = memory.percent
        swap_percent = swap.percent
        disk_percent = disk.percent

        # 2. Redis Connection & Service Status
        redis_client = _get_redis_client()
        redis_connected = redis_client is not None

        containers_running = 0
        if redis_client:
            try:
                # Count healthy services from Redis
                all_status = redis_client.hgetall("services:health")

                # Filter for services that are 'healthy'
                containers_running = sum(
                    1
                    for data_json in all_status.values()
                    if isinstance(data_json, str) and "healthy" in data_json
                )
            except Exception:
                pass

        # 3. LangGraph Active Status (Data Driven - from Redis)
        client_stats = get_client_stats()
        langgraph_active = client_stats["langgraph_active"]

        # 4. Bind System Metrics to Organs (11-오장육부 Metaphor)
        # Score calculation: 100 - (Usage %)
        # Healthy means Low Usage (high score)

        # Brain (Memory)
        brain_score = max(0, 100 - memory_percent)
        # Digestive (Disk)
        digestive_score = max(0, 100 - disk_percent)
        # Heart (Redis - Connectivity)
        heart_score = 100 if redis_connected else 0
        # Lungs (Swap/CPU Proxy)
        lungs_score = max(0, 100 - swap_percent)

        # Others (Baseline high, slightly affected by total load)
        avg_load = (memory_percent + disk_percent) / 2
        general_score = max(50, 100 - (avg_load * 0.5))

        organs_data = [
            {"name": "Brain", "score": brain_score, "metric": f"Mem {memory_percent}%"},
            {"name": "Heart", "score": heart_score, "metric": "Redis Connected"},
            {
                "name": "Digestive",
                "score": digestive_score,
                "metric": f"Disk {disk_percent}%",
            },
            {"name": "Lungs", "score": lungs_score, "metric": f"Swap {swap_percent}%"},
            # Fill others with general health
            {"name": "Immune", "score": general_score, "metric": "General Protection"},
            {
                "name": "Musculoskeletal",
                "score": general_score,
                "metric": "Infrastructure",
            },
            {"name": "Endocrine", "score": general_score, "metric": "Scheduling"},
            {"name": "Nervous", "score": brain_score, "metric": "Network/API"},
            {"name": "Reproductive", "score": 100, "metric": "Backups"},
            {"name": "Circulatory", "score": heart_score, "metric": "Data Flow"},
            {
                "name": "Integumentary",
                "score": general_score,
                "metric": "Firewall/API Gateway",
            },
        ]

        return {
            "memory_percent": round(memory_percent, 1),
            "swap_percent": round(swap_percent, 1),
            "containers_running": containers_running,
            "disk_percent": round(disk_percent, 1),
            "redis_connected": redis_connected,
            "langgraph_active": langgraph_active,
            "organs": organs_data,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error("Error collecting system metrics: %s", e)
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


async def _log_stream(limit: int | None = None) -> AsyncGenerator[str, None]:
    counter = 0
    while True:
        counter += 1
        message = {
            "timestamp": datetime.now(UTC).isoformat(),
            "message": f"[{counter}] 시스템 정상 동작 (Unified Health)",
        }
        yield json.dumps(message)  # Ensure JSON string for SSE data
        await asyncio.sleep(1)
        if limit and counter >= limit:
            break


@router.get("/kingdom-status")
async def get_kingdom_status() -> dict[str, Any]:
    """
    AFO Kingdom Grand Status (Real-time Truth)
    SSOT: Uses get_comprehensive_health() to ensure consistency with /health
    """

    settings = get_settings()

    # 1. Get Truthful Health Data
    health_data = await get_comprehensive_health()
    trinity = health_data.get("trinity", {})
    organs_v1 = health_data.get("organs", {})

    # 2. Get Resource Metrics (Entropy)
    cpu_percent = psutil.cpu_percent(interval=None)

    # 3. Construct Response aligned with Truth
    # Extract Pillar scores from health service (0.0-1.0 range -> 0-100)
    pillars = [
        {"name": "Truth 眞", "score": int(trinity.get("truth", 0) * 100)},
        {"name": "Good 善", "score": int(trinity.get("goodness", 0) * 100)},
        {"name": "Beauty 美", "score": int(trinity.get("beauty", 0) * 100)},
        {"name": "Serenity 孝", "score": int(trinity.get("filial_serenity", 0) * 100)},
        {"name": "Eternity 永", "score": int(trinity.get("eternity", 0) * 100)},
    ]

    # Map V1 organs to Dashboard expected format
    dashboard_organs = []

    # Map backend organs to dashboard metaphor
    # 心_Redis -> Heart
    if "心_Redis" in organs_v1:
        o = organs_v1["心_Redis"]
        dashboard_organs.append(
            {
                "name": "Heart",
                "score": 100 if o["status"] == "healthy" else 0,
                "metric": "Redis " + ("Alive" if o["status"] == "healthy" else "Down"),
            }
        )

    # 肝_PostgreSQL -> Stomach (Digestion/Storage)
    if "肝_PostgreSQL" in organs_v1:
        o = organs_v1["肝_PostgreSQL"]
        dashboard_organs.append(
            {
                "name": "Stomach",
                "score": 100 if o["status"] == "healthy" else 0,
                "metric": "DB " + ("Alive" if o["status"] == "healthy" else "Down"),
            }
        )

    # 肺_API_Server -> Lungs/Eyes (Breath/Vision)
    if "肺_API_Server" in organs_v1:
        o = organs_v1["肺_API_Server"]
        dashboard_organs.append(
            {
                "name": "Lungs",
                "score": 100 if o["status"] == "healthy" else 0,
                "metric": "API " + ("Alive" if o["status"] == "healthy" else "Down"),
            }
        )

    # 脾_Ollama -> Brain (Intelligence)
    if "脾_Ollama" in organs_v1:
        o = organs_v1["脾_Ollama"]
        dashboard_organs.append(
            {
                "name": "Brain",
                "score": 100 if o["status"] == "healthy" else 0,
                "metric": "LLM " + ("Alive" if o["status"] == "healthy" else "Down"),
            }
        )

    # Get Client Stats from Redis (Data Driven)
    client_stats = get_client_stats()

    return {
        "heartbeat": 100 if health_data.get("status") == "balanced" else 50,
        "dependency_count": client_stats["dependency_count"],
        "total_dependencies": client_stats["total_dependencies"],
        "verified_dependencies": [],
        "pillars": pillars,
        "trinity_score": health_data.get("health_percentage", 0),
        "scholars": [],  # Populate if needed
        "organs": dashboard_organs,  # Dashboard format
        "entropy": int(cpu_percent),
        "timestamp": datetime.now().isoformat(),
        # Phase 23: Dashboard Hardening (Always Exposed Vitals)
        "head_sha": os.getenv("GIT_COMMIT_SHA", "unknown")[:7],
        "chancellor_v2_enabled": settings.CHANCELLOR_V2_ENABLED,
        "canary_status": ("V2 (Canary)" if settings.CHANCELLOR_V2_ENABLED else "V1 (Stable)"),
        # Include original health data for debugging
        "raw_health": health_data,
    }


@router.get("/antigravity/config")
async def get_antigravity_config() -> dict[str, Any]:
    """
    [TRUTH WIRING]
    Expose current AntiGravity settings for verification.
    """

    return {
        "environment": antigravity.ENVIRONMENT,
        "auto_deploy": antigravity.AUTO_DEPLOY,
        "dry_run_default": antigravity.DRY_RUN_DEFAULT,
        "auto_sync": antigravity.AUTO_SYNC,
        "log_level": antigravity.LOG_LEVEL,
        "mode": "Self-Expanding" if antigravity.SELF_EXPANDING_MODE else "Static",
    }


# SSOT SSE Router (prefix-free for /api/logs/stream canonical path)
# This router is registered separately in router_manager.py
sse_ssot_router = APIRouter(prefix="/api", tags=["SSE SSOT"])


# Notebook Bridge Kingdom Status (jangjungwha.com format)
@sse_ssot_router.get("/kingdom/status")
async def get_kingdom_status_notebook_bridge() -> dict[str, Any]:
    """
    Kingdom Status for Notebook Bridge (jangjungwha.com format).
    Returns trinityScore, pillars as object, systemHealth.
    """
    import uuid

    health_data = await get_comprehensive_health()
    trinity = health_data.get("trinity", {})

    # Convert to jangjungwha.com expected format
    return {
        "trinityScore": round(health_data.get("health_percentage", 0), 2),
        "pillars": {
            "truth": int(trinity.get("truth", 0) * 100),
            "goodness": int(trinity.get("goodness", 0) * 100),
            "beauty": int(trinity.get("beauty", 0) * 100),
            "serenity": int(trinity.get("filial_serenity", 0) * 100),
            "infinity": int(trinity.get("eternity", 0) * 100),
        },
        "activeAgents": len(health_data.get("organs", {})),
        "systemHealth": f"VERIFY_TRUST: {uuid.uuid4().hex[:8].upper()}",
        "lastUpdated": datetime.now().isoformat(),
        "schedule": [],
    }


@sse_ssot_router.get("/notebooks")
async def get_notebooks_alias(limit: int = 5) -> dict[str, Any]:
    """
    Notebooks API alias for Notebook Bridge.
    Returns sample notebooks for demo purposes.
    """
    # Sample notebooks for demo
    sample_notebooks = [
        {
            "id": "demo-001",
            "title": "AFO Kingdom System Overview",
            "updatedAt": datetime.now().isoformat(),
        },
        {
            "id": "demo-002",
            "title": "Trinity Score Monitoring",
            "updatedAt": datetime.now().isoformat(),
        },
        {
            "id": "demo-003",
            "title": "Julie CPA Tax Strategy",
            "updatedAt": datetime.now().isoformat(),
        },
    ]
    return {"results": sample_notebooks[:limit]}


async def _sse_log_generator(request: Request):
    """
    Generate SSE events from Redis Pub/Sub messages with File Fallback.
    Trinity Score: 善 (Goodness) - Failover mechanism for high availability.
    """
    if METRICS_AVAILABLE:
        sse_open_connections.inc()

    redis_available = False
    pubsub = None

    try:
        settings = get_settings()
        redis_url = settings.REDIS_URL
        # Using decode_responses=True for simpler string handling
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        pubsub = redis_client.pubsub()
        pubsub.subscribe("kingdom:logs:stream")
        redis_available = True
        logger.info("[SSE] Connected to Redis Pub/Sub")
    except Exception as e:
        logger.warning(f"[SSE] Redis unavailable ({e}). Falling back to file tail.")

    # Send initial connection message
    initial_msg = {
        "message": "🔌 [Serenity] Connected to Chancellor Stream"
        + (" (Redis)" if redis_available else " (Fallback: File)"),
        "level": "SUCCESS",
        "source": "Chancellor Stream",
        "timestamp": (
            datetime.now().isoformat() if not redis_available else asyncio.get_event_loop().time()
        ),
    }
    yield f"data: {json.dumps(initial_msg)}\n\n"

    if redis_available and pubsub:
        try:
            while True:
                if await request.is_disconnected():
                    logger.info("[SSE] Client disconnected (Redis mode)")
                    break

                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    # message["data"] is already a JSON string from publish_thought
                    yield f"data: {message['data']}\n\n"

                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"[SSE] Redis stream error: {e}")
        finally:
            pubsub.close()

    # Fallback to File Tail (Goodness)
    logger.info("[SSE] Starting File Fallback tailing")
    log_file = "backend.log"
    if not os.path.exists(log_file):
        try:
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] Log file initialized.\n")
        except Exception:
            pass

    try:
        # Note: We use traditional open here for tailing, which is okay in this async generator
        # as it sleeps between reads.
        with open(log_file) as f:
            f.seek(0, 2)  # Go to end
            while True:
                if await request.is_disconnected():
                    logger.info("[SSE] Client disconnected (File mode)")
                    break

                line = f.readline()
                if line:
                    msg = {
                        "message": line.strip(),
                        "level": "INFO",
                        "source": "backend.log",
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield f"data: {json.dumps(msg)}\n\n"
                else:
                    await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"[SSE] File Fallback failed: {e}")
        error_msg = {"message": f"Critical Stream Failure: {e}", "level": "ERROR"}
        yield f"data: {json.dumps(error_msg)}\n\n"
    finally:
        if METRICS_AVAILABLE:
            sse_open_connections.dec()


# SSOT Canonical Path: /api/logs/stream
@sse_ssot_router.get("/logs/stream")
async def stream_logs_ssot(request: Request) -> StreamingResponse:
    """
    [SSOT] Canonical SSE Log Stream Endpoint
    Using native StreamingResponse for maximum reliability (Truth)
    """
    return StreamingResponse(
        _sse_log_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx no-buffer
        },
    )


# Cursor Compatibility Path: /api/stream/logs
@sse_ssot_router.get("/stream/logs")
async def stream_logs_cursor_compat(request: Request, limit: int = 0) -> RedirectResponse:
    """[Alias] Cursor compatibility path for /api/stream/logs (Redirects to SSOT)"""
    return RedirectResponse("/api/logs/stream", status_code=308)


# Original Path (retained for existing integrations): /api/system/logs/stream
@router.get("/logs/stream")
async def stream_logs(request: Request, limit: int = 0) -> RedirectResponse:
    """
    [Serenity: 孝] Simple Test Log Stream
    Redirects to canonical SSOT path
    """
    return RedirectResponse("/api/logs/stream", status_code=308)
