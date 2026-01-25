# Trinity Score: 90.0 (Established by Chancellor)
# packages/afo-core/utils/history.py
# (Historian - 영(永) 기록 보관소)
# 🧭 Trinity Score: 眞95% 善99% 美90% 孝95%

import json
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class Historian:
    """Historian (영(永)): The Keeper of Records.
    Ensures that every decision and action of the Royal Council is recorded for posterity.
    """

    @staticmethod
    async def record(
        query: str,
        trinity_score: float,
        status: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Records a major event/decision to the Chronicles."""
        if metadata is None:
            metadata = {}

        record_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "trinity_score": trinity_score,
            "status": status,
            "metadata": metadata,
            "philosophy": "Eternity (永)",
        }

        # 1. Log to System Log (Immediate Truth)
        logger.info(
            f"📜 [Historian] Chronicle Entry: {json.dumps(record_entry, ensure_ascii=False)}"
        )

        # 2. Persist to PostgreSQL via AuditTrail (Liver/Eternity)
        try:
            from AFO.domain.audit.trail import AuditTrail

            audit = AuditTrail()
            # Risk score is inverted goodness, if not in metadata, we estimate from trinity
            risk_score = metadata.get("risk_score", (100.0 - trinity_score) / 100.0)

            await audit.log(
                trinity_score=(trinity_score / 100.0 if trinity_score > 1.0 else trinity_score),
                risk_score=risk_score,
                action=status,
                context={**metadata, "query": query},
            )
        except Exception as e:
            logger.error(f"⚠️ [Historian] AuditTrail persistence failed: {e}")

        return record_entry

    @staticmethod
    def log_chronicle(content: str) -> None:
        """Logs a free-form chronicle entry.

        Args:
            content: Chronicle content to log

        """
        logger.info(f"📜 [Historian] {content}")

    @staticmethod
    def log_preference(
        query: str, rejected: str, chosen: str, critique: str = ""
    ) -> dict[str, Any]:
        """[RLAIF] Records 'Chosen' vs 'Rejected' responses based on 헌법(Constitution).
        Used for future model alignment and moral fine-tuning.
        """
        preference_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "rejected": rejected,
            "chosen": chosen,
            "critique": critique,
            "type": "RLAIF_PREFERENCE",
        }
        logger.info(
            f"⚖️ [Historian] RLAIF Preference Entry: {json.dumps(preference_entry, ensure_ascii=False)}"
        )
        return preference_entry


historian = Historian()
