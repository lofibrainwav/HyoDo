# Trinity Score: 91.0 (Established by Chancellor)
"""LangGraph AsyncPostgresSaver Integration (2026 Best Practices)
Async-native PostgreSQL checkpointer for LangGraph persistence.

2026 Best Practices Implementation:
- AsyncPostgresSaver for non-blocking database operations
- Pipeline mode for minimized roundtrips
- Per-channel versioned checkpoint storage
- Production-ready with pause/resume, time-travel support

Philosophy:
- 眞 (Truth): Durable state persistence with SSOT
- 善 (Goodness): Fault-tolerant with automatic recovery
- 美 (Beauty): Minimal latency, async by design
"""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

logger = logging.getLogger(__name__)

# Database configuration from environment
POSTGRES_URI = os.getenv(
    "AFO_POSTGRES_URI", "postgresql://postgres:postgres@localhost:15432/afo_kingdom"
)


class LangGraphCheckpointer:
    """LangGraph AsyncPostgresSaver wrapper for AFO Kingdom.

    Provides:
    1. Async PostgreSQL checkpoint storage
    2. Thread/conversation memory persistence
    3. Time-travel debugging support
    4. Automatic table setup
    """

    def __init__(self, connection_string: str | None = None) -> None:
        self.connection_string = connection_string or POSTGRES_URI
        self._saver = None
        self._pool = None
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the PostgreSQL checkpointer.

        Returns:
            True if initialization succeeded
        """
        try:
            import psycopg_pool
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            # Create async connection pool
            self._pool = psycopg_pool.AsyncConnectionPool(
                conninfo=self.connection_string,
                min_size=2,
                max_size=10,
                open=False,
            )
            await self._pool.open()

            # Create saver with pool
            self._saver = AsyncPostgresSaver(self._pool)

            # Setup tables (creates checkpoint tables if not exist)
            await self._saver.setup()

            self._initialized = True
            logger.info("✅ LangGraph AsyncPostgresSaver initialized")
            return True

        except ImportError as e:
            logger.warning(f"⚠️ LangGraph checkpoint dependencies not available: {e}")
            logger.info("Install with: uv add langgraph-checkpoint-postgres psycopg[binary]")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to initialize AsyncPostgresSaver: {e}")
            return False

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._initialized = False
            logger.info("PostgreSQL checkpointer closed")

    @property
    def saver(self) -> Any:
        """Get the AsyncPostgresSaver instance for use with LangGraph.

        Returns:
            The configured AsyncPostgresSaver or None if not initialized
        """
        if not self._initialized:
            logger.warning("Checkpointer not initialized. Call initialize() first.")
            return None
        return self._saver

    def is_available(self) -> bool:
        """Check if checkpointer is available and initialized."""
        return self._initialized and self._saver is not None


# Singleton instance
_checkpointer: LangGraphCheckpointer | None = None


def get_checkpointer() -> LangGraphCheckpointer:
    """Get singleton LangGraph checkpointer instance."""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = LangGraphCheckpointer()
    return _checkpointer


@asynccontextmanager
async def get_async_checkpointer() -> AsyncGenerator[Any, None]:
    """Context manager for async checkpointer usage.

    Usage:
        async with get_async_checkpointer() as saver:
            graph = create_graph()
            compiled = graph.compile(checkpointer=saver)
    """
    checkpointer = get_checkpointer()

    if not checkpointer.is_available():
        await checkpointer.initialize()

    try:
        yield checkpointer.saver
    finally:
        # Pool remains open for reuse
        pass


async def create_graph_with_persistence(graph_builder: Any, thread_id: str | None = None) -> Any:
    """Create a compiled LangGraph with PostgreSQL persistence.

    Args:
        graph_builder: LangGraph StateGraph builder
        thread_id: Optional thread ID for conversation

    Returns:
        Compiled graph with checkpointer configured
    """
    checkpointer = get_checkpointer()

    if not checkpointer.is_available():
        success = await checkpointer.initialize()
        if not success:
            logger.warning("PostgreSQL checkpointer unavailable, using in-memory")
            return graph_builder.compile()

    compiled = graph_builder.compile(checkpointer=checkpointer.saver)

    if thread_id:
        logger.info(f"Graph compiled with persistence, thread_id: {thread_id}")

    return compiled


# Example usage for integration with existing graphs
async def example_chancellor_graph_with_persistence():
    """Example: Chancellor graph with PostgreSQL persistence."""
    try:
        from AFO.chancellor_graph import create_chancellor_graph

        graph_builder = create_chancellor_graph()

        async with get_async_checkpointer() as saver:
            if saver:
                compiled = graph_builder.compile(checkpointer=saver)
                logger.info("Chancellor graph compiled with PostgreSQL persistence")
                return compiled
            else:
                logger.warning("Using in-memory checkpointer")
                return graph_builder.compile()

    except ImportError:
        logger.warning("Chancellor graph not available")
        return None
