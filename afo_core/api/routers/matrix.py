# Trinity Score: 90.0 (Established by Chancellor)
"""Matrix Router (The Gateway)
Phase 10: Real-time Thought Stream
"""

import logging
from typing import Any

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

from AFO.services.matrix_stream import matrix_stream
from AFO.utils.standard_shield import shield

router = APIRouter()
logger = logging.getLogger("afo.api.matrix")


@shield(pillar="美")
@router.get("/matrix-stream")
async def matrix_feed(request: Request) -> Any:
    """SSE Endpoint for The Matrix Stream.
    Broadcasts AI thoughts with Pillar Classification.
    """
    logger.info(f"🕶️ Matrix Stream Connected: {request.client.host}")  # type: ignore

    return EventSourceResponse(matrix_stream.event_generator())


# Endpoint for pushing thoughts (simulating internal monologues)
@shield(pillar="美")
@router.post("/matrix-stream/emit")
async def emit_thought(payload: dict[str, str]) -> dict[str, str]:
    """Internal endpoint to push thoughts to the stream.
    Payload: {"text": "thinking...", "level": "info"}
    """
    text = payload.get("text", "")
    level = payload.get("level", "info")

    await matrix_stream.push_thought(text, level)
    return {"status": "emitted"}
