# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/cache/swr_cache.py
# (Stale-While-Revalidate 구현 - PDF 성능 최적화 기반)
# 🧭 Trinity Score: 眞85% 善95% 美99% 孝100%

import asyncio
import json
import logging
import time
from collections.abc import Callable
from typing import Any

# Assume AFO redis client wrapper or standard redis
try:
    import redis  # type: ignore[import-untyped]

    redis_client: Any | None = redis.Redis(host="localhost", port=6379, decode_responses=True)
except ImportError:
    redis_client = None
    print("⚠️ Redis not installed, SWR cache falling back to pass-through")

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
