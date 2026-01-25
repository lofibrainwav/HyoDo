# Trinity Score: 94.0 (善 Goodness - Safety & Correctness)
"""
Intelligent Cache Invalidation Engine - Phase 82

Event-driven cache invalidation based on IRS changes and data dependencies.
Prevents stale data while minimizing over-invalidation.

Features:
    - IRS SSE event subscription
    - Dependency graph for cascade invalidation
    - Pattern-based invalidation
    - Semantic similarity invalidation
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InvalidationTrigger(str, Enum):
    """Types of cache invalidation triggers."""

    IRS_CHANGE = "irs_change"
    DATA_UPDATE = "data_update"
    SCHEMA_CHANGE = "schema_change"
    MANUAL = "manual"
    TTL_EXPIRED = "ttl_expired"
    CASCADE = "cascade"


class InvalidationScope(str, Enum):
    """Scope of cache invalidation."""

    GLOBAL = "global"
    USER = "user"
    QUERY = "query"
    PATTERN = "pattern"
    SEMANTIC = "semantic"


@dataclass
class InvalidationEvent:
    """Represents a cache invalidation event."""

    trigger: InvalidationTrigger
    scope: InvalidationScope
    pattern: str | None = None
    user_id: str | None = None
    query: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    cascade_from: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "trigger": self.trigger.value,
            "scope": self.scope.value,
            "pattern": self.pattern,
            "user_id": self.user_id,
            "query": self.query,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "cascade_from": self.cascade_from,
        }


@dataclass
class InvalidationResult:
    """Result of an invalidation operation."""

    success: bool
    entries_invalidated: int
    duration_ms: float
    event: InvalidationEvent
    cascades: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class DependencyNode:
    """Node in the cache dependency graph."""

    key: str
    dependencies: set[str] = field(default_factory=set)
    dependents: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class DependencyGraph:
    """
    Cache dependency graph for cascade invalidation.

    Tracks relationships between cached data to enable
    proper invalidation when source data changes.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, DependencyNode] = {}
        self._tag_index: dict[str, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def add_dependency(
        self,
        key: str,
        depends_on: str | list[str],
        tags: set[str] | None = None,
    ) -> None:
        """Add a dependency relationship."""
        async with self._lock:
            if key not in self._nodes:
                self._nodes[key] = DependencyNode(key=key)

            deps = [depends_on] if isinstance(depends_on, str) else depends_on
            for dep in deps:
                if dep not in self._nodes:
                    self._nodes[dep] = DependencyNode(key=dep)

                self._nodes[key].dependencies.add(dep)
                self._nodes[dep].dependents.add(key)

            if tags:
                self._nodes[key].tags.update(tags)
                for tag in tags:
                    self._tag_index[tag].add(key)

    async def get_cascade_keys(self, key: str) -> set[str]:
        """Get all keys that should be invalidated when key changes."""
        cascade = set()
        visited = set()
        queue = [key]

        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)

            if current in self._nodes:
                for dependent in self._nodes[current].dependents:
                    if dependent not in visited:
                        cascade.add(dependent)
                        queue.append(dependent)

        return cascade

    async def get_keys_by_tag(self, tag: str) -> set[str]:
        """Get all keys with a specific tag."""
        return self._tag_index.get(tag, set()).copy()

    async def remove_key(self, key: str) -> None:
        """Remove a key from the dependency graph."""
        async with self._lock:
            if key not in self._nodes:
                return

            node = self._nodes[key]

            # Remove from dependents' dependencies
            for dep in node.dependencies:
                if dep in self._nodes:
                    self._nodes[dep].dependents.discard(key)

            # Remove from dependencies' dependents
            for dependent in node.dependents:
                if dependent in self._nodes:
                    self._nodes[dependent].dependencies.discard(key)

            # Remove from tag index
            for tag in node.tags:
                self._tag_index[tag].discard(key)

            del self._nodes[key]


# IRS change type to cache pattern mapping
IRS_CHANGE_PATTERNS: dict[str, list[str]] = {
    "form": ["tax:*", "filing:*", "return:*"],
    "guidance": ["advice:*", "recommendation:*", "strategy:*"],
    "rate": ["calculation:*", "bracket:*", "deduction:*"],
    "deadline": ["schedule:*", "reminder:*", "calendar:*"],
    "regulation": ["compliance:*", "rule:*", "requirement:*"],
}


class InvalidationEngine:
    """
    Intelligent cache invalidation engine.

    Coordinates cache invalidation across multiple sources
    based on events, dependencies, and semantic relationships.
    """

    def __init__(self) -> None:
        self.dependency_graph = DependencyGraph()
        self._event_queue: asyncio.Queue[InvalidationEvent] = asyncio.Queue(maxsize=1000)
        self._handlers: dict[InvalidationTrigger, list] = defaultdict(list)
        self._running = False
        self._worker_task: asyncio.Task | None = None
        self._metrics = {
            "total_events": 0,
            "total_invalidations": 0,
            "cascade_invalidations": 0,
            "irs_invalidations": 0,
            "errors": 0,
        }
        self._history: list[InvalidationResult] = []

    def register_handler(
        self,
        trigger: InvalidationTrigger,
        handler: Any,
    ) -> None:
        """Register an invalidation handler for a trigger type."""
        self._handlers[trigger].append(handler)
        logger.info(f"Registered invalidation handler for {trigger.value}")

    async def start(self) -> None:
        """Start the invalidation engine worker."""
        if self._running:
            return

        self._running = True
        self._worker_task = asyncio.create_task(self._process_events())
        logger.info("🔄 Invalidation Engine started")

    async def stop(self) -> None:
        """Stop the invalidation engine worker."""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("🔄 Invalidation Engine stopped")

    async def _process_events(self) -> None:
        """Background worker to process invalidation events."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0,
                )
                await self._handle_event(event)
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing invalidation event: {e}")
                self._metrics["errors"] += 1

    async def _handle_event(self, event: InvalidationEvent) -> InvalidationResult:
        """Handle a single invalidation event."""
        start_time = datetime.now()
        self._metrics["total_events"] += 1

        result = InvalidationResult(
            success=True,
            entries_invalidated=0,
            duration_ms=0,
            event=event,
        )

        try:
            # Call registered handlers
            for handler in self._handlers.get(event.trigger, []):
                try:
                    count = await handler(event)
                    result.entries_invalidated += count
                except Exception as e:
                    result.errors.append(str(e))
                    logger.error(f"Handler error: {e}")

            # Handle cascade invalidation
            if event.pattern:
                cascade_keys = await self.dependency_graph.get_cascade_keys(event.pattern)
                for key in cascade_keys:
                    cascade_event = InvalidationEvent(
                        trigger=InvalidationTrigger.CASCADE,
                        scope=InvalidationScope.PATTERN,
                        pattern=key,
                        cascade_from=event.pattern,
                    )
                    await self._event_queue.put(cascade_event)
                    result.cascades.append(key)
                    self._metrics["cascade_invalidations"] += 1

            self._metrics["total_invalidations"] += result.entries_invalidated

        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            self._metrics["errors"] += 1
            logger.error(f"Invalidation error: {e}")

        duration = (datetime.now() - start_time).total_seconds() * 1000
        result.duration_ms = round(duration, 2)

        # Keep history (last 100 events)
        self._history.append(result)
        if len(self._history) > 100:
            self._history = self._history[-100:]

        logger.info(
            f"🔄 Invalidation complete: {result.entries_invalidated} entries "
            f"({result.duration_ms}ms)"
        )
        return result

    async def invalidate(self, event: InvalidationEvent) -> None:
        """Queue an invalidation event for processing."""
        try:
            self._event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Invalidation queue full, processing synchronously")
            await self._handle_event(event)

    async def invalidate_on_irs_change(
        self,
        change_type: str,
        change_id: str,
        severity: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Handle IRS change events and invalidate related caches.

        Maps IRS change types to cache patterns for targeted invalidation.
        """
        self._metrics["irs_invalidations"] += 1

        patterns = IRS_CHANGE_PATTERNS.get(change_type, ["irs:*"])

        for pattern in patterns:
            event = InvalidationEvent(
                trigger=InvalidationTrigger.IRS_CHANGE,
                scope=InvalidationScope.PATTERN,
                pattern=pattern,
                metadata={
                    "change_id": change_id,
                    "change_type": change_type,
                    "severity": severity,
                    **(metadata or {}),
                },
            )
            await self.invalidate(event)

        logger.info(f"🔄 IRS Change [{change_type}] triggered invalidation: {patterns}")

    async def add_dependency(
        self,
        cache_key: str,
        depends_on: str | list[str],
        tags: set[str] | None = None,
    ) -> None:
        """Add a cache dependency for cascade invalidation."""
        await self.dependency_graph.add_dependency(cache_key, depends_on, tags)

    async def invalidate_by_tag(self, tag: str) -> int:
        """Invalidate all cache entries with a specific tag."""
        keys = await self.dependency_graph.get_keys_by_tag(tag)
        count = 0

        for key in keys:
            event = InvalidationEvent(
                trigger=InvalidationTrigger.DATA_UPDATE,
                scope=InvalidationScope.PATTERN,
                pattern=key,
                metadata={"tag": tag},
            )
            await self.invalidate(event)
            count += 1

        return count

    def get_metrics(self) -> dict[str, Any]:
        """Get engine performance metrics."""
        return {
            **self._metrics,
            "queue_size": self._event_queue.qsize(),
            "running": self._running,
            "handlers_registered": sum(len(h) for h in self._handlers.values()),
        }

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent invalidation history."""
        return [
            {
                "success": r.success,
                "entries": r.entries_invalidated,
                "duration_ms": r.duration_ms,
                "trigger": r.event.trigger.value,
                "scope": r.event.scope.value,
                "cascades": len(r.cascades),
                "errors": len(r.errors),
                "timestamp": r.event.timestamp.isoformat(),
            }
            for r in self._history[-limit:]
        ]


# Global singleton instance
_invalidation_engine: InvalidationEngine | None = None


def get_invalidation_engine() -> InvalidationEngine:
    """Get or create the global invalidation engine instance."""
    global _invalidation_engine
    if _invalidation_engine is None:
        _invalidation_engine = InvalidationEngine()
    return _invalidation_engine


async def setup_invalidation_handlers() -> None:
    """Setup default invalidation handlers."""
    from AFO.cache.semantic_cache import get_semantic_cache

    engine = get_invalidation_engine()
    semantic_cache = get_semantic_cache()

    async def semantic_invalidation_handler(event: InvalidationEvent) -> int:
        """Handler to invalidate semantic cache entries."""
        if event.pattern:
            return await semantic_cache.invalidate(pattern=event.pattern)
        if event.query:
            return await semantic_cache.invalidate_by_similarity(event.query)
        return 0

    engine.register_handler(
        InvalidationTrigger.IRS_CHANGE,
        semantic_invalidation_handler,
    )
    engine.register_handler(
        InvalidationTrigger.DATA_UPDATE,
        semantic_invalidation_handler,
    )
    engine.register_handler(
        InvalidationTrigger.CASCADE,
        semantic_invalidation_handler,
    )

    logger.info("✅ Default invalidation handlers registered")
