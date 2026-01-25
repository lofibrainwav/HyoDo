import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient

# DSPy 문제回避를 위해 직접 app 생성
from AFO.api.config import get_app_config

app = get_app_config()

# RAG Query 라우터 등록 (query/stream 엔드포인트 포함)
try:
    from AFO.api.routers.rag_query import router as rag_query_router

    app.include_router(rag_query_router, prefix="/api")
    print("✅ RAG Query Router registered successfully")
except Exception as e:
    print(f"❌ RAG Query Router registration failed: {e}")


def test_debug_routes() -> None:
    """디버깅: 등록된 라우터 확인"""
    routes = []
    for route in app.routes:
        if hasattr(route, "path"):
            routes.append(route.path)
    print(f"Registered routes: {routes}")
    assert "/api/query/stream" in routes


@pytest.mark.slow
@pytest.mark.asyncio
async def test_rag_streaming_endpoint() -> None:
    """
    眞 (Truth): RAG 스트리밍 엔드포인트가 SSE 형식을 준수하고 실제 토큰을 반환하는지 검증
    善 (Goodness): 에러 이벤트만 오는 경우는 실패로 간주 (T2.1 UX 목표달성 검증)
    """
    from typing import AsyncIterator
    from unittest.mock import MagicMock, patch

    # Mock the generator to yield async events
    async def mock_generator(*args: object, **kwargs: object) -> AsyncIterator[str]:
        yield "event: start\ndata: {}\n\n"
        yield 'event: token\ndata: "AFO"\n\n'
        yield 'event: token\ndata: " Kingdom"\n\n'
        yield "event: done\ndata: {}\n\n"

    # Patch the function where it is imported in the router
    with patch(
        "AFO.api.routers.rag_query.generate_answer_stream_async",
        side_effect=mock_generator,
    ):
        # Phase 3: Mock payload
        payload = {
            "query": "Who is the Commander?",
            "use_hyde": False,
            "use_graph": False,
            "use_qdrant": False,
        }

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            async with ac.stream(
                "POST", "/api/query/stream", json=payload, timeout=5.0
            ) as response:
                assert response.status_code == 200
                assert "text/event-stream" in response.headers["content-type"]

                events = []
                async for line in response.aiter_lines():
                    if line.strip():
                        events.append(line)
                        # print(f"Received: {line}")

                # Check for specific event types
                has_start = any("event: start" in e for e in events)
                has_token = any("event: token" in e for e in events)
                has_done = any("event: done" in e for e in events)

                assert has_start, "❌ 'start' 이벤트가 누락되었습니다."
                assert has_token, "❌ 'token' 이벤트가 누락되었습니다."
                assert has_done, "❌ 'done' 이벤트가 누락되었습니다."

                # Check content presence
                content_found = any("AFO" in e for e in events)
                assert content_found, "❌ Mocked content 'AFO' not found in stream."

                print("✅ T2.1 RAG Streaming Verification Success (Mocked Stream)")
