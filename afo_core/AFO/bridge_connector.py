"""
NotebookLM Bridge Connector (REST Edition)
------------------------------------------
Connects the AFO Core (Python Brain) to the NotebookLM Bridge (Vercel Edge).
Uses Upstash REST API via HTTP for maximum firewall compatibility.
"""

import json
import logging
import os
from datetime import datetime

import requests

logger = logging.getLogger(__name__)


class NotebookBridgeConnector:
    """Connector to the shared Upstash Redis via REST API"""

    def __init__(self) -> None:
        # Load credentials (expecting REST variables)
        self.url = os.getenv("UPSTASH_REDIS_REST_URL") or os.getenv("KV_REST_API_URL")
        self.token = os.getenv("UPSTASH_REDIS_REST_TOKEN") or os.getenv("KV_REST_API_TOKEN")
        self.enabled = False

        if self.url and self.token:
            self.enabled = True
            logger.info("NotebookBridgeConnector: Configured with REST API")
        else:
            logger.warning("NotebookBridgeConnector: Missing REST env vars. Bridge disabled.")

    def _post(self, command: list) -> None:
        """Execute a Redis command via REST API"""
        if not self.enabled:
            return None

        try:
            # Upstash REST format: POST / { command: [...] } or /cmd/key/arg
            # We'll use the pipeline endpoint or simple command endpoint
            response = requests.post(
                f"{self.url}/pipeline",
                headers={"Authorization": f"Bearer {self.token}"},
                json=[command],
                timeout=30,  # SSOT: Prevent hanging requests
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NotebookBridgeConnector: Request failed - {e}")
            return None

    def update_kingdom_status(
        self,
        trinity_score: float,
        active_agents: int,
        health: str = "Optimal",
        pillars: dict[str, float] | None = None,
    ):
        """Push current Kingdom Status to the Edge"""
        if not self.enabled:
            return

        # Default pillars if not provided (mirrors score)
        if not pillars:
            pillars = {
                "truth": trinity_score,
                "goodness": trinity_score,
                "beauty": trinity_score,
                "serenity": trinity_score,
                "infinity": trinity_score,
            }

        status_payload = {
            "trinityScore": trinity_score,
            "pillars": pillars,
            "activeAgents": active_agents,
            "systemHealth": health,
            "lastUpdated": datetime.now().isoformat(),
        }

        # Redis SET command: ["SET", key, value]
        self._post(["SET", "kingdom:status", json.dumps(status_payload)])
        logger.info("NotebookBridgeConnector: Kingdom Status updated")

    def push_irs_update(self, change_id: str, summary: str, impact_level: str) -> None:
        """Push a new IRS regulation update to the Edge"""
        if not self.enabled:
            return

        update_payload = {
            "changeId": change_id,
            "changeType": "NEW_REGULATION",
            "impactLevel": impact_level,
            "summary": summary,
            "effectiveDate": datetime.now().isoformat(),
        }

        # Redis LPUSH + LTRIM
        # Since _post logic above is simple 1-command, let's do two calls or update _post to handle pipelines
        # For simplicity, sending pipeline request manually here
        try:
            requests.post(
                f"{self.url}/pipeline",
                headers={"Authorization": f"Bearer {self.token}"},
                json=[
                    ["LPUSH", "irs:changes", json.dumps(update_payload)],
                    ["LTRIM", "irs:changes", 0, 49],
                ],
                timeout=30,  # SSOT: Prevent hanging requests
            )
            logger.info(f"NotebookBridgeConnector: Pushed IRS update {change_id}")
        except Exception as e:
            logger.error(f"NotebookBridgeConnector: IRS update failed - {e}")


# Global instance
bridge = NotebookBridgeConnector()
