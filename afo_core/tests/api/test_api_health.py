# Trinity Score: 90.0 (Established by Chancellor)
"""Test API Health Endpoints
테스트 커버리지 향상 Phase 1
"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Health 엔드포인트 테스트"""

    @pytest.fixture
    def client(self) -> TestClient:
        """FastAPI TestClient 생성"""
        # Import lazily to avoid import errors
        import os
        import sys

        sys.path.insert(
            0,
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )

        from AFO.api_server import app

        return TestClient(app)

    def test_health_endpoint_returns_200(self, client: TestClient) -> None:
        """GET /health 가 200을 반환하는지 테스트"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_has_status(self, client: TestClient) -> None:
        """GET /health 응답에 status 필드가 있는지 테스트"""
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] in ["balanced", "unbalanced", "warning", "imbalanced"]

    def test_health_endpoint_has_trinity(self, client: TestClient) -> None:
        """GET /health 응답에 trinity 필드가 있는지 테스트"""
        response = client.get("/health")
        data = response.json()
        assert "trinity" in data

    def test_trinity_score_range(self, client: TestClient) -> None:
        """Trinity score가 0-1 범위인지 테스트"""
        response = client.get("/health")
        data = response.json()
        trinity = data.get("trinity", {})
        if "trinity_score" in trinity:
            assert 0 <= trinity["trinity_score"] <= 1

    def test_health_percentage_range(self, client: TestClient) -> None:
        """health_percentage가 0-100 범위인지 테스트"""
        response = client.get("/health")
        data = response.json()
        if "health_percentage" in data:
            assert 0 <= data["health_percentage"] <= 100

    def test_organs_present(self, client: TestClient) -> None:
        """Organs 필드가 있는지 테스트"""
        response = client.get("/health")
        data = response.json()
        assert "organs" in data

    def test_decision_field(self, client: TestClient) -> None:
        """Decision 필드가 AUTO_RUN 또는 ASK인지 테스트"""
        response = client.get("/health")
        data = response.json()
        if "decision" in data:
            assert data["decision"] in ["AUTO_RUN", "ASK_COMMANDER", "TRY_AGAIN", "ASK"]


class TestRootEndpoint:
    """Root 엔드포인트 테스트"""

    @pytest.fixture
    def client(self) -> TestClient:
        import os
        import sys

        sys.path.insert(
            0,
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        )
        from AFO.api_server import app

        return TestClient(app)

    def test_root_endpoint_returns_200(self, client: TestClient) -> None:
        """GET / 가 200을 반환하는지 테스트"""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_has_version(self, client: TestClient) -> None:
        """GET / 응답에 version 필드가 있는지 테스트"""
        response = client.get("/")
        data = response.json()
        assert "version" in data or "api_version" in data or "message" in data
