from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# Trinity Score: 90.0 (Established by Chancellor)
"""Automated Debugging Real-time Stream (SSE)
자동화 디버깅 시스템 실시간 스트리밍

眞善美孝永 철학에 기반한 실시간 모니터링
"""


router = APIRouter(prefix="/api/debugging", tags=["Automated Debugging"])

logger = logging.getLogger(__name__)

# 전역 이벤트 큐 (실제로는 Redis pub/sub 사용 권장)
_debugging_event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()


async def broadcast_debugging_event(event_data: dict[str, Any]) -> None:
    """디버깅 이벤트 브로드캐스트 (내부 모듈에서 호출)

    Args:
        event_data: 이벤트 데이터

    """
    await _debugging_event_queue.put(event_data)


@router.get("/stream")
async def stream_debugging_events(request: Request) -> EventSourceResponse:
    """자동화 디버깅 시스템 실시간 스트리밍 (SSE)

    클라이언트가 연결하면 디버깅 과정의 모든 이벤트를 실시간으로 스트리밍합니다.
    """
    logger.info("🔌 디버깅 스트림 연결됨")

    async def event_generator() -> AsyncGenerator[dict[str, Any], None]:
        # 초기 연결 메시지
        yield {
            "event": "message",
            "data": json.dumps(
                {
                    "source": "SYSTEM",
                    "type": "connection",
                    "message": "🏰 자동화 디버깅 시스템 스트림 연결됨",
                    "timestamp": datetime.now().isoformat(),
                    "retry": 3000,  # 3 seconds reconnection hint
                }
            ),
        }

        while True:
            # 클라이언트 연결 확인
            if await request.is_disconnected():
                logger.info("🔌 디버깅 스트림 연결 해제됨")
                break

            try:
                # 이벤트 대기 (타임아웃으로 keep-alive 전송)
                # TICKET-049: 정기적인 하트비트 주기를 15초에서 3.0초로 단축하여 실시간성 강화
                data = await asyncio.wait_for(_debugging_event_queue.get(), timeout=3.0)
                yield {"event": "message", "data": json.dumps(data)}
            except TimeoutError:
                # Keep-alive
                yield {
                    "event": "ping",
                    "data": json.dumps(
                        {
                            "type": "keep-alive",
                            "timestamp": datetime.now().isoformat(),
                        }
                    ),
                }
            except Exception as e:
                logger.error(f"❌ 디버깅 스트림 에러: {e}")
                break

    return EventSourceResponse(event_generator())


@router.post("/emit")
async def emit_debugging_event(event: dict[str, Any]) -> dict[str, Any]:
    """디버깅 이벤트 발생 (내부 모듈에서 호출)

    Args:
        event: 이벤트 데이터

    Returns:
        브로드캐스트 상태

    """
    await broadcast_debugging_event(event)
    return {"status": "broadcasted", "event_type": event.get("type", "unknown")}
