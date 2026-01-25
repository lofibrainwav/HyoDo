# Trinity Score: 90.0 (Established by Chancellor)
"""Grok Real-time Stream Router (Phase 18)
The Pulse of the Kingdom - Connecting the Cloud to the Dashboard.
"""

import asyncio
import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from AFO.utils.standard_shield import shield

router = APIRouter(prefix="/api/grok", tags=["Grok Stream"])


async def grok_event_stream() -> AsyncGenerator[str, None]:
    """Generates a stream of 'Grok Insights' simulating real-time cloud analysis.
    In a real scenario, this would subscribe to a Redis channel or actual LLM stream.
    """
    message_id = 1

    # Initial connection message
    initial_payload = {
        "id": 0,
        "timestamp": datetime.now(UTC).isoformat(),
        "content": "📡 Grok uplink established. Listening to the Cloud...",
        "source": "system",
    }
    yield f"data: {json.dumps(initial_payload)}\n\n"

    while True:
        # Simulate periodic "Grok" thoughts/checks (Every 5-10 seconds)
        await asyncio.sleep(5)

        # In a real system, we'd check for new messages in a queue here.
        # For the demo/visualizer, we pulse a heartbeat or a simulated insight.

        # We can add some variability or check system stats if we wanted to make it 'real'.
        # For now, following the 'Vibe' of the loop.

        qt = datetime.now(UTC).isoformat()

        # Alternating messages for demo effect
        if message_id % 3 == 0:
            content = (
                f"🔍 Grok Analysis #{message_id}: Trinity Alignment at 100%. Optimizing latency."
            )
            source = "grok"
        elif message_id % 3 == 1:
            content = f"☁️ Cloud Pulse #{message_id}: Kubernetes Node #1 health check passed."
            source = "system"
        else:
            content = f"💡 Strategy Insight #{message_id}: User intent detected in 'Phase 18'. Execution optimal."
            source = "grok"

        payload = {
            "id": message_id,
            "timestamp": qt,
            "content": content,
            "source": source,
        }

        yield f"data: {json.dumps(payload)}\n\n"
        message_id += 1


@shield(pillar="善")
@router.get("/stream")
async def grok_stream() -> StreamingResponse:
    """SSE Endpoint for Grok's Real-time Stream."""
    return StreamingResponse(grok_event_stream(), media_type="text/event-stream")
