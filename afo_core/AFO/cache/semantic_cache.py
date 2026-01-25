# Trinity Score: 92.0 (眞 Truth - Semantic Precision)
"""
Semantic Cache Layer - Phase 82

Query embedding 기반 의미적 캐시 시스템.
동일 의도의 다른 표현 쿼리도 캐시 히트 가능.

Example:
    "What's my tax bracket?" + "Show me my income tier" = CACHE HIT
"""

import asyncio
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# Default similarity threshold for semantic matching
DEFAULT_SIMILARITY_THRESHOLD = 0.85


@dataclass
class SemanticCacheEntry:
    """Semantic cache entry with embedding vector."""

    key: str
    query: str
    embedding: list[float]
    value: Any
    ttl: int
    created_at: datetime = field(default_factory=datetime.now)
    hit_count: int = 0
    last_accessed: datetime | None = None

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl


@dataclass
class SemanticCacheMetrics:
    """Metrics for semantic cache performance."""

    total_queries: int = 0
    exact_hits: int = 0
    semantic_hits: int = 0
    misses: int = 0
    invalidations: int = 0
    avg_similarity: float = 0.0
    similarity_samples: list[float] = field(default_factory=list)

    @property
    def hit_rate(self) -> float:
        """Calculate overall hit rate."""
        if self.total_queries == 0:
            return 0.0
        return (self.exact_hits + self.semantic_hits) / self.total_queries

    @property
    def semantic_hit_rate(self) -> float:
        """Calculate semantic-only hit rate."""
        if self.total_queries == 0:
            return 0.0
        return self.semantic_hits / self.total_queries

    def record_similarity(self, similarity: float) -> None:
        """Record similarity score for averaging."""
        self.similarity_samples.append(similarity)
        # Keep only last 1000 samples
        if len(self.similarity_samples) > 1000:
            self.similarity_samples = self.similarity_samples[-1000:]
        self.avg_similarity = sum(self.similarity_samples) / len(self.similarity_samples)

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_queries": self.total_queries,
            "exact_hits": self.exact_hits,
            "semantic_hits": self.semantic_hits,
            "misses": self.misses,
            "invalidations": self.invalidations,
            "hit_rate": round(self.hit_rate * 100, 2),
            "semantic_hit_rate": round(self.semantic_hit_rate * 100, 2),
            "avg_similarity": round(self.avg_similarity, 4),
        }


class EmbeddingProvider:
    """Embedding provider abstraction for query vectorization."""

    def __init__(self, model_name: str = "nomic-embed-text") -> None:
        self.model_name = model_name
        self._client: Any = None

    async def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text using Ollama."""
        try:
            # Lazy import to avoid dependency issues
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": self.model_name, "prompt": text},
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding", [])
                logger.warning(f"Embedding request failed: {response.status_code}")
                return self._fallback_embedding(text)
        except Exception as e:
            logger.warning(f"Ollama embedding error: {e}, using fallback")
            return self._fallback_embedding(text)

    def _fallback_embedding(self, text: str) -> list[float]:
        """Fallback: simple hash-based pseudo-embedding for resilience."""
        # Generate deterministic pseudo-embedding from text hash
        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to 384-dimensional float vector (normalized)
        embedding = []
        for i in range(0, min(len(hash_bytes), 32), 1):
            val = (hash_bytes[i] - 128) / 128.0
            embedding.extend([val] * 12)  # 32 * 12 = 384 dimensions
        return embedding[:384]


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    arr1 = np.array(vec1)
    arr2 = np.array(vec2)

    dot_product = np.dot(arr1, arr2)
    norm1 = np.linalg.norm(arr1)
    norm2 = np.linalg.norm(arr2)

    if norm1 == 0 or norm2 == 0:
        return 0.0

    return float(dot_product / (norm1 * norm2))


class SemanticCache:
    """
    Semantic Cache Layer for intent-based query matching.

    Uses embedding vectors to find semantically similar queries,
    enabling cache hits even when exact query strings differ.
    """

    def __init__(
        self,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        max_entries: int = 10000,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.embedding_provider = embedding_provider or EmbeddingProvider()
        self._cache: dict[str, SemanticCacheEntry] = {}
        self._lock = asyncio.Lock()
        self.metrics = SemanticCacheMetrics()

    async def get(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[Any | None, float]:
        """
        Get cached value for query using semantic matching.

        Returns:
            Tuple of (value, similarity_score). Value is None if no match found.
        """
        self.metrics.total_queries += 1

        # First, try exact match using query hash
        exact_key = self._generate_exact_key(query, context)
        if exact_key in self._cache:
            entry = self._cache[exact_key]
            if not entry.is_expired():
                entry.hit_count += 1
                entry.last_accessed = datetime.now()
                self.metrics.exact_hits += 1
                logger.debug(f"💾 Semantic Cache EXACT HIT: {exact_key[:32]}...")
                return entry.value, 1.0

        # If no exact match, try semantic matching
        query_embedding = await self.embedding_provider.get_embedding(query)
        if not query_embedding:
            self.metrics.misses += 1
            return None, 0.0

        best_match: SemanticCacheEntry | None = None
        best_similarity = 0.0

        async with self._lock:
            for entry in self._cache.values():
                if entry.is_expired():
                    continue

                similarity = cosine_similarity(query_embedding, entry.embedding)
                self.metrics.record_similarity(similarity)

                if similarity > best_similarity and similarity >= self.similarity_threshold:
                    best_similarity = similarity
                    best_match = entry

        if best_match:
            best_match.hit_count += 1
            best_match.last_accessed = datetime.now()
            self.metrics.semantic_hits += 1
            logger.debug(
                f"💾 Semantic Cache SEMANTIC HIT: {best_match.key[:32]}... "
                f"(similarity: {best_similarity:.4f})"
            )
            return best_match.value, best_similarity

        self.metrics.misses += 1
        return None, 0.0

    async def set(
        self,
        query: str,
        value: Any,
        ttl: int = 1800,
        context: dict[str, Any] | None = None,
    ) -> str:
        """
        Set cache entry with semantic embedding.

        Returns:
            The cache key for the entry.
        """
        key = self._generate_exact_key(query, context)
        embedding = await self.embedding_provider.get_embedding(query)

        entry = SemanticCacheEntry(
            key=key,
            query=query,
            embedding=embedding,
            value=value,
            ttl=ttl,
        )

        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_entries:
                await self._evict_lru()

            self._cache[key] = entry

        logger.debug(f"💾 Semantic Cache SET: {key[:32]}... (TTL: {ttl}s)")
        return key

    async def invalidate(self, pattern: str | None = None, key: str | None = None) -> int:
        """
        Invalidate cache entries by pattern or key.

        Returns:
            Number of invalidated entries.
        """
        count = 0
        async with self._lock:
            if key and key in self._cache:
                del self._cache[key]
                count = 1
            elif pattern:
                keys_to_delete = [k for k in self._cache if pattern.lower() in k.lower()]
                for k in keys_to_delete:
                    del self._cache[k]
                    count += 1

        self.metrics.invalidations += count
        logger.info(f"💾 Semantic Cache INVALIDATED: {count} entries")
        return count

    async def invalidate_by_similarity(
        self,
        query: str,
        threshold: float | None = None,
    ) -> int:
        """
        Invalidate all entries semantically similar to query.

        Useful for invalidating related queries when source data changes.
        """
        threshold = threshold or self.similarity_threshold
        query_embedding = await self.embedding_provider.get_embedding(query)
        if not query_embedding:
            return 0

        count = 0
        async with self._lock:
            keys_to_delete = []
            for key, entry in self._cache.items():
                similarity = cosine_similarity(query_embedding, entry.embedding)
                if similarity >= threshold:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                del self._cache[key]
                count += 1

        self.metrics.invalidations += count
        logger.info(f"💾 Semantic Cache SIMILARITY INVALIDATED: {count} entries")
        return count

    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return

        # Sort by last_accessed (None = never accessed = oldest)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at,
        )

        # Remove oldest 10%
        evict_count = max(1, len(sorted_entries) // 10)
        for key, _ in sorted_entries[:evict_count]:
            del self._cache[key]

        logger.debug(f"💾 Semantic Cache LRU EVICTION: {evict_count} entries")

    def _generate_exact_key(
        self,
        query: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """Generate exact match key from query and context."""
        key_data = {"query": query.strip().lower()}
        if context:
            key_data["context"] = json.dumps(context, sort_keys=True, default=str)

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics."""
        return {
            **self.metrics.to_dict(),
            "cache_size": len(self._cache),
            "max_entries": self.max_entries,
            "similarity_threshold": self.similarity_threshold,
        }

    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        count = 0
        async with self._lock:
            keys_to_delete = [key for key, entry in self._cache.items() if entry.is_expired()]
            for key in keys_to_delete:
                del self._cache[key]
                count += 1

        if count > 0:
            logger.info(f"💾 Semantic Cache CLEANUP: {count} expired entries removed")
        return count


# Global singleton instance
_semantic_cache: SemanticCache | None = None


def get_semantic_cache() -> SemanticCache:
    """Get or create the global semantic cache instance."""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache


async def semantic_cache_get(
    query: str,
    context: dict[str, Any] | None = None,
) -> tuple[Any | None, float]:
    """Convenience function to get from semantic cache."""
    cache = get_semantic_cache()
    return await cache.get(query, context)


async def semantic_cache_set(
    query: str,
    value: Any,
    ttl: int = 1800,
    context: dict[str, Any] | None = None,
) -> str:
    """Convenience function to set in semantic cache."""
    cache = get_semantic_cache()
    return await cache.set(query, value, ttl, context)
