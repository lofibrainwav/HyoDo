"""11臟六腑 Organ Health Metrics Module.

Maps the 11 organs of traditional medicine to infrastructure components
and tracks their health metrics.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..prometheus import (
    record_organ_error,
    update_organ_health,
    update_organ_response_time,
)

logger = logging.getLogger(__name__)


class OrganType(Enum):
    """11臟六腑 organ types."""

    HEART = ("心", "Redis", "Session/cache/pub-sub")
    LIVER = ("肝", "PostgreSQL", "Persistent storage")
    BRAIN = ("腦", "Soul Engine", "Main API")
    TONGUE = ("舌", "Ollama", "Local LLM inference")
    LUNGS = ("肺", "LanceDB", "Vector embeddings")
    EYES = ("眼", "Dashboard", "Next.js UI")
    KIDNEYS = ("腎", "MCP", "External tool connections")
    SPLEEN = ("脾", "Task Queue", "Background jobs")
    STOMACH = ("胃", "Object Storage", "File storage")
    INTESTINES = ("腸", "Message Bus", "Event streaming")
    GALLBLADDER = ("膽", "Auth Service", "Authentication")

    def __init__(self, hanja: str, service: str, description: str) -> None:
        self.hanja = hanja
        self.service = service
        self.description = description


@dataclass
class OrganHealth:
    """Organ health status."""

    organ: OrganType
    health_score: float
    response_time_ms: float
    last_check: str
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "organ": self.organ.hanja,
            "service": self.organ.service,
            "health_score": self.health_score,
            "response_time_ms": self.response_time_ms,
            "last_check": self.last_check,
            "status": self.status,
        }


class OrganMetricsCollector:
    """Collects and records 11臟六腑 organ health metrics."""

    def __init__(self) -> None:
        self._health_cache: dict[str, OrganHealth] = {}
        logger.info("OrganMetricsCollector initialized")

    def record_organ_health(
        self,
        organ: OrganType,
        health_score: float,
        response_time_ms: float,
    ) -> None:
        """Record organ health metrics.

        Args:
            organ: The organ type
            health_score: Health score 0-100
            response_time_ms: Response time in milliseconds
        """
        from datetime import datetime

        update_organ_health(organ.hanja, health_score)
        update_organ_response_time(organ.hanja, response_time_ms)

        health = OrganHealth(
            organ=organ,
            health_score=health_score,
            response_time_ms=response_time_ms,
            last_check=datetime.now().isoformat(),
            status="healthy"
            if health_score >= 80
            else "degraded"
            if health_score >= 50
            else "critical",
        )

        self._health_cache[organ.hanja] = health
        logger.debug(f"Organ health: {organ.hanja}={health_score:.1f}")

    def record_organ_error(
        self,
        organ: OrganType,
        error_type: str,
    ) -> None:
        """Record an organ error.

        Args:
            organ: The organ type
            error_type: Type of error
        """
        record_organ_error(organ.hanja, error_type)
        logger.warning(f"Organ error: {organ.hanja} - {error_type}")

    def get_organ_health(self, organ: OrganType) -> OrganHealth | None:
        """Get cached health for an organ."""
        return self._health_cache.get(organ.hanja)

    def get_all_organ_health(self) -> dict[str, OrganHealth]:
        """Get all cached organ health data."""
        return self._health_cache.copy()

    def check_all_organs(self) -> dict[str, Any]:
        """Check all organs and return summary."""
        healthy = sum(1 for h in self._health_cache.values() if h.health_score >= 80)
        degraded = sum(1 for h in self._health_cache.values() if 50 <= h.health_score < 80)
        critical = sum(1 for h in self._health_cache.values() if h.health_score < 50)

        return {
            "total": len(self._health_cache),
            "healthy": healthy,
            "degraded": degraded,
            "critical": critical,
            "organs": {k: v.to_dict() for k, v in self._health_cache.items()},
        }


__all__ = [
    "OrganType",
    "OrganHealth",
    "OrganMetricsCollector",
]
