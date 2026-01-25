# Trinity Score: 90.0 (Established by Chancellor)
"""
Client Stats Router Tests - Data Driven Model Verification

Tests for the Client Stats API that eliminates hardcoding via Redis.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from api.routers.client_stats import (
    DEFAULT_DEPENDENCY_COUNT,
    DEFAULT_LANGGRAPH_ACTIVE,
    DEFAULT_TOTAL_DEPENDENCIES,
    ClientStatsResponse,
    ClientStatsUpdate,
    get_client_stats,
    router,
    update_client_stats,
)
from fastapi.testclient import TestClient


class TestClientStatsRouter:
    """Client Stats Router Tests"""

    @pytest.fixture
    def client(self):
        """Create test client for the router"""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    def test_get_stats_fallback(self, client):
        """Test GET /api/client-stats returns fallback when Redis unavailable"""
        with patch("api.routers.client_stats._get_redis_client", return_value=None):
            response = client.get("/api/client-stats")
            assert response.status_code == 200
            data = response.json()
            assert data["dependency_count"] == DEFAULT_DEPENDENCY_COUNT
            assert data["langgraph_active"] == DEFAULT_LANGGRAPH_ACTIVE
            assert data["total_dependencies"] == DEFAULT_TOTAL_DEPENDENCIES
            assert data["source"] == "fallback"
            assert "timestamp" in data

    def test_get_stats_from_redis(self, client):
        """Test GET /api/client-stats returns values from Redis"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "client:stats:dependency_count": "50",
            "client:stats:langgraph_active": "true",
            "client:stats:total_dependencies": "55",
        }.get(key)

        with patch("api.routers.client_stats._get_redis_client", return_value=mock_redis):
            response = client.get("/api/client-stats")
            assert response.status_code == 200
            data = response.json()
            assert data["dependency_count"] == 50
            assert data["langgraph_active"] is True
            assert data["total_dependencies"] == 55
            assert data["source"] == "redis"

    def test_update_stats_success(self, client):
        """Test PUT /api/client-stats updates values in Redis"""
        mock_redis = MagicMock()
        mock_redis.get.side_effect = lambda key: {
            "client:stats:dependency_count": "100",
            "client:stats:langgraph_active": "false",
            "client:stats:total_dependencies": "100",
        }.get(key)
        mock_redis.set.return_value = True

        with patch("api.routers.client_stats._get_redis_client", return_value=mock_redis):
            response = client.put(
                "/api/client-stats",
                json={"dependency_count": 100, "langgraph_active": False},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["dependency_count"] == 100
            assert data["langgraph_active"] is False

    def test_update_stats_no_updates(self, client):
        """Test PUT /api/client-stats with empty body returns 400"""
        response = client.put("/api/client-stats", json={})
        assert response.status_code == 400
        assert "No updates provided" in response.json()["detail"]

    def test_update_stats_redis_unavailable(self, client):
        """Test PUT /api/client-stats returns 503 when Redis unavailable"""
        with patch("api.routers.client_stats._get_redis_client", return_value=None):
            response = client.put(
                "/api/client-stats",
                json={"dependency_count": 50},
            )
            assert response.status_code == 503
            assert "Redis unavailable" in response.json()["detail"]

    def test_reset_stats_success(self, client):
        """Test POST /api/client-stats/reset resets to defaults"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        with patch("api.routers.client_stats._get_redis_client", return_value=mock_redis):
            response = client.post("/api/client-stats/reset")
            assert response.status_code == 200
            data = response.json()
            assert data["defaults"]["dependency_count"] == DEFAULT_DEPENDENCY_COUNT
            assert data["defaults"]["langgraph_active"] == DEFAULT_LANGGRAPH_ACTIVE
            assert data["defaults"]["total_dependencies"] == DEFAULT_TOTAL_DEPENDENCIES

    def test_reset_stats_redis_unavailable(self, client):
        """Test POST /api/client-stats/reset returns 503 when Redis unavailable"""
        with patch("api.routers.client_stats._get_redis_client", return_value=None):
            response = client.post("/api/client-stats/reset")
            assert response.status_code == 503


class TestClientStatsFunctions:
    """Test helper functions directly"""

    def test_get_client_stats_fallback(self):
        """Test get_client_stats returns fallback when Redis unavailable"""
        with patch("api.routers.client_stats._get_redis_client", return_value=None):
            stats = get_client_stats()
            assert stats["source"] == "fallback"
            assert stats["dependency_count"] == DEFAULT_DEPENDENCY_COUNT

    def test_get_client_stats_initializes_missing_keys(self):
        """Test get_client_stats initializes missing keys in Redis"""
        mock_redis = MagicMock()
        mock_redis.get.return_value = None  # No keys exist

        with patch("api.routers.client_stats._get_redis_client", return_value=mock_redis):
            stats = get_client_stats()
            # Should have called set for each missing key
            assert mock_redis.set.call_count == 3
            assert stats["source"] == "redis"

    def test_update_client_stats_success(self):
        """Test update_client_stats updates Redis"""
        mock_redis = MagicMock()
        mock_redis.set.return_value = True

        with patch("api.routers.client_stats._get_redis_client", return_value=mock_redis):
            result = update_client_stats({"dependency_count": 75})
            assert result is True
            mock_redis.set.assert_called()

    def test_update_client_stats_redis_unavailable(self):
        """Test update_client_stats returns False when Redis unavailable"""
        with patch("api.routers.client_stats._get_redis_client", return_value=None):
            result = update_client_stats({"dependency_count": 75})
            assert result is False


class TestClientStatsModels:
    """Test Pydantic models"""

    def test_client_stats_update_validation(self):
        """Test ClientStatsUpdate validates correctly"""
        # Valid update
        update = ClientStatsUpdate(dependency_count=50, langgraph_active=True)
        assert update.dependency_count == 50
        assert update.langgraph_active is True

        # Partial update
        partial = ClientStatsUpdate(dependency_count=30)
        assert partial.dependency_count == 30
        assert partial.langgraph_active is None

    def test_client_stats_update_negative_validation(self):
        """Test ClientStatsUpdate rejects negative dependency_count"""
        with pytest.raises(ValueError):
            ClientStatsUpdate(dependency_count=-1)

    def test_client_stats_response_model(self):
        """Test ClientStatsResponse model"""
        response = ClientStatsResponse(
            dependency_count=42,
            langgraph_active=True,
            total_dependencies=42,
            source="redis",
            timestamp=datetime.now().isoformat(),
        )
        assert response.dependency_count == 42
        assert response.source == "redis"
