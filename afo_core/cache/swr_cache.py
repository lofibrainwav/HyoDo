# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/cache/swr_cache.py
# (Stale-While-Revalidate 구현 - PDF 성능 최적화 기반)
# 🧭 Trinity Score: 眞85% 善95% 美99% 孝100%

import asyncio
import json
import logging
import os
import time
from collections.abc import Callable
from typing import Any

# 환경 변수에서 Redis 설정 로드 (하드코딩 제거)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Assume AFO redis client wrapper or standard redis
try:
    import redis  # type: ignore[import-untyped]

    redis_client: Any | None = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
    )
    logger = logging.getLogger(__name__)
    logger.info(f"[SWR] Redis connected to {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}")
except ImportError:
    redis_client = None
    print("⚠️ Redis not installed, SWR cache falling back to pass-through")
except Exception as e:
    redis_client = None
    print(f"⚠️ Redis connection failed: {e}, SWR cache falling back to pass-through")

logger = logging.getLogger(__name__)


async def background_revalidate(key: str, fetch_func: Callable[[], Any], ttl: int, swr_grace: int):
    """백그라운드 재검증 (SWR 핵심)
    Executes the fetch function and updates the cache.
    """
    try:
        logger.info(f"[SWR] Background revalidating key: {key}")
        data = fetch_func()  # This might be async in real app, keeping simple for pattern
        if asyncio.iscoroutine(data):
            data = await data

        # Update Cache
        if redis_client:
            payload = {"data": data, "timestamp": time.time()}
            redis_client.set(key, json.dumps(payload), ex=ttl + swr_grace)

        logger.info(f"[SWR] Revalidation complete for {key}")
    except Exception as e:
        logger.error(f"[SWR] Background revalidation failed for {key}: {e}")
