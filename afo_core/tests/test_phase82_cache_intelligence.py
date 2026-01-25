# Trinity Score: 92.0 (Phase 82 - Cache Intelligence Tests)
"""
Phase 82 Integration Tests: Advanced Cache Intelligence

Tests for semantic cache, adaptive TTL, invalidation engine,
and multimodal document processor.
"""

import pytest


# ============================================================================
# Semantic Cache Tests
# ============================================================================
class TestSemanticCache:
    """Tests for semantic cache layer."""

    @pytest.fixture
    def semantic_cache(self):
        """Create a fresh semantic cache instance."""
        from AFO.cache.semantic_cache import SemanticCache

        return SemanticCache(similarity_threshold=0.85, max_entries=100)

    @pytest.mark.asyncio
    async def test_set_and_get_exact_match(self, semantic_cache):
        """Test exact match cache hit."""
        query = "What is my tax bracket?"
        value = {"bracket": "22%", "income": 50000}

        await semantic_cache.set(query, value, ttl=300)
        result, similarity = await semantic_cache.get(query)

        assert result == value
        assert similarity == 1.0

    @pytest.mark.asyncio
    async def test_cache_miss(self, semantic_cache):
        """Test cache miss for unrelated query."""
        await semantic_cache.set("What is the weather?", {"temp": 72}, ttl=300)
        result, similarity = await semantic_cache.get("Completely different query")

        # Should be a miss (similarity below threshold)
        assert result is None or similarity < 0.85

    @pytest.mark.asyncio
    async def test_invalidate_by_pattern(self, semantic_cache):
        """Test pattern-based invalidation."""
        await semantic_cache.set("tax query 1", {"data": 1}, ttl=300)
        await semantic_cache.set("tax query 2", {"data": 2}, ttl=300)
        await semantic_cache.set("weather query", {"data": 3}, ttl=300)

        count = await semantic_cache.invalidate(pattern="tax")

        assert count >= 2

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, semantic_cache):
        """Test metrics are tracked correctly."""
        await semantic_cache.set("query1", "value1", ttl=300)
        await semantic_cache.get("query1")  # Hit
        await semantic_cache.get("nonexistent")  # Miss

        metrics = semantic_cache.get_metrics()

        assert metrics["total_queries"] == 2
        assert metrics["exact_hits"] == 1
        assert metrics["misses"] == 1

    @pytest.mark.asyncio
    async def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        from AFO.cache.semantic_cache import SemanticCache

        cache = SemanticCache(max_entries=5)

        # Fill cache
        for i in range(5):
            await cache.set(f"query_{i}", f"value_{i}", ttl=300)

        # Access first entry to make it recent
        await cache.get("query_0")

        # Add one more to trigger eviction
        await cache.set("query_5", "value_5", ttl=300)

        # query_1 should be evicted (oldest not accessed)
        result, _ = await cache.get("query_1")
        assert result is None

        # query_0 should still exist (was accessed)
        result, _ = await cache.get("query_0")
        assert result == "value_0"


# ============================================================================
# Adaptive TTL Tests
# ============================================================================
class TestAdaptiveTTL:
    """Tests for adaptive TTL strategy."""

    @pytest.fixture
    def ttl_strategy(self):
        """Create a fresh TTL strategy instance."""
        from AFO.cache.adaptive_ttl import AdaptiveTTLStrategy, TTLConfig

        config = TTLConfig(
            ai_response_base=1800,
            excellent_multiplier=1.5,
            critical_multiplier=0.5,
        )
        return AdaptiveTTLStrategy(config)

    def test_excellent_state_extends_ttl(self, ttl_strategy):
        """Test TTL extension in excellent state."""
        decision = ttl_strategy.calculate_ttl(
            base_ttl=1000,
            trinity_score=98.0,
            entropy=0.05,
        )

        assert decision.final_ttl > 1000
        assert decision.system_state.value == "excellent"
        assert decision.multiplier >= 1.4

    def test_critical_state_reduces_ttl(self, ttl_strategy):
        """Test TTL reduction in critical state."""
        decision = ttl_strategy.calculate_ttl(
            base_ttl=1000,
            trinity_score=60.0,
            entropy=0.3,
        )

        assert decision.final_ttl < 1000
        assert decision.system_state.value == "critical"
        assert decision.multiplier <= 0.6

    def test_high_entropy_reduces_ttl(self, ttl_strategy):
        """Test high entropy reduces TTL."""
        # Same trinity score, different entropy
        low_entropy = ttl_strategy.calculate_ttl(
            base_ttl=1000,
            trinity_score=90.0,
            entropy=0.05,
        )
        high_entropy = ttl_strategy.calculate_ttl(
            base_ttl=1000,
            trinity_score=90.0,
            entropy=0.5,
        )

        assert high_entropy.final_ttl < low_entropy.final_ttl

    def test_ttl_bounds(self, ttl_strategy):
        """Test TTL stays within bounds."""
        # Very low TTL request
        decision = ttl_strategy.calculate_ttl(
            base_ttl=10,
            trinity_score=60.0,
            entropy=0.9,
        )
        assert decision.final_ttl >= ttl_strategy.config.min_ttl

        # Very high TTL request
        decision = ttl_strategy.calculate_ttl(
            base_ttl=1000000,
            trinity_score=99.0,
            entropy=0.0,
        )
        assert decision.final_ttl <= ttl_strategy.config.max_ttl

    def test_history_tracking(self, ttl_strategy):
        """Test TTL decision history is tracked."""
        for i in range(5):
            ttl_strategy.calculate_ttl(
                base_ttl=1000,
                trinity_score=80 + i * 4,
                entropy=0.1,
            )

        history = ttl_strategy.get_history(limit=3)
        assert len(history) == 3

        stats = ttl_strategy.get_stats()
        assert stats["decisions_made"] == 5


# ============================================================================
# Invalidation Engine Tests
# ============================================================================
class TestInvalidationEngine:
    """Tests for intelligent cache invalidation engine."""

    @pytest.fixture
    def invalidation_engine(self):
        """Create a fresh invalidation engine instance."""
        from AFO.cache.invalidation_engine import InvalidationEngine

        return InvalidationEngine()

    @pytest.mark.asyncio
    async def test_event_queuing(self, invalidation_engine):
        """Test events are queued properly."""
        from AFO.cache.invalidation_engine import (
            InvalidationEvent,
            InvalidationScope,
            InvalidationTrigger,
        )

        event = InvalidationEvent(
            trigger=InvalidationTrigger.MANUAL,
            scope=InvalidationScope.PATTERN,
            pattern="test:*",
        )

        await invalidation_engine.invalidate(event)

        metrics = invalidation_engine.get_metrics()
        assert metrics["queue_size"] >= 1

    @pytest.mark.asyncio
    async def test_irs_change_patterns(self, invalidation_engine):
        """Test IRS change triggers correct patterns."""
        await invalidation_engine.invalidate_on_irs_change(
            change_type="form",
            change_id="test-123",
            severity="warning",
        )

        metrics = invalidation_engine.get_metrics()
        assert metrics["irs_invalidations"] >= 1

    @pytest.mark.asyncio
    async def test_dependency_graph(self, invalidation_engine):
        """Test dependency graph for cascade invalidation."""
        # Create dependencies: A -> B -> C
        await invalidation_engine.add_dependency("cache:B", "cache:A")
        await invalidation_engine.add_dependency("cache:C", "cache:B")

        # Get cascade keys for A
        cascade = await invalidation_engine.dependency_graph.get_cascade_keys("cache:A")

        assert "cache:B" in cascade
        assert "cache:C" in cascade

    @pytest.mark.asyncio
    async def test_tag_based_invalidation(self, invalidation_engine):
        """Test tag-based invalidation."""
        await invalidation_engine.add_dependency(
            "cache:user:1",
            "cache:base",
            tags={"user_data"},
        )
        await invalidation_engine.add_dependency(
            "cache:user:2",
            "cache:base",
            tags={"user_data"},
        )

        keys = await invalidation_engine.dependency_graph.get_keys_by_tag("user_data")

        assert len(keys) >= 2

    def test_handler_registration(self, invalidation_engine):
        """Test handler registration."""
        from AFO.cache.invalidation_engine import InvalidationTrigger

        async def test_handler(_event):
            return 0

        invalidation_engine.register_handler(
            InvalidationTrigger.MANUAL,
            test_handler,
        )

        metrics = invalidation_engine.get_metrics()
        assert metrics["handlers_registered"] >= 1


# ============================================================================
# Multimodal Document Processor Tests
# ============================================================================
class TestMultimodalProcessor:
    """Tests for multimodal document processor."""

    def test_document_type_detection(self):
        """Test document type detection."""
        from AFO.rag.multimodal_document_processor import (
            DocumentType,
            detect_document_type,
        )

        assert detect_document_type("test.pdf") == DocumentType.PDF
        assert detect_document_type("audio.mp3") == DocumentType.AUDIO
        assert detect_document_type("video.mp4") == DocumentType.VIDEO
        assert detect_document_type("image.png") == DocumentType.IMAGE
        assert detect_document_type("readme.txt") == DocumentType.TEXT

    def test_document_id_generation(self):
        """Test unique document ID generation."""
        from AFO.rag.multimodal_document_processor import generate_document_id

        id1 = generate_document_id("/path/to/file1.pdf")
        id2 = generate_document_id("/path/to/file2.pdf")
        id3 = generate_document_id("/path/to/file1.pdf")

        # Different paths = different IDs
        assert id1 != id2

        # Same path = same ID
        assert id1 == id3

    def test_pdf_processor_chunking(self):
        """Test PDF processor text chunking logic."""
        from AFO.rag.multimodal_document_processor import PDFProcessor

        processor = PDFProcessor(chunk_size=10, chunk_overlap=2)
        text = " ".join([f"word{i}" for i in range(25)])

        chunks = processor._chunk_text(text)

        assert len(chunks) >= 2
        assert all(len(c.content.split()) <= 10 for c in chunks)

    def test_processor_stats(self):
        """Test processor statistics."""
        from AFO.rag.multimodal_document_processor import MultimodalDocumentProcessor

        processor = MultimodalDocumentProcessor()
        stats = processor.get_stats()

        assert "total_documents" in stats
        assert stats["total_documents"] == 0


# ============================================================================
# Cache Metrics API Tests
# ============================================================================
class TestCacheMetricsAPI:
    """Tests for cache metrics API endpoint."""

    @pytest.fixture
    def mock_metrics(self):
        """Return mock cache metrics."""
        return {
            "semantic": {
                "total_queries": 100,
                "hit_rate": 45.5,
                "semantic_hit_rate": 15.2,
                "exact_hits": 30,
                "semantic_hits": 15,
                "misses": 55,
                "invalidations": 5,
                "cache_size": 50,
                "avg_similarity": 0.82,
            },
            "adaptive_ttl": {
                "decisions_made": 100,
                "avg_multiplier": 1.15,
                "min_multiplier": 0.5,
                "max_multiplier": 1.5,
                "current_trinity_score": 92.5,
                "current_entropy": 0.12,
                "state_distribution": {"healthy": 60, "normal": 30, "degraded": 10},
            },
            "invalidation": {
                "total_events": 50,
                "total_invalidations": 200,
                "cascade_invalidations": 30,
                "irs_invalidations": 10,
                "errors": 2,
                "queue_size": 0,
                "running": True,
            },
        }

    def test_response_model_structure(self):
        """Test response model structure."""
        from api.routers.cache_metrics import CacheMetricsResponse

        response = CacheMetricsResponse(
            total_queries=100,
            hit_rate=50.0,
            semantic_hit_rate=20.0,
        )

        assert response.total_queries == 100
        assert response.hit_rate == 50.0


# ============================================================================
# Integration Tests
# ============================================================================
class TestPhase82Integration:
    """Integration tests for Phase 82 components."""

    @pytest.mark.asyncio
    async def test_semantic_cache_with_adaptive_ttl(self):
        """Test semantic cache uses adaptive TTL."""
        from AFO.cache.adaptive_ttl import get_adaptive_ttl_strategy
        from AFO.cache.semantic_cache import SemanticCache

        ttl_strategy = get_adaptive_ttl_strategy()
        cache = SemanticCache()

        # Get adaptive TTL
        decision = ttl_strategy.calculate_ttl(
            base_ttl=1800,
            trinity_score=95.0,
            entropy=0.1,
        )

        # Use adaptive TTL for cache set
        await cache.set(
            "test query",
            {"result": "data"},
            ttl=decision.final_ttl,
        )

        result, _ = await cache.get("test query")
        assert result == {"result": "data"}

    @pytest.mark.asyncio
    async def test_irs_event_triggers_invalidation(self):
        """Test IRS events trigger cache invalidation."""
        from AFO.cache.invalidation_engine import get_invalidation_engine
        from AFO.cache.semantic_cache import SemanticCache

        engine = get_invalidation_engine()
        cache = SemanticCache()

        # Set up cache entry
        await cache.set("tax calculation", {"bracket": "22%"}, ttl=3600)

        # Trigger IRS change
        await engine.invalidate_on_irs_change(
            change_type="rate",
            change_id="irs-2026-001",
            severity="critical",
        )

        # Verify invalidation was triggered
        metrics = engine.get_metrics()
        assert metrics["irs_invalidations"] >= 1

    def test_unified_metrics(self):
        """Test unified metrics collection."""
        from AFO.cache import get_cache_metrics

        metrics = get_cache_metrics()

        # Should have all Phase 82 sections
        assert "semantic" in metrics
        assert "adaptive_ttl" in metrics
        assert "invalidation" in metrics
