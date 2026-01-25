# Trinity Score: 92.0 (Phase 82 - Cache Intelligence API)
"""
Cache Metrics API Router - Phase 82

Provides endpoints for monitoring cache performance,
semantic cache hits, invalidation events, and adaptive TTL.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheMetricsResponse(BaseModel):
    """Response model for cache metrics."""

    total_queries: int = Field(default=0, description="Total cache queries")
    hit_rate: float = Field(default=0.0, description="Overall cache hit rate (%)")
    semantic_hit_rate: float = Field(default=0.0, description="Semantic cache hit rate (%)")
    exact_hits: int = Field(default=0, description="Exact match cache hits")
    semantic_hits: int = Field(default=0, description="Semantic similarity cache hits")
    misses: int = Field(default=0, description="Cache misses")
    invalidations: int = Field(default=0, description="Total cache invalidations")
    cache_size: int = Field(default=0, description="Current cache size")
    avg_similarity: float = Field(default=0.0, description="Average similarity score")


class TTLStatsResponse(BaseModel):
    """Response model for adaptive TTL statistics."""

    decisions_made: int = Field(default=0, description="Total TTL decisions")
    avg_multiplier: float = Field(default=1.0, description="Average TTL multiplier")
    min_multiplier: float = Field(default=1.0, description="Minimum TTL multiplier")
    max_multiplier: float = Field(default=1.0, description="Maximum TTL multiplier")
    current_trinity_score: float = Field(default=100.0, description="Current Trinity Score")
    current_entropy: float = Field(default=0.0, description="Current system entropy")
    state_distribution: dict[str, int] = Field(
        default_factory=dict, description="Distribution of system states"
    )


class InvalidationStatsResponse(BaseModel):
    """Response model for invalidation engine statistics."""

    total_events: int = Field(default=0, description="Total invalidation events")
    total_invalidations: int = Field(default=0, description="Total entries invalidated")
    cascade_invalidations: int = Field(default=0, description="Cascade invalidations")
    irs_invalidations: int = Field(default=0, description="IRS-triggered invalidations")
    errors: int = Field(default=0, description="Invalidation errors")
    queue_size: int = Field(default=0, description="Current queue size")
    running: bool = Field(default=False, description="Engine running status")


class UnifiedCacheResponse(BaseModel):
    """Unified cache metrics response."""

    semantic: CacheMetricsResponse
    adaptive_ttl: TTLStatsResponse
    invalidation: InvalidationStatsResponse
    timestamp: str


@router.get("/metrics", response_model=UnifiedCacheResponse)
async def get_cache_metrics() -> UnifiedCacheResponse:
    """
    Get unified cache metrics including semantic cache,
    adaptive TTL, and invalidation engine statistics.
    """
    from datetime import datetime

    try:
        from AFO.cache import get_cache_metrics as _get_metrics

        metrics = _get_metrics()

        # Build semantic cache metrics
        semantic_data = metrics.get("semantic", {})
        semantic = CacheMetricsResponse(
            total_queries=semantic_data.get("total_queries", 0),
            hit_rate=semantic_data.get("hit_rate", 0.0),
            semantic_hit_rate=semantic_data.get("semantic_hit_rate", 0.0),
            exact_hits=semantic_data.get("exact_hits", 0),
            semantic_hits=semantic_data.get("semantic_hits", 0),
            misses=semantic_data.get("misses", 0),
            invalidations=semantic_data.get("invalidations", 0),
            cache_size=semantic_data.get("cache_size", 0),
            avg_similarity=semantic_data.get("avg_similarity", 0.0),
        )

        # Build adaptive TTL stats
        ttl_data = metrics.get("adaptive_ttl", {})
        adaptive_ttl = TTLStatsResponse(
            decisions_made=ttl_data.get("decisions_made", 0),
            avg_multiplier=ttl_data.get("avg_multiplier", 1.0),
            min_multiplier=ttl_data.get("min_multiplier", 1.0),
            max_multiplier=ttl_data.get("max_multiplier", 1.0),
            current_trinity_score=ttl_data.get("current_trinity_score", 100.0),
            current_entropy=ttl_data.get("current_entropy", 0.0),
            state_distribution=ttl_data.get("state_distribution", {}),
        )

        # Build invalidation stats
        inv_data = metrics.get("invalidation", {})
        invalidation = InvalidationStatsResponse(
            total_events=inv_data.get("total_events", 0),
            total_invalidations=inv_data.get("total_invalidations", 0),
            cascade_invalidations=inv_data.get("cascade_invalidations", 0),
            irs_invalidations=inv_data.get("irs_invalidations", 0),
            errors=inv_data.get("errors", 0),
            queue_size=inv_data.get("queue_size", 0),
            running=inv_data.get("running", False),
        )

        return UnifiedCacheResponse(
            semantic=semantic,
            adaptive_ttl=adaptive_ttl,
            invalidation=invalidation,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error(f"Failed to get cache metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semantic/history")
async def get_semantic_cache_history(limit: int = 10) -> dict[str, Any]:
    """Get recent semantic cache activity."""
    try:
        from AFO.cache.semantic_cache import get_semantic_cache

        cache = get_semantic_cache()
        return {
            "metrics": cache.get_metrics(),
            "limit": limit,
        }
    except Exception as e:
        logger.error(f"Failed to get semantic cache history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ttl/history")
async def get_ttl_history(limit: int = 10) -> dict[str, Any]:
    """Get recent TTL decision history."""
    try:
        from AFO.cache.adaptive_ttl import get_adaptive_ttl_strategy

        strategy = get_adaptive_ttl_strategy()
        return {
            "history": strategy.get_history(limit),
            "stats": strategy.get_stats(),
        }
    except Exception as e:
        logger.error(f"Failed to get TTL history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invalidation/history")
async def get_invalidation_history(limit: int = 10) -> dict[str, Any]:
    """Get recent invalidation event history."""
    try:
        from AFO.cache.invalidation_engine import get_invalidation_engine

        engine = get_invalidation_engine()
        return {
            "history": engine.get_history(limit),
            "metrics": engine.get_metrics(),
        }
    except Exception as e:
        logger.error(f"Failed to get invalidation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/invalidate")
async def trigger_invalidation(
    pattern: str | None = None,
    tag: str | None = None,
) -> dict[str, Any]:
    """
    Manually trigger cache invalidation.

    Args:
        pattern: Cache key pattern to invalidate
        tag: Tag to invalidate all related entries
    """
    if not pattern and not tag:
        raise HTTPException(
            status_code=400,
            detail="Must provide either pattern or tag",
        )

    try:
        from AFO.cache.invalidation_engine import (
            InvalidationEvent,
            InvalidationScope,
            InvalidationTrigger,
            get_invalidation_engine,
        )

        engine = get_invalidation_engine()
        count = 0

        if pattern:
            event = InvalidationEvent(
                trigger=InvalidationTrigger.MANUAL,
                scope=InvalidationScope.PATTERN,
                pattern=pattern,
            )
            await engine.invalidate(event)
            count += 1

        if tag:
            count += await engine.invalidate_by_tag(tag)

        return {
            "success": True,
            "pattern": pattern,
            "tag": tag,
            "events_queued": count,
        }

    except Exception as e:
        logger.error(f"Invalidation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_expired_cache() -> dict[str, Any]:
    """Clean up expired cache entries."""
    try:
        from AFO.cache.semantic_cache import get_semantic_cache

        cache = get_semantic_cache()
        count = await cache.cleanup_expired()

        return {
            "success": True,
            "entries_removed": count,
        }

    except Exception as e:
        logger.error(f"Cache cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
