# Trinity Score: 90.0 (Established by Chancellor)
"""
Cache Backends for AFO Kingdom
"""

import json
import logging
import time
from typing import TYPE_CHECKING, Any

from AFO.config.settings import get_settings

if TYPE_CHECKING:
    from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger(__name__)
settings = get_settings()


class MemoryBackend:
    def __init__(self, max_size: int = 1000) -> None:
        self._cache: dict[str, tuple[Any, float]] = {}
        self._max_size = max_size

    def get(self, key: str) -> Any | None:
        if key not in self._cache:
            return None
        val, expiry = self._cache[key]
        if expiry < time.time():
            del self._cache[key]
            return None
        return val

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        if len(self._cache) >= self._max_size:
            try:
                first_key = next(iter(self._cache))
                del self._cache[first_key]
            except StopIteration:
                pass
        self._cache[key] = (value, time.time() + ttl)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()


class RedisBackend:
    def __init__(self, redis_url: str | None = None) -> None:
        self.redis: AsyncRedis | None = None
        self._url = redis_url or settings.get_redis_url()
        self._connected = False

    async def _ensure_connection(self) -> None:
        if not self._connected:
            try:
                import redis.asyncio as aioredis

                self.redis = aioredis.from_url(self._url, encoding="utf-8", decode_responses=True)
                await self.redis.ping()
                self._connected = True
                logger.debug(f"✅ L2 Cache Connected: {self._url}")
            except Exception as e:
                logger.error(f"❌ L2 Cache Connection Failed: {e}")
                self.redis = None
                self._connected = False

    async def ping(self) -> bool:
        await self._ensure_connection()
        if self.redis is not None:
            try:
                res = await self.redis.ping()
                return bool(res)
            except Exception:
                return False
        return False

    async def get(self, key: str) -> Any | None:
        await self._ensure_connection()
        if self.redis is None:
            return None
        try:
            val = await self.redis.get(key)
            if val:
                try:
                    return json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    return val
            return None
        except Exception as e:
            logger.debug(f"L2 Cache Get Error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        await self._ensure_connection()
        if self.redis is None:
            return
        try:
            val = json.dumps(value) if not isinstance(value, (str, bytes, int, float)) else value
            await self.redis.setex(key, ttl, val)
        except Exception as e:
            logger.debug(f"L2 Cache Set Error: {e}")

    async def delete(self, key: str) -> None:
        await self._ensure_connection()
        if self.redis is not None:
            await self.redis.delete(key)

    async def clear(self) -> None:
        await self._ensure_connection()
        if self.redis is not None:
            await self.redis.flushdb()
