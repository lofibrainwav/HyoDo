# Trinity Score: 90.0 (Established by Chancellor)
"""
Streams Router (孝 - Serenity)
------------------------------
Server-Sent Events (SSE) router for real-time dashboard updates.
Reduces friction by providing visible system thought processes.
"""

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/mcp/thoughts")
async def stream_thoughts(request: Request) -> EventSourceResponse:
    """
    Stream real-time thoughts from the Chancellor (Matrix Style).
    Connection stays open to push updates instantly.
    """

    from AFO.utils.redis_connection import get_shared_async_redis_client

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        # Initial greeting
        yield {
            "event": "message",
            "data": json.dumps(
                {
                    "source": "System",
                    "message": "Neural Link Established... Waiting for Chancellor.",
                    "type": "info",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }
            ),
        }

        try:
            redis = await get_shared_async_redis_client()
            pubsub = redis.pubsub()
            await pubsub.subscribe("chancellor_thought_stream")

            async for message in pubsub.listen():
                # 클라이언트 연결 확인 (眞: 안정성)
                if await request.is_disconnected():
                    break

                if message["type"] == "message":
                    payload = message["data"]
                    yield {"event": "message", "data": payload}

                # 정기적인 하트비트 신호 (TICKET-049)
                # Redis 수신 대기 중에도 주기적인 핑을 보내 연결 유지를 보장함
                # NOTE: pubsub.get_message()와 asyncio.sleep()을 조합하는 방식이 더 안정적임

        except Exception as e:
            logger.error(f"Thought Stream Error: {e}")
            yield {
                "event": "message",
                "data": json.dumps(
                    {
                        "source": "System",
                        "message": f"Stream Error: {e}",
                        "type": "error",
                        "timestamp": datetime.now().strftime("%H:%M:%S"),
                        "retry": 5000,
                    }
                ),
            }
            if "pubsub" in locals():
                await pubsub.unsubscribe("chancellor_thought_stream")

    # TICKET-049: sse-starlette의 keep_alive 설정을 활성화하여 전역적인 하트비트 보장
    return EventSourceResponse(event_generator(), send_timeout=30, ping=3)
