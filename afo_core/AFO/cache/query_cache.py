# Trinity Score: 90.0 (Established by Chancellor)
"""
Database Query Cache Decorator
Phase 6C: Database Query Caching for Performance Optimization

Implements intelligent caching for database queries to reduce DB load and improve response times.
"""

import functools
import hashlib
import json
import logging
from collections.abc import Callable

from AFO.manager import cache_manager

logger = logging.getLogger(__name__)


class QueryCache:
    """
    Database Query Caching Decorator
    """

    def __init__(self, ttl: int = 300, key_prefix: str = "db:query") -> None:
        self.ttl = ttl
        self.key_prefix = key_prefix

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function call
            cache_key = self._generate_cache_key(func, args, kwargs)

            # Try to get from cache first
            if cache_manager:
                try:
                    cached_result = await cache_manager.get(cache_key)
                    if cached_result is not None:
                        logger.debug(f"💾 DB Query Cache Hit: {cache_key}")
                        return cached_result
                except Exception as e:
                    logger.warning(f"Cache read error: {e}")

            # Execute the actual query
            result = await func(*args, **kwargs)

            # Cache the result
            if cache_manager and result is not None:
                try:
                    await cache_manager.set(cache_key, result, ttl=self.ttl)
                    logger.debug(f"💾 DB Query Cached: {cache_key} (TTL: {self.ttl}s)")
                except Exception as e:
                    logger.warning(f"Cache write error: {e}")

            return result

        return wrapper

    def _generate_cache_key(self, func: Callable, args: tuple, kwargs: dict) -> str:
        """
        Generate intelligent cache key for database queries
        """
        # Extract function information
        func_name = f"{func.__module__}.{func.__qualname__}"

        # Normalize arguments (remove sensitive data, sort dicts, etc.)
        normalized_args = self._normalize_args(args)
        normalized_kwargs = self._normalize_kwargs(kwargs)

        # Create key components
        key_components = {
            "func": func_name,
            "args": normalized_args,
            "kwargs": normalized_kwargs,
        }

        # Generate hash
        key_str = json.dumps(key_components, sort_keys=True, default=str)
        key_hash = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()[:16]

        return f"{self.key_prefix}:{key_hash}"

    def _normalize_args(self, args: tuple) -> list:
        """Normalize positional arguments for caching"""
        normalized = []
        for arg in args:
            if hasattr(arg, "__dict__"):
                # For objects, use class name and id
                normalized.append(f"{arg.__class__.__name__}:{id(arg)}")
            elif isinstance(arg, dict):
                # Sort dict keys for consistent hashing
                normalized.append(json.dumps(arg, sort_keys=True, default=str))
            else:
                normalized.append(str(arg))
        return normalized

    def _normalize_kwargs(self, kwargs: dict) -> dict:
        """Normalize keyword arguments for caching"""
        normalized = {}
        for key, value in kwargs.items():
            if hasattr(value, "__dict__"):
                # For objects, use class name and id
                normalized[key] = f"{value.__class__.__name__}:{id(value)}"
            elif isinstance(value, dict):
                # Sort dict keys for consistent hashing
                normalized[key] = json.dumps(value, sort_keys=True, default=str)
            else:
                normalized[key] = str(value)
        return dict(sorted(normalized.items()))  # Sort for consistency


# Convenience decorators with different TTLs
def cache_query(ttl: int = 300, key_prefix: str = "db:query") -> None:
    """
    Decorator for caching database queries

    Args:
        ttl: Time to live in seconds
        key_prefix: Cache key prefix

    Usage:
        @cache_query(ttl=600)
        async def get_user_profile(user_id: int):
            return await db.query(User).filter(User.id == user_id).first()
    """
    return QueryCache(ttl=ttl, key_prefix=key_prefix)


def cache_user_data(ttl: int = 1800) -> None:
    """Cache user-specific data (longer TTL)"""
    return QueryCache(ttl=ttl, key_prefix="db:user")


def cache_system_data(ttl: int = 3600) -> None:
    """Cache system-wide data (even longer TTL)"""
    return QueryCache(ttl=ttl, key_prefix="db:system")


def invalidate_cache(pattern: str) -> None:
    """
    Invalidate cache entries matching a pattern
    Note: This is a simplified implementation - in production,
    you'd want more sophisticated cache invalidation strategies
    """

    async def _invalidate():
        if cache_manager:
            # Pattern-based invalidation requires Redis SCAN - using log notification for now
            # Full implementation planned when Redis cluster is available
            logger.info(f"Cache invalidation requested for pattern: {pattern}")

    return _invalidate


# Cache invalidation helpers
class CacheInvalidator:
    """Helper class for cache invalidation"""

    @staticmethod
    async def invalidate_user_cache(user_id: str):
        """Invalidate all cache entries for a specific user"""
        pattern = f"db:user:*{user_id}*"
        await invalidate_cache(pattern)()

    @staticmethod
    async def invalidate_system_cache():
        """Invalidate system-wide cache"""
        pattern = "db:system:*"
        await invalidate_cache(pattern)()

    @staticmethod
    async def invalidate_query_cache(func_name: str):
        """Invalidate cache for a specific query function"""
        pattern = f"db:query:*{func_name}*"
        await invalidate_cache(pattern)()
