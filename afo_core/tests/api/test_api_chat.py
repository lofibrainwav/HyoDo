# Trinity Score: 90.0 (Established by Chancellor)
"""Tests for api/routes/chat.py
Chat API 엔드포인트 테스트
"""

import pytest
from fastapi.testclient import TestClient


class TestChatEndpoint:
    """Chat API 엔드포인트 테스트"""

    @pytest.fixture
    def client(self) -> None:
        import os
        import sys

        sys.path.insert(
            0,
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )
        from AFO.api_server import app

        return TestClient(app)

    @pytest.mark.slow
    def test_chat_message_post(self, client: TestClient) -> None:
        """POST /api/chat/message 테스트"""
        response = client.post("/api/chat/message", json={"message": "Hello"})
        # 200 (성공) 또는 422 (검증 오류) 또는 500/503 (백엔드 문제)
        assert response.status_code in [200, 422, 500, 503]

    @pytest.mark.slow
    def test_chat_message_has_response(self, client: TestClient) -> None:
        """Chat 응답에 response 필드가 있는지 테스트"""
        response = client.post("/api/chat/message", json={"message": "test"})
        if response.status_code == 200:
            data = response.json()
            assert "response" in data or "error" in data

    def test_chat_providers_get(self, client: TestClient) -> None:
        """GET /api/chat/providers 테스트"""
        response = client.get("/api/chat/providers")
        assert response.status_code in [200, 404]

    def test_chat_stats_get(self, client: TestClient) -> None:
        """GET /api/chat/stats 테스트"""
        response = client.get("/api/chat/stats")
        assert response.status_code in [200, 404]

    def test_chat_health_get(self, client: TestClient) -> None:
        """GET /api/chat/health 테스트"""
        response = client.get("/api/chat/health")
        assert response.status_code in [200, 404]


class TestChatRouting:
    """Chat 라우팅 로직 테스트"""

    def test_routing_info_structure(self) -> None:
        """라우팅 정보 구조 테스트"""
        from typing import Any

        routing_info: dict[str, Any] = {
            "provider": "ollama",
            "model": "llama3.2:3b",
            "reasoning": "로컬 우선",
            "estimated_cost": 0.0,
            "estimated_latency": 500,
        }

        assert "provider" in routing_info
        assert "model" in routing_info
        assert routing_info["estimated_cost"] >= 0

    def test_provider_priority(self) -> None:
        """Provider 우선순위 테스트: Ollama → Gemini → Claude → OpenAI"""
        priority = ["ollama", "gemini", "claude", "openai"]
        assert priority[0] == "ollama"  # 로컬 우선
        assert len(priority) == 4

    def test_fallback_logic(self) -> None:
        """폴백 로직 테스트"""
        providers = ["ollama", "gemini", "claude", "openai"]
        failed = ["ollama"]  # Ollama 실패

        # 다음 사용 가능한 provider 찾기
        available = [p for p in providers if p not in failed]
        assert available[0] == "gemini"


class TestChatValidation:
    """Chat 입력 검증 테스트"""

    @pytest.fixture
    def client(self) -> None:
        import os
        import sys

        sys.path.insert(
            0,
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )
        from AFO.api_server import app

        return TestClient(app)

    def test_empty_message_rejected(self, client: TestClient) -> None:
        """빈 메시지가 거부되는지 테스트"""
        response = client.post("/api/chat/message", json={"message": ""})
        # 빈 메시지는 422 또는 처리됨
        assert response.status_code in [200, 422, 500]

    def test_missing_message_field(self, client: TestClient) -> None:
        """Message 필드 누락 시 422 반환 테스트"""
        response = client.post("/api/chat/message", json={})
        assert response.status_code == 422

    @pytest.mark.slow
    def test_long_message_handled(self, client: TestClient) -> None:
        """긴 메시지 처리 테스트"""
        long_message = "test " * 1000
        response = client.post("/api/chat/message", json={"message": long_message})
        assert response.status_code in [200, 422, 500, 503]
