# Trinity Score: 90.0 (Established by Chancellor)
import asyncio
import json
import logging
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from AFO.utils.standard_shield import shield

router = APIRouter()
logger = logging.getLogger(__name__)

# AFO_SSE_HEARTBEAT: keep SSE connection alive even when upstream is silent
_SSE_HEARTBEAT_PAYLOAD = "event: heartbeat\ndata: ping\n\n"


async def with_heartbeat(source: AsyncIterator[Any], interval_s: float = 5.0) -> AsyncIterator[Any]:
    while True:
        try:
            chunk = await asyncio.wait_for(source.__anext__(), timeout=interval_s)
            yield chunk
        except TimeoutError:
            yield _SSE_HEARTBEAT_PAYLOAD
        except StopAsyncIteration:
            return


# Simple in-memory event bus for now (Redis Pub/Sub in production)
_thought_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()


async def broadcast_thought(thought_data: dict[str, Any]) -> None:
    """Internal helper to push thoughts to the stream"""
    await _thought_queue.put(thought_data)


@shield(pillar="善")
@router.get("/sse")
async def stream_thoughts(request: Request) -> Any:
    """[The Matrix Stream]
    Streams real-time thoughts from Chancellor, Antigravity, and Trinity.
    Clients (AFOPantheon) connect here to visualize the "Soul of the Machine".
    """

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        while True:
            # Check for client disconnect
            if await request.is_disconnected():
                break

            # Wait for next thought (with timeout to send keep-alive)
            try:
                # Use wait_for to allow checking disconnect + keep-alive
                data = await asyncio.wait_for(_thought_queue.get(), timeout=5.0)
                yield {"event": "message", "data": json.dumps(data)}
            except TimeoutError:
                # Keep-alive
                yield {"event": "ping", "data": "keep-alive"}
            except Exception as e:
                logger.error(f"SSE Error: {e}")
                break

    return EventSourceResponse(with_heartbeat(event_generator()))


# Endpoint for internal modules to push thoughts (simulating Pub/Sub publisher)
@shield(pillar="善")
@router.post("/emit")
async def emit_thought(thought: dict[str, Any]) -> dict[str, Any]:
    await broadcast_thought(thought)
    return {"status": "broadcasted"}
