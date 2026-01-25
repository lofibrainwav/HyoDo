# Trinity Score: 90.0 (Established by Chancellor)
"""
Multi-Level Cache Manager

Orchestrates L1 (Memory) and L2 (Redis) caching strategies.
Implements the "Truth" of data retrieval speed vs. consistency.
"""

import logging
import time
from typing import Any

from AFO.backends import MemoryBackend, RedisBackend

logger = logging.getLogger(__name__)


class CacheMetrics:
    """Phase 6B: Cache Performance Metrics Collector"""

    def __init__(self) -> None:
        self.metrics = {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "l1_hits": 0,
            "l2_hits": 0,
            "predictive_hits": 0,
            "hit_rate": 0.0,
            "avg_response_time_ms": 0.0,
            "total_response_time_ms": 0.0,
        }
        self._start_time = time.time()

    def record_request(self, hit: bool, level: str = "miss", response_time_ms: float = 0.0) -> None:
        """Record cache request metrics"""
        self.metrics["total_requests"] += 1
        self.metrics["total_response_time_ms"] += response_time_ms

        if hit:
            self.metrics["cache_hits"] += 1
            if level == "l1":
                self.metrics["l1_hits"] += 1
            elif level == "l2":
                self.metrics["l2_hits"] += 1
            elif level == "predictive":
                self.metrics["predictive_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        # Update hit rate
        total = self.metrics["total_requests"]
        if total > 0:
            self.metrics["hit_rate"] = self.metrics["cache_hits"] / total
            self.metrics["avg_response_time_ms"] = self.metrics["total_response_time_ms"] / total

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics with uptime"""
        metrics = self.metrics.copy()
        metrics["uptime_seconds"] = time.time() - self._start_time
        return metrics

    def reset(self) -> None:
        """Reset metrics (for testing)"""
        self.metrics = {k: 0.0 if isinstance(v, float) else 0 for k, v in self.metrics.items()}
        self._start_time = time.time()


class MultiLevelCache:
    """
    Tiered Cache System.

    Flow:
    1. Check L1 (Memory). Hit -> Return.
    2. Check L2 (Redis). Hit -> Populate L1 -> Return.
    3. Miss -> Return None (Caller fetches from DB/LLM) -> Caller calls set().
    """

    def __init__(self) -> None:
        self.l1 = MemoryBackend(max_size=5000)  # Fast, local
        self.l2 = RedisBackend()  # Shared, persistent
        self.metrics = CacheMetrics()  # Phase 6B: Performance tracking

    async def get(self, key: str) -> Any | None:
        """Get value with automated L1 promotion"""
        import time

        start_time = time.time()

        try:
            # 1. L1 Check
            val = await self.l1.get(key)
            if val is not None:
                # Phase 6B: Record L1 hit metrics
                response_time = (time.time() - start_time) * 1000
                self.metrics.record_request(hit=True, level="l1", response_time_ms=response_time)
                return val

            # 2. L2 Check
            val = await self.l2.get(key)
            if val is not None:
                # Phase 6B: Record L2 hit metrics
                response_time = (time.time() - start_time) * 1000
                self.metrics.record_request(hit=True, level="l2", response_time_ms=response_time)
                # Promote to L1 for next time
                await self.l1.set(key, val, ttl=60)  # Short TTL for L1
                return val

            # Phase 6B: Record miss metrics
            response_time = (time.time() - start_time) * 1000
            self.metrics.record_request(hit=False, response_time_ms=response_time)
            return None
        except Exception as e:
            # Phase 6B: Record error as miss
            response_time = (time.time() - start_time) * 1000
            self.metrics.record_request(hit=False, response_time_ms=response_time)
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int | None = 300) -> None:
        """Set value in all layers"""
        # Set L1 (Short TTL if specified, or default short)
        l1_ttl = min(ttl, 60) if ttl else 60
        await self.l1.set(key, value, ttl=l1_ttl)

        # Set L2
        await self.l2.set(key, value, ttl=ttl)

    async def delete(self, key: str) -> None:
        """Delete from all layers"""
        await self.l1.delete(key)
        await self.l2.delete(key)

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics"""
        return self.metrics.get_metrics()


# Singleton Instance
cache_manager = MultiLevelCache()
