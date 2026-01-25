"""IRS Changes SSE Router - Phase 80

Real-time Server-Sent Events endpoint for IRS change notifications.
Enables live streaming of IRS updates to agents and dashboards.

Author: AFO Kingdom Phase 80
Trinity Score: 善(Goodness) - Timely Tax Updates
"""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from AFO.services.irs_monitor_service import IRSMonitorService

logger = logging.getLogger("afo.api.irs_changes")

router = APIRouter(prefix="/api/irs/changes", tags=["IRS Changes"])


# SSE format helper
def _sse_format(event: str, data: dict[str, Any]) -> str:
    """Format data as SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


# In-memory change queue for SSE broadcasting
_change_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=100)
_monitor_service = IRSMonitorService()


async def _broadcast_change(change: dict[str, Any]) -> None:
    """Broadcast a change to all SSE subscribers."""
    try:
        _change_queue.put_nowait(change)
    except asyncio.QueueFull:
        # Drop oldest if queue full
        try:
            _change_queue.get_nowait()
            _change_queue.put_nowait(change)
        except Exception:
            pass


async def _sse_generator(
    include_heartbeat: bool = True,
    heartbeat_interval: int = 30,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for IRS changes."""
    # Send initial connection event
    yield _sse_format(
        "connected",
        {
            "status": "connected",
            "timestamp": datetime.now(UTC).isoformat(),
            "message": "IRS Changes SSE stream established",
        },
    )

    last_heartbeat = datetime.now(UTC)

    while True:
        try:
            # Try to get change with timeout
            try:
                change = await asyncio.wait_for(
                    _change_queue.get(),
                    timeout=heartbeat_interval if include_heartbeat else None,
                )
                yield _sse_format("change", change)
            except TimeoutError:
                # Send heartbeat on timeout
                if include_heartbeat:
                    now = datetime.now(UTC)
                    if (now - last_heartbeat).seconds >= heartbeat_interval:
                        yield _sse_format(
                            "heartbeat",
                            {
                                "timestamp": now.isoformat(),
                                "queue_size": _change_queue.qsize(),
                            },
                        )
                        last_heartbeat = now

        except asyncio.CancelledError:
            # Client disconnected
            yield _sse_format(
                "disconnected",
                {
                    "status": "disconnected",
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            break
        except Exception as e:
            logger.error(f"SSE generator error: {e}")
            yield _sse_format(
                "error",
                {
                    "error": str(e),
                    "timestamp": datetime.now(UTC).isoformat(),
                },
            )
            break


@router.get("/stream")
async def stream_irs_changes(
    heartbeat: bool = Query(default=True, description="Include heartbeat events"),
    heartbeat_interval: int = Query(default=30, ge=5, le=300, description="Heartbeat interval"),
) -> StreamingResponse:
    """Stream real-time IRS changes via Server-Sent Events.

    Returns:
        SSE stream with events:
        - connected: Initial connection confirmation
        - change: IRS change notification
        - heartbeat: Keep-alive signal
        - disconnected: Stream termination
        - error: Error notification

    Example usage:
        ```javascript
        const eventSource = new EventSource('/api/irs/changes/stream');
        eventSource.addEventListener('change', (e) => {
            const change = JSON.parse(e.data);
            console.log('IRS Change:', change);
        });
        ```
    """
    return StreamingResponse(
        _sse_generator(heartbeat, heartbeat_interval),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/recent")
async def get_recent_changes(
    limit: int = Query(default=20, ge=1, le=100, description="Number of changes to return"),
    since: str | None = Query(default=None, description="ISO timestamp to filter changes after"),
) -> dict[str, Any]:
    """Get recent IRS changes (non-streaming).

    Args:
        limit: Maximum number of changes to return
        since: Optional ISO timestamp to filter changes after

    Returns:
        List of recent IRS changes with metadata
    """
    try:
        # Get changes from monitor service
        changes = await _monitor_service.get_recent_changes(limit=limit)

        # Filter by timestamp if provided
        if since:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
            changes = [
                c
                for c in changes
                if datetime.fromisoformat(c.get("timestamp", "").replace("Z", "+00:00")) > since_dt
            ]

        return {
            "status": "success",
            "count": len(changes),
            "changes": changes,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get recent changes: {e}")
        return {
            "status": "error",
            "error": str(e),
            "changes": [],
            "timestamp": datetime.now(UTC).isoformat(),
        }


@router.post("/notify")
async def notify_change(
    change_type: str = Query(..., description="Type of change (publication, form, guidance)"),
    title: str = Query(..., description="Change title"),
    description: str = Query(default="", description="Change description"),
    source_url: str = Query(default="", description="Source URL"),
    severity: str = Query(default="info", description="Severity (info, warning, critical)"),
) -> dict[str, Any]:
    """Manually notify about an IRS change (for testing/admin).

    This endpoint allows manual injection of change notifications
    for testing or administrative purposes.
    """
    change = {
        "change_id": f"IRS-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
        "change_type": change_type,
        "title": title,
        "description": description,
        "source_url": source_url,
        "severity": severity,
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "manual",
    }

    await _broadcast_change(change)
    logger.info(f"Manual IRS change notification: {change['change_id']}")

    return {
        "status": "success",
        "message": "Change notification broadcasted",
        "change": change,
    }


@router.get("/status")
async def get_stream_status() -> dict[str, Any]:
    """Get current SSE stream status."""
    return {
        "status": "active",
        "queue_size": _change_queue.qsize(),
        "queue_max": _change_queue.maxsize,
        "monitor_status": await _monitor_service.get_status(),
        "timestamp": datetime.now(UTC).isoformat(),
    }


# Expose broadcast function for external use
__all__ = ["router", "_broadcast_change"]
