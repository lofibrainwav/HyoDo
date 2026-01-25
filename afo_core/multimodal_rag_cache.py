from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from AFO.utils.redis_connection import get_redis_client as get_redis_connection

# Trinity Score: 90.0 (Multimodal RAG Cache Module)
"""
Multimodal RAG Cache Module for AFO Kingdom

Redis 기반 멀티모달 RAG 캐시 시스템
텍스트, 이미지, 비디오 등 다양한 모달리티의 RAG 결과를 캐싱

眞善美孝永: Truth 95%, Goodness 90%, Beauty 85%, Serenity 100%, Eternity 95%
"""


# Configure logging
logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Any | None = None


def set_redis_client(client: Any) -> None:
    """Set the Redis client for caching."""
    global _redis_client
    _redis_client = client
    logger.info("✅ Multimodal RAG Cache Redis client 설정됨")


def get_redis_client() -> Any | None:
    """Get the configured Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = get_redis_connection()
            logger.info("✅ Multimodal RAG Cache Redis client 자동 설정됨")
        except Exception as e:
            logger.warning(f"⚠️ Multimodal RAG Cache Redis 연결 실패: {e}")
            return None
    return _redis_client


def _generate_cache_key(query: str, modality: str = "text") -> str:
    """Generate a cache key for the query."""
    content = f"{modality}:{query}"
    return f"multimodal_rag:{hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()}"


def get_cache(query: str, modality: str = "text") -> Any | None:
    """
    Get cached RAG result for the query.

    Args:
        query: The search query
        modality: The modality type

    Returns:
        The cached result or None if not found
    """
    client = get_redis_client()
    if not client:
        return None

    try:
        cache_key = _generate_cache_key(query, modality)
        cached_data = client.get(cache_key)

        if cached_data:
            logger.debug(f"✅ Multimodal RAG Cache hit: {query[:50]}...")
            return json.loads(cached_data)

        return None

    except Exception as e:
        logger.warning(f"⚠️ Multimodal RAG Cache get failed: {e}")
        return None


def set_cache(
    query: str,
    result: Any,
    modality: str = "text",
    ttl_seconds: int = 3600,
) -> bool:
    """
    Cache the RAG result for the query.

    Args:
        query: The search query
        result: The RAG result to cache
        modality: The modality type
        ttl_seconds: Time to live in seconds (default: 1 hour)

    Returns:
        True if cached successfully, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False

    try:
        cache_key = _generate_cache_key(query, modality)
        serialized_result = json.dumps(result, ensure_ascii=False)

        success = client.setex(cache_key, ttl_seconds, serialized_result)
        if success:
            logger.debug(f"✅ Multimodal RAG Cache set: {query[:50]}... (TTL: {ttl_seconds}s)")
        return bool(success)

    except Exception as e:
        logger.warning(f"⚠️ Multimodal RAG Cache set failed: {e}")
        return False


def clear_cache(pattern: str = "*") -> int:
    """
    Clear cache entries matching the pattern.

    Args:
        pattern: Redis key pattern to match (default: all multimodal_rag keys)

    Returns:
        Number of keys deleted
    """
    client = get_redis_client()
    if not client:
        return 0

    try:
        if pattern == "*":
            pattern = "multimodal_rag:*"

        keys = client.keys(pattern)
        if keys:
            deleted_count = client.delete(*keys)
            logger.info(f"✅ Multimodal RAG Cache cleared: {deleted_count} entries")
            return deleted_count  # type: ignore[no-any-return]
        else:
            logger.info("ℹ️ Multimodal RAG Cache: No entries to clear")
            return 0

    except Exception as e:
        logger.warning(f"⚠️ Multimodal RAG Cache clear failed: {e}")
        return 0


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache statistics
    """
    client = get_redis_client()
    if not client:
        return {"status": "redis_unavailable", "entries": 0}

    try:
        keys = client.keys("multimodal_rag:*")
        return {
            "status": "healthy",
            "entries": len(keys),
            "keys_sample": keys[:5] if keys else [],
        }

    except Exception as e:
        logger.warning(f"⚠️ Multimodal RAG Cache stats failed: {e}")
        return {"status": "error", "error": str(e)}


# Initialize Redis client on module import
try:
    get_redis_client()
except Exception:
    logger.warning("⚠️ Multimodal RAG Cache 초기화 실패 - Redis 연결 필요")
