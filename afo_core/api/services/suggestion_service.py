from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from AFO.utils.redis_connection import get_shared_async_redis_client

"""Suggestion Service - AFO Kingdom Agentic Evolution.

Enables agents to push proactive suggestions to the dashboard via Redis Pub/Sub.
"""


logger = logging.getLogger(__name__)


async def publish_proactive_suggestion(
    source: str,
    message: str,
    priority: str = "medium",
    action_url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """Publish a proactive suggestion to the Chancellor Stream.

    Args:
        source: Name of the agent (e.g., 'Zilong', 'Lushun')
        message: The proactive advice or suggestion
        priority: 'high', 'medium', 'low'
        action_url: Optional link for the user to act on
        metadata: Optional additional context

    Returns:
        True if published successfully, False otherwise.
    """
    try:
        redis = await get_shared_async_redis_client()

        payload = {
            "source": source,
            "message": message,
            "type": "suggestion",
            "priority": priority,
            "action_url": action_url,
            "metadata": metadata or {},
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        }

        # Publish to the channel used by streams_router
        await redis.publish("chancellor_thought_stream", json.dumps(payload))
        logger.info(f"✅ Proactive suggestion published from {source}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to publish proactive suggestion: {e}")
        return False
