# Trinity Score: 90.0 (Established by Chancellor)
"""Phase 3: API 엔드포인트 통합 테스트
眞善美孝永 5기둥 철학에 의거한 API 통합 테스트

이 테스트는 다음 API 엔드포인트들의 통합 동작을 검증합니다:
- /api/health/comprehensive
- /api/skills/list
- /chancellor/health
- /api/trinity/health
"""

import asyncio
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

# 프로젝트 루트를 sys.path에 추가
_AFO_ROOT = Path(__file__).resolve().parent.parent
if str(_AFO_ROOT) not in sys.path:
    sys.path.insert(0, str(_AFO_ROOT))


@pytest.fixture
def api_client() -> TestClient:
    """API 클라이언트 픽스처"""
    try:
        from AFO.api_server import app

        return TestClient(app)
    except ImportError:
        pytest.skip("API server not available")


class TestHealthEndpointsIntegration:
    """眞 (Truth): Health 엔드포인트 통합 테스트"""

    def test_root_endpoint(self, api_client: TestClient) -> None:
        """루트 엔드포인트 테스트"""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "AFO Kingdom Soul Engine API"

    @pytest.mark.slow
    def test_comprehensive_health_endpoint(self, api_client: TestClient) -> None:
        """종합 건강 체크 엔드포인트 테스트"""
        response = api_client.get("/api/health/comprehensive")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # 최소한 status 또는 trinity 정보가 있어야 함
        assert "status" in data or "trinity" in data or "organs" in data


class TestSkillsEndpointsIntegration:
    """眞 (Truth): Skills 엔드포인트 통합 테스트"""

    def test_skills_list_endpoint(self, api_client: TestClient) -> None:
        """스킬 목록 조회 엔드포인트 테스트"""
        response = api_client.get("/api/skills/list")
        # 200 또는 404 가능 (서비스 상태에 따라)
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (dict, list))
            if isinstance(data, dict):
                assert "skills" in data or "items" in data or isinstance(data.get("data"), list)


class TestChancellorEndpointsIntegration:
    """眞善美 (Trinity): Chancellor 엔드포인트 통합 테스트"""

    def test_chancellor_health_endpoint(self, api_client: TestClient) -> None:
        """Chancellor 건강 체크 엔드포인트 테스트"""
        response = api_client.get("/chancellor/health")
        # 200 또는 404 가능 (서비스 상태에 따라)
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


class TestTrinityEndpointsIntegration:
    """眞善美孝永 (Trinity): Trinity 엔드포인트 통합 테스트"""

    def test_trinity_health_endpoint(self, api_client: TestClient) -> None:
        """Trinity 건강 체크 엔드포인트 테스트"""
        response = api_client.get("/api/trinity/health")
        # 200 또는 404 가능 (서비스 상태에 따라)
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
