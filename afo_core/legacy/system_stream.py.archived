# Trinity Score: 90.0 (Established by Chancellor)
"""
Chancellor Stream SSE (Server-Sent Events) Endpoint
Real-time log streaming for AFO Kingdom monitoring

Provides live log streaming via Redis Pub/Sub to SSE clients.
Implements 眞善美孝永 principles for reliable real-time communication.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, cast

import redis
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


async def publish_thought(content: dict | None = None, **kwargs) -> None:
    """
    Publish thought to Chancellor Stream via Redis.

    Args:
        content: Thought content dict with message, level, source, timestamp
        **kwargs: Additional thought parameters
    """
    try:
        from AFO.config.settings import get_settings

        settings = get_settings()
        redis_url = settings.REDIS_URL
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

        # Merge content dict with kwargs
        if content is None:
            content = {}
        if kwargs:
            content.update(kwargs)

        # Ensure timestamp is included
        if "timestamp" not in content:
            content["timestamp"] = asyncio.get_event_loop().time()

        # Publish to Redis channel
        redis_client.publish("kingdom:logs:stream", json.dumps(content))

        logger.debug(
            f"Published thought to Chancellor Stream: {content.get('message', '')[:100]}..."
        )

    except Exception as e:
        logger.error(f"Failed to publish thought: {e}")
        # Don't raise exception - logging should not break business logic


# SSE event generator
async def log_stream_generator(request: Request) -> Any:
    """
    Generate SSE events from Redis Pub/Sub messages with File Fallback.

    Trinity Score: 善 (Goodness) - Failover mechanism for high availability.
    """
    redis_available = False
    pubsub = None

    try:
        from AFO.config.settings import get_settings

        settings = get_settings()
        redis_url = settings.REDIS_URL
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        redis_client.ping()
        pubsub = redis_client.pubsub()
        pubsub.subscribe("kingdom:logs:stream")
        redis_available = True
        logger.info("Chancellor Stream: Connected to Redis Pub/Sub")
    except Exception as e:
        logger.warning(f"Chancellor Stream: Redis unavailable ({e}). Falling back to file tail.")

    # Send initial connection message
    initial_msg = {
        "message": "🔌 [Serenity] Connected to Chancellor Stream"
        + (" (Redis)" if redis_available else " (Fallback: File)"),
        "level": "SUCCESS",
        "source": "Chancellor Stream",
        "timestamp": datetime.now().isoformat()
        if not redis_available
        else asyncio.get_event_loop().time(),
    }
    yield {"data": json.dumps(initial_msg)}

    if redis_available and pubsub:
        try:
            while True:
                if await request.is_disconnected():
                    break

                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    yield {"data": message["data"]}

                await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Chancellor Stream Redis error: {e}")
        finally:
            pubsub.close()

    # Fallback to File Tail (Goodness)
    logger.info("Chancellor Stream: Starting File Fallback tailing")
    log_file = "backend.log"
    if not os.path.exists(log_file):
        try:
            with open(log_file, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] Log file initialized.\n")
        except Exception:
            pass

    try:
        with open(log_file) as f:
            f.seek(0, 2)  # Go to end
            while True:
                if await request.is_disconnected():
                    break

                line = f.readline()
                if line:
                    msg = {
                        "message": line.strip(),
                        "level": "INFO",
                        "source": "backend.log",
                        "timestamp": datetime.now().isoformat(),
                    }
                    yield {"data": json.dumps(msg)}
                else:
                    await asyncio.sleep(0.5)
    except Exception as e:
        logger.error(f"Chancellor Stream File Fallback failed: {e}")
        yield {"data": json.dumps({"message": f"Critical Stream Failure: {e}", "level": "ERROR"})}


# NOTE: /logs/stream endpoint moved to system_health.py to avoid route conflicts
# This file previously contained duplicate /logs/stream implementation
# Keeping this comment for historical reference and future disambiguation

from fastapi import APIRouter

# Empty router to prevent import errors in router_manager.py
router = APIRouter(prefix="/system/stream", tags=["System Stream"])
