import logging
from typing import Any

from AFO.evolution.dgm_engine import dgm_engine
from AFO.governance.kill_switch import sentry
from AFO.governance.narrative_sanitizer import sanitizer

logger = logging.getLogger(__name__)


class ExternalInterfaceService:
    """
    Service layer for external public interfaces.
    眞 (Truth): Decouples business logic from API routing.
    美 (Beauty): Provides a clean, sanitized interface for public consumption.
    """

    def get_public_chronicle(self) -> list[dict[str, Any]]:
        """Returns a sanitized, read-only summary of the kingdom's optimization history."""
        try:
            history = dgm_engine.chronicle.get_history()
            public_data = []
            for h in history:
                if h.decree_status == "APPROVED":
                    public_data.append(
                        {
                            "iteration": h.generation,
                            "summary": [sanitizer.sanitize(m) for m in h.modifications],
                            "reliability_index": h.trinity_score,
                            "timestamp": h.timestamp,
                        }
                    )
            return public_data
        except Exception as e:
            logger.error(f"Failed to fetch public chronicle: {e}")
            return []

    def get_public_status(self) -> dict[str, Any]:
        """Returns the high-level health of the civilization."""
        return {
            "status": "OPERATIONAL" if not sentry.is_locked() else "MAINTENANCE",
            "mode": "ADAPTIVE",
            "governance": "ACTIVE",
        }


external_service = ExternalInterfaceService()
