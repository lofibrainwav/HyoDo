# Trinity Score: 90.0 (Established by Chancellor)
"""Yeongdeok Complete - AFO Kingdom Memory System (Phase 2.5)
Named after 영덕 (Yeongdeok), the Kingdom's archivist sage.
Provides comprehensive memory management and context persistence.
"""

import contextlib
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry."""

    key: str
    content: Any
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: list[str] = field(default_factory=list)
    importance: float = 1.0
    access_count: int = 0


class YeongdeokComplete:
    """The Complete Memory System (영덕 완성)

    A unified memory management system for the AFO Kingdom that handles:
    - Short-term conversation memory
    - Long-term knowledge persistence
    - Context retrieval and relevance scoring
    - Memory consolidation and archival
    """

    def __init__(self, max_short_term: int = 100, max_long_term: int = 1000, **kwargs: Any) -> None:
        self.short_term: dict[str, MemoryEntry] = {}
        self.long_term: dict[str, MemoryEntry] = {}
        self.max_short_term = max_short_term
        self.max_long_term = max_long_term
        self.conversation_buffer: list[dict[str, str]] = []
        self.browser: Any | None = None

    def _generate_key(self, content: str) -> str:
        """Generate a unique key for content."""
        try:
            return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()[:16]
        except Exception:
            return str(hash(content))[:16]

    def remember(self, content: Any, tags: list[str] | None = None, importance: float = 1.0) -> str:
        """Store a memory in short-term storage."""
        try:
            content_str = json.dumps(content) if not isinstance(content, str) else content
            key = self._generate_key(content_str)

            entry = MemoryEntry(key=key, content=content, tags=tags or [], importance=importance)

            self.short_term[key] = entry

            # Consolidate if needed
            if len(self.short_term) > self.max_short_term:
                self._consolidate()

            return key
        except Exception:
            return "error_key"

    def recall(self, key: str) -> Any | None:
        """Recall a memory by key."""
        try:
            # Check short-term first
            if key in self.short_term:
                entry = self.short_term[key]
                entry.access_count += 1
                return entry.content

            # Then long-term
            if key in self.long_term:
                entry = self.long_term[key]
                entry.access_count += 1
                return entry.content
        except Exception:
            pass
        return None

    def search(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search memories by content."""
        try:
            results = []
            query_lower = query.lower()

            # Search both stores
            all_entries = list(self.short_term.values()) + list(self.long_term.values())

            for entry in all_entries:
                content_str = str(entry.content).lower()
                if query_lower in content_str:
                    score = content_str.count(query_lower) * entry.importance
                    results.append(
                        {
                            "key": entry.key,
                            "content": entry.content,
                            "score": score,
                            "tags": entry.tags,
                        }
                    )

            # Sort by score
            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:limit]
        except Exception:
            return []

    def search_by_tags(self, tags: list[str], limit: int = 10) -> list[dict[str, Any]]:
        """Search memories by tags."""
        try:
            results = []
            all_entries = list(self.short_term.values()) + list(self.long_term.values())

            for entry in all_entries:
                matching_tags = set(entry.tags) & set(tags)
                if matching_tags:
                    results.append(
                        {
                            "key": entry.key,
                            "content": entry.content,
                            "matching_tags": list(matching_tags),
                            "importance": entry.importance,
                        }
                    )

            results.sort(key=lambda x: len(x["matching_tags"]), reverse=True)
            return results[:limit]
        except Exception:
            return []

    def add_conversation(self, role: str, content: str) -> None:
        """Add a conversation turn to buffer."""
        try:
            self.conversation_buffer.append(
                {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            # Keep buffer manageable
            if len(self.conversation_buffer) > self.max_short_term:
                self.conversation_buffer = self.conversation_buffer[-self.max_short_term :]
        except Exception:
            pass

    def get_conversation_context(self, last_n: int = 10) -> list[dict[str, str]]:
        """Get recent conversation context."""
        try:
            return self.conversation_buffer[-last_n:]
        except Exception:
            return []

    def _consolidate(self) -> None:
        """Consolidate short-term to long-term memory."""
        try:
            # Move high-importance or frequently accessed items to long-term
            to_move = []
            for key, entry in self.short_term.items():
                if entry.importance > 0.7 or entry.access_count > 3:
                    to_move.append(key)

            for key in to_move:
                self.long_term[key] = self.short_term.pop(key)

            # Prune if needed
            if len(self.long_term) > self.max_long_term:
                # Remove lowest importance entries
                sorted_entries = sorted(
                    self.long_term.items(),
                    key=lambda x: x[1].importance * x[1].access_count,
                )
                for key, _ in sorted_entries[: len(self.long_term) - self.max_long_term]:
                    del self.long_term[key]
        except Exception:
            pass

    def forget(self, key: str) -> bool:
        """Remove a specific memory."""
        try:
            if key in self.short_term:
                del self.short_term[key]
                return True
            if key in self.long_term:
                del self.long_term[key]
                return True
        except Exception:
            pass
        return False

    def clear_short_term(self) -> None:
        """Clear all short-term memory."""
        with contextlib.suppress(Exception):
            self.short_term = {}

    def get_stats(self) -> dict[str, Any]:
        """Get memory system statistics."""
        try:
            return {
                "short_term_count": len(self.short_term),
                "long_term_count": len(self.long_term),
                "conversation_buffer_size": len(self.conversation_buffer),
                "max_short_term": self.max_short_term,
                "max_long_term": self.max_long_term,
            }
        except Exception:
            return {"error": "failed to get stats"}

    def export(self) -> dict[str, Any]:
        """Export all memories for backup."""
        try:
            return {
                "short_term": {k: v.__dict__ for k, v in self.short_term.items()},
                "long_term": {k: v.__dict__ for k, v in self.long_term.items()},
                "conversation_buffer": self.conversation_buffer,
                "exported_at": datetime.now().isoformat(),
            }
        except Exception:
            return {"error": "export failed"}

    async def close_eyes(self) -> None:
        """Graceful shutdown of the memory system.

        Trinity Score: 孝 (Serenity) - 마찰 없는 클린업
        """
        try:
            # Clear short-term memory for clean shutdown
            self.clear_short_term()

            # Close any open connections (future expansion)
            if hasattr(self, "_redis_client") and self._redis_client:
                with contextlib.suppress(Exception):
                    await self._redis_client.close()

            logger.info("✅ Yeongdeok memory system closed gracefully")
        except Exception as e:
            logger.warning(f"Yeongdeok close_eyes failed: {e}")
            # Don't raise exception during shutdown


# Default instance
yeongdeok = YeongdeokComplete()


def get_memory_system() -> YeongdeokComplete:
    """Get the default Yeongdeok memory system."""
    try:
        return yeongdeok
    except Exception:
        return YeongdeokComplete()
