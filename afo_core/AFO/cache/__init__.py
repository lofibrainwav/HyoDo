# Trinity Score: 92.0 (Established by Chancellor - Phase 82 Enhanced)
"""
AFO Unified Cache System

Phase 6B: Intelligent Cache Revolution
Phase 82: Advanced Semantic Cache + Adaptive TTL + Intelligent Invalidation

Implements multi-level caching with predictive capabilities,
semantic similarity matching, and Trinity Score-based TTL.
"""

from typing import Any

from AFO.backends import MemoryBackend, RedisBackend

# Phase 82: Advanced Cache Components
from AFO.cache.adaptive_ttl import (
    AdaptiveTTLStrategy,
    TTLConfig,
    TTLDecision,
    calculate_adaptive_ttl,
    get_adaptive_ttl_strategy,
)
from AFO.cache.invalidation_engine import (
    DependencyGraph,
    InvalidationEngine,
    InvalidationEvent,
    InvalidationTrigger,
    get_invalidation_engine,
    setup_invalidation_handlers,
)
from AFO.cache.semantic_cache import (
    SemanticCache,
    SemanticCacheEntry,
    SemanticCacheMetrics,
    get_semantic_cache,
    semantic_cache_get,
    semantic_cache_set,
)
from AFO.manager import MultiLevelCache, cache_manager
from AFO.predictive import PredictiveCacheManager, predictive_manager
from AFO.query_cache import (
    CacheInvalidator,
    QueryCache,
    cache_query,
    cache_system_data,
    cache_user_data,
    invalidate_cache,
)


def get_cache_metrics() -> dict[str, Any]:
    """Phase 6B + 82: Get unified cache performance metrics"""
    metrics = cache_manager.get_metrics()

    # Add semantic cache metrics
    try:
        semantic = get_semantic_cache()
        metrics["semantic"] = semantic.get_metrics()
    except Exception:
        metrics["semantic"] = {}

    # Add adaptive TTL stats
    try:
        ttl_strategy = get_adaptive_ttl_strategy()
        metrics["adaptive_ttl"] = ttl_strategy.get_stats()
    except Exception:
        metrics["adaptive_ttl"] = {}

    # Add invalidation engine metrics
    try:
        engine = get_invalidation_engine()
        metrics["invalidation"] = engine.get_metrics()
    except Exception:
        metrics["invalidation"] = {}

    return metrics


__all__ = [
    # Phase 6B exports
    "CacheInvalidator",
    "MemoryBackend",
    "MultiLevelCache",
    "PredictiveCacheManager",
    "QueryCache",
    "RedisBackend",
    "cache_manager",
    "cache_query",
    "cache_system_data",
    "cache_user_data",
    "get_cache_metrics",
    "invalidate_cache",
    "predictive_manager",
    # Phase 82: Semantic Cache
    "SemanticCache",
    "SemanticCacheEntry",
    "SemanticCacheMetrics",
    "get_semantic_cache",
    "semantic_cache_get",
    "semantic_cache_set",
    # Phase 82: Invalidation Engine
    "DependencyGraph",
    "InvalidationEngine",
    "InvalidationEvent",
    "InvalidationTrigger",
    "get_invalidation_engine",
    "setup_invalidation_handlers",
    # Phase 82: Adaptive TTL
    "AdaptiveTTLStrategy",
    "TTLConfig",
    "TTLDecision",
    "calculate_adaptive_ttl",
    "get_adaptive_ttl_strategy",
]
