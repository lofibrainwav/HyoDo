from __future__ import annotations

import hashlib
import os
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import asyncio


class RouterCache:
    """Request Caching & Deduplication Manager"""

    def __init__(self) -> None:
        # OPTIMIZATION Phase 3: Request deduplication + caching
        self._inflight_requests: dict[str, Any] = {}
        self._response_cache: dict[str, tuple[dict[str, Any], float]] = {}
        self._cache_ttl = float(os.getenv("AFO_SCHOLAR_CACHE_TTL", "1800"))  # 30 min default
        self._cache_max_size = int(os.getenv("AFO_SCHOLAR_CACHE_SIZE", "200"))
        self._cache_stats = {"hits": 0, "misses": 0, "dedup": 0}

    def get_cache_key(self, scholar_key: str, query: str, context: dict[str, Any] | None) -> str:
        """Generate cache key for scholar call."""
        ctx_str = str(sorted((context or {}).items()))
        combined = f"{scholar_key}:{query}:{ctx_str}"
        return hashlib.sha256(combined.encode()).hexdigest()[:24]

    def get(self, key: str) -> dict[str, Any] | None:
        """Get cached response if not expired."""
        if key not in self._response_cache:
            return None
        cached, timestamp = self._response_cache[key]
        if time.time() - timestamp > self._cache_ttl:
            del self._response_cache[key]
            return None
        self._cache_stats["hits"] += 1
        return cached

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Store response in cache."""
        # Evict oldest entries if at capacity
        while len(self._response_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._response_cache))
            del self._response_cache[oldest_key]
        self._response_cache[key] = (value, time.time())
        self._cache_stats["misses"] += 1

    @property
    def inflight_requests(self) -> dict[str, asyncio.Future[dict[str, Any]]]:
        return self._inflight_requests

    def record_dedup(self) -> None:
        self._cache_stats["dedup"] += 1

    def get_stats(self) -> dict[str, int]:
        return self._cache_stats
