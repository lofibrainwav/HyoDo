"""
AFO Health Monitor
System health monitoring service for Council of Minds.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import psutil
except ImportError:
    psutil = None


class HealthMonitor:
    """Core Health Monitor Service"""

    async def get_comprehensive_health(self) -> dict[str, Any]:
        """Collects all health metrics (Real-Time)."""
        from AFO.api.routes.integrity_check import IntegrityCheckRequest, check_integrity

        friction = self._get_friction_metrics()
        integrity = await check_integrity(IntegrityCheckRequest())

        # Calculate Serenity Score based on Friction
        # Base 100 - (Friction * 50)
        serenity_score = 100.0 - (friction["friction_score"] * 50.0)

        return {
            "system": self._get_system_metrics(),
            "friction": friction,
            "trinity": {
                "score": integrity["total_score"],
                "serenity_real": serenity_score,
                "pillars": integrity["pillars"],
            },
            "status": "healthy"
            if (friction["friction_score"] < 0.5 and integrity["total_score"] > 80)
            else "degraded",
        }

    def _get_system_metrics(self) -> dict[str, Any]:
        if not psutil:
            return {"cpu_percent": 0.0, "memory_percent": 0.0, "error": "psutil not installed"}

        return {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }

    def _get_friction_metrics(self) -> dict[str, Any]:
        """Analyzes log files for recent errors (Friction)."""
        from AFO.health.friction import get_friction_metrics

        return get_friction_metrics()
