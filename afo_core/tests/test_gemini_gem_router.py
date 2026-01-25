# Trinity Score: 90.0 (Established by Chancellor)
"""
Tests for Gemini Gem API Router

Tests REST API endpoints for the Gemini Gem chat widget.
"""

from unittest.mock import AsyncMock, patch

import pytest
from api.routes.gemini_gem import router
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app() -> FastAPI:
    """Create FastAPI app with router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create test client."""
    return TestClient(app)


class TestGemChatEndpoint:
    """Tests for POST /api/gemini-gem/chat endpoint."""

    def test_chat_returns_response(self, client: TestClient) -> None:
        """Chat endpoint should return a response."""
        mock_result = {
            "success": True,
            "response": "Hello! How can I help?",
            "session_id": "gem-12345678",
            "timestamp": "2025-01-21T12:00:00",
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.chat",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = client.post(
                "/api/gemini-gem/chat",
                json={"message": "Hello"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["response"] == "Hello! How can I help?"
        assert data["session_id"] == "gem-12345678"

    def test_chat_with_session_id(self, client: TestClient) -> None:
        """Chat endpoint should accept session_id."""
        mock_result = {
            "success": True,
            "response": "Continued conversation",
            "session_id": "existing-session",
            "timestamp": "2025-01-21T12:00:00",
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.chat",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = client.post(
                "/api/gemini-gem/chat",
                json={"message": "Continue", "session_id": "existing-session"},
            )

        assert response.status_code == 200
        assert response.json()["session_id"] == "existing-session"

    def test_chat_validates_empty_message(self, client: TestClient) -> None:
        """Chat endpoint should reject empty messages."""
        response = client.post(
            "/api/gemini-gem/chat",
            json={"message": ""},
        )

        assert response.status_code == 422  # Validation error

    def test_chat_handles_error_response(self, client: TestClient) -> None:
        """Chat endpoint should handle error responses."""
        mock_result = {
            "success": False,
            "error": "API unavailable",
            "session_id": "gem-12345678",
            "timestamp": "2025-01-21T12:00:00",
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.chat",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            response = client.post(
                "/api/gemini-gem/chat",
                json={"message": "Hello"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["error"] == "API unavailable"


class TestClearSessionEndpoint:
    """Tests for POST /api/gemini-gem/clear/{session_id} endpoint."""

    def test_clear_existing_session(self, client: TestClient) -> None:
        """Should clear existing session successfully."""
        with patch(
            "api.routes.gemini_gem.gemini_gem_service.clear_session",
            return_value=True,
        ):
            response = client.post("/api/gemini-gem/clear/test-session")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_clear_nonexistent_session(self, client: TestClient) -> None:
        """Should return 404 for non-existent session."""
        with patch(
            "api.routes.gemini_gem.gemini_gem_service.clear_session",
            return_value=False,
        ):
            response = client.post("/api/gemini-gem/clear/nonexistent")

        assert response.status_code == 404


class TestGetSessionInfoEndpoint:
    """Tests for GET /api/gemini-gem/session/{session_id} endpoint."""

    def test_get_existing_session_info(self, client: TestClient) -> None:
        """Should return session info for existing session."""
        mock_info = {
            "session_id": "test-session",
            "created_at": "2025-01-21T12:00:00",
            "updated_at": "2025-01-21T12:05:00",
            "message_count": 4,
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.get_session_info",
            return_value=mock_info,
        ):
            response = client.get("/api/gemini-gem/session/test-session")

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert data["message_count"] == 4

    def test_get_nonexistent_session_info(self, client: TestClient) -> None:
        """Should return 404 for non-existent session."""
        with patch(
            "api.routes.gemini_gem.gemini_gem_service.get_session_info",
            return_value=None,
        ):
            response = client.get("/api/gemini-gem/session/nonexistent")

        assert response.status_code == 404


class TestStatusEndpoint:
    """Tests for GET /api/gemini-gem/status endpoint."""

    def test_get_status(self, client: TestClient) -> None:
        """Should return service status."""
        mock_status = {
            "available": True,
            "model": "gemini-1.5-flash",
            "active_sessions": 5,
            "max_sessions": 100,
            "gem_url": "https://gemini.google.com/gem/test",
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.get_service_status",
            return_value=mock_status,
        ):
            response = client.get("/api/gemini-gem/status")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["model"] == "gemini-1.5-flash"
        assert data["active_sessions"] == 5


class TestHealthEndpoint:
    """Tests for GET /api/gemini-gem/health endpoint."""

    def test_health_when_available(self, client: TestClient) -> None:
        """Should return healthy when API available."""
        mock_status = {
            "available": True,
            "model": "gemini-1.5-flash",
            "active_sessions": 0,
            "max_sessions": 100,
            "gem_url": "https://gemini.google.com/gem/test",
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.get_service_status",
            return_value=mock_status,
        ):
            response = client.get("/api/gemini-gem/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["gemini_available"] is True

    def test_health_when_unavailable(self, client: TestClient) -> None:
        """Should return degraded when API unavailable."""
        mock_status = {
            "available": False,
            "model": "gemini-1.5-flash",
            "active_sessions": 0,
            "max_sessions": 100,
            "gem_url": "https://gemini.google.com/gem/test",
        }

        with patch(
            "api.routes.gemini_gem.gemini_gem_service.get_service_status",
            return_value=mock_status,
        ):
            response = client.get("/api/gemini-gem/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["gemini_available"] is False
