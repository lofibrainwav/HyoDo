from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

import asyncpg

from AFO.api.compat import get_settings_safe

# Trinity Score: 90.0 (Established by Chancellor)
# domain/audit/trail.py
"""
AFO Audit Trail - 永 (Eternity)
Immutable logging of Trinity decisions to PostgreSQL.

Stores:
- decision_id: UUID
- trinity_score: float
- risk_score: float
- action: Union[AUTO_RUN, ASK_COMMANDER]
- timestamp: datetime
- context: JSON metadata
"""


# Lazy import PostgreSQL driver
_db_connection = None


@dataclass
class AuditRecord:
    """A single Trinity decision audit record."""

    decision_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trinity_score: float = 0.0
    risk_score: float = 0.0
    action: str = "ASK_COMMANDER"  # Union[AUTO_RUN, ASK_COMMANDER]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            **asdict(self),
            "timestamp": self.timestamp.isoformat(),
        }


class AuditTrail:
    """
    永 (Eternity) Audit Trail

    Provides immutable persistent logging of all Trinity governance decisions
    to PostgreSQL for regulatory compliance and historical analysis.
    """

    TABLE_NAME = "trinity_audit_trail"

    def __init__(self, database_url: str | None = None) -> None:
        if database_url:
            self.database_url = database_url
        else:
            # Try to get from AFO settings, fallback to .env then hardcoded default

            settings = get_settings_safe()

            if settings:
                host = getattr(settings, "POSTGRES_HOST", "localhost")
                port = getattr(settings, "POSTGRES_PORT", 15432)
                db = getattr(settings, "POSTGRES_DB", "afo_memory")
                user = getattr(settings, "POSTGRES_USER", "afo")
                pw = getattr(settings, "POSTGRES_PASSWORD", "afo_secret_change_me")
                self.database_url = f"postgresql://{user}:{pw}@{host}:{port}/{db}"
            else:
                self.database_url = os.getenv(
                    "DATABASE_URL",
                    "postgresql://afo:afo_secret_change_me@localhost:15432/afo_memory",
                )
        self._connection = None
        self._records: list[AuditRecord] = []  # In-memory fallback

    async def _get_connection(self) -> Any | None:
        """
        Lazy connection to PostgreSQL.

        Returns:
            asyncpg connection object or None if connection failed
        """
        global _db_connection
        if _db_connection is None:
            try:
                _db_connection = await asyncpg.connect(self.database_url)
                await self._ensure_table()
            except ImportError:
                print("⚠️ [Audit] asyncpg not installed, using in-memory fallback")
            except Exception as e:
                print(f"⚠️ [Audit] DB connection failed: {e}, using in-memory")
        return _db_connection

    async def _ensure_table(self) -> None:
        """Create audit table if not exists."""
        conn = await self._get_connection()
        if conn:
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.TABLE_NAME} (
                    decision_id UUID PRIMARY KEY,
                    trinity_score REAL NOT NULL,
                    risk_score REAL NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    context JSONB,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """  # nosec B608
            )

    async def log(
        self,
        trinity_score: float,
        risk_score: float,
        action: str,
        context: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """
        Log a Trinity decision to the audit trail.

        Args:
            trinity_score: Current Trinity Score (0.0 - 1.0)
            risk_score: Current Risk Score (0.0 - 1.0)
            action: Decision made (Union[AUTO_RUN, ASK_COMMANDER])
            context: Optional metadata (query, strategist responses, etc.)

        Returns:
            The created AuditRecord
        """
        record = AuditRecord(
            trinity_score=trinity_score,
            risk_score=risk_score,
            action=action,
            context=context or {},
        )

        conn = await self._get_connection()
        if conn:
            try:
                await conn.execute(
                    f"INSERT INTO {self.TABLE_NAME} (decision_id, trinity_score, risk_score, action, timestamp, context) VALUES ($1, $2, $3, $4, $5, $6)",  # nosec B608
                    uuid.UUID(record.decision_id),
                    record.trinity_score,
                    record.risk_score,
                    record.action,
                    record.timestamp,
                    json.dumps(record.context),
                )
                print(f"📝 [Audit] Logged: {record.action} (Trinity: {trinity_score:.2f})")
            except Exception as e:
                print(f"⚠️ [Audit] DB write failed: {e}")
                self._records.append(record)  # Fallback to memory
        else:
            # In-memory fallback
            self._records.append(record)
            print(f"📝 [Audit] Logged (memory): {record.action}")

        return record

    async def get_recent(self, limit: int = 100) -> list[AuditRecord]:
        """Get recent audit records."""
        conn = await self._get_connection()
        if conn:
            rows = await conn.fetch(
                f"SELECT * FROM {self.TABLE_NAME} ORDER BY timestamp DESC LIMIT $1",  # nosec B608
                limit,
            )
            return [
                AuditRecord(
                    decision_id=str(row["decision_id"]),
                    trinity_score=row["trinity_score"],
                    risk_score=row["risk_score"],
                    action=row["action"],
                    timestamp=row["timestamp"],
                    context=row["context"] or {},
                )
                for row in rows
            ]
        return self._records[-limit:]

    async def get_statistics(self) -> dict[str, Any]:
        """Get audit trail statistics."""
        conn = await self._get_connection()
        if conn:
            stats = await conn.fetchrow(
                f"SELECT COUNT(*) as total_decisions, AVG(trinity_score) as avg_trinity, AVG(risk_score) as avg_risk, SUM(CASE WHEN action = 'AUTO_RUN' THEN 1 ELSE 0 END) as auto_run_count, SUM(CASE WHEN action = 'ASK_COMMANDER' THEN 1 ELSE 0 END) as ask_count FROM {self.TABLE_NAME}"  # nosec B608
            )
            return dict(stats) if stats else {}

        # In-memory fallback
        total = len(self._records)
        auto_run = sum(1 for r in self._records if r.action == "AUTO_RUN")
        return {
            "total_decisions": total,
            "avg_trinity": sum(r.trinity_score for r in self._records) / max(1, total),
            "avg_risk": sum(r.risk_score for r in self._records) / max(1, total),
            "auto_run_count": auto_run,
            "ask_count": total - auto_run,
        }


# Singleton for easy access
audit_trail = AuditTrail()


async def log_decision(
    trinity_score: float,
    risk_score: float,
    action: str,
    context: dict[str, Any] | None = None,
) -> AuditRecord:
    """Convenience function for logging decisions."""
    return await audit_trail.log(trinity_score, risk_score, action, context)
