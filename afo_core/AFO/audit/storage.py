# Trinity Score: 95.0 (Phase 33 Audit Module Refactoring)
"""Audit Storage Backends"""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .models import AuditEvent, AuditQuery, AuditStats

logger = logging.getLogger(__name__)


# ============================================================================
# Storage Abstract Base Class (永 - Persistence)
# ============================================================================


class AuditStorage(ABC):
    """Abstract base class for audit storage backends (永 - Persistence)"""

    @abstractmethod
    async def store(self, event: AuditEvent) -> bool:
        """Store an audit event"""
        pass

    @abstractmethod
    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events"""
        pass

    @abstractmethod
    async def get_stats(self, hours: int = 24) -> AuditStats:
        """Get audit statistics"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close storage connection"""
        pass


# ============================================================================
# File-Based Storage Implementation (孝 - Reliable)
# ============================================================================


class FileAuditStorage(AuditStorage):
    """JSONL file-based audit storage with rotation (孝 - Reliable)

    Features:
    - JSONL format for easy parsing and streaming
    - Automatic log rotation based on size
    - Thread-safe write operations
    - Efficient querying with streaming reads
    """

    def __init__(
        self,
        log_dir: Path | None = None,
        max_file_size_mb: int = 10,
        max_backup_files: int = 5,
    ):
        if log_dir is None:
            log_dir = Path.home() / ".afo" / "audit"

        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "audit_trail.jsonl"
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_backup_files = max_backup_files
        self._write_lock = asyncio.Lock()

        logger.info(f"FileAuditStorage initialized at {self.log_file}")

    async def store(self, event: AuditEvent) -> bool:
        """Store an audit event to JSONL file"""
        async with self._write_lock:
            try:
                await self._rotate_if_needed()

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(event.to_json() + "\n")

                return True
            except Exception as e:
                logger.error(f"Failed to store audit event: {e}")
                return False

    async def query(self, query: AuditQuery) -> list[AuditEvent]:
        """Query audit events from file"""
        events: list[AuditEvent] = []
        skipped = 0

        try:
            if not self.log_file.exists():
                return events

            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        event = AuditEvent.from_dict(data)

                        if self._matches_query(event, query):
                            if skipped < query.offset:
                                skipped += 1
                                continue

                            events.append(event)

                            if len(events) >= query.limit:
                                break
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Skipping malformed audit log entry: {e}")
                        continue

        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")

        return events

    async def get_stats(self, hours: int = 24) -> AuditStats:
        """Get audit statistics for the specified time period"""
        stats = AuditStats(time_range_hours=hours)
        cutoff = datetime.now(UTC) - timedelta(hours=hours)
        unique_users: set[str] = set()
        unique_resources: set[str] = set()
        success_count = 0

        try:
            if not self.log_file.exists():
                return stats

            with open(self.log_file, encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        data = json.loads(line)
                        timestamp_str = data.get("timestamp", "")
                        if timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                            if timestamp < cutoff:
                                continue

                        stats.total_events += 1

                        # Count by type
                        event_type = data.get("event_type", "unknown")
                        stats.events_by_type[event_type] = (
                            stats.events_by_type.get(event_type, 0) + 1
                        )

                        # Count by severity
                        severity = data.get("severity", "info")
                        stats.events_by_severity[severity] = (
                            stats.events_by_severity.get(severity, 0) + 1
                        )

                        # Track unique users
                        user_id = data.get("user_id")
                        if user_id:
                            unique_users.add(user_id)

                        # Track unique resources
                        resource = data.get("resource")
                        if resource:
                            unique_resources.add(resource)

                        # Track success rate
                        if data.get("success", True):
                            success_count += 1

                    except (json.JSONDecodeError, ValueError):
                        continue

            stats.unique_users = len(unique_users)
            stats.unique_resources = len(unique_resources)
            stats.success_rate = (
                (success_count / stats.total_events * 100) if stats.total_events > 0 else 0.0
            )

        except Exception as e:
            logger.error(f"Failed to calculate audit stats: {e}")

        return stats

    async def close(self) -> None:
        """Close storage (no-op for file storage)"""
        pass

    async def _rotate_if_needed(self) -> None:
        """Rotate log file if it exceeds max size"""
        try:
            if not self.log_file.exists():
                return

            if self.log_file.stat().st_size < self.max_file_size:
                return

            # Create backup filename with timestamp
            backup_time = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
            backup_file = self.log_dir / f"audit_trail.{backup_time}.jsonl"

            # Rotate
            self.log_file.rename(backup_file)
            logger.info(f"Rotated audit log to {backup_file}")

            # Clean up old backups
            backups = sorted(self.log_dir.glob("audit_trail.*.jsonl"), reverse=True)
            for old_backup in backups[self.max_backup_files :]:
                old_backup.unlink()
                logger.info(f"Removed old audit backup: {old_backup}")

        except Exception as e:
            logger.error(f"Failed to rotate audit log: {e}")

    def _matches_query(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check if an event matches the query criteria"""
        if not self._matches_basic_filters(event, query):
            return False

        return self._matches_time_range(event, query)

    def _matches_basic_filters(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check basic equal/in filters"""
        if query.event_types and event.event_type not in query.event_types:
            return False

        if query.severities and event.severity not in query.severities:
            return False

        if query.user_id and event.user_id != query.user_id:
            return False

        if query.trace_id and event.trace_id != query.trace_id:
            return False

        if query.resource and query.resource not in (event.resource or ""):
            return False

        return not (query.success is not None and event.success != query.success)

    def _matches_time_range(self, event: AuditEvent, query: AuditQuery) -> bool:
        """Check time range filters"""
        if query.start_time and event.timestamp < query.start_time:
            return False

        return not (query.end_time and event.timestamp > query.end_time)
