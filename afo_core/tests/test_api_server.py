# Trinity Score: 90.0 (Established by Chancellor)
# Standardized for Trinity 100%
"""
Tests for api_server.py core functions
API 서버 핵심 함수 테스트 (Real Module Import)
"""

import os
import sys
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure AFO root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Late import to ensure path is set
# Late import to ensure path is set
from AFO.api_server import app


class TestAPIServerConfig:
    """API 서버 설정 테스트"""

    def test_api_metadata(self) -> None:
        """API 메타데이터 테스트"""
        assert "AFO" in app.title
        assert "Soul Engine" in app.title
        # Version check - actual version might change, just check structure
        assert len(app.version.split(".")) >= 2

    def test_app_configured(self) -> None:
        """App 설정 확인"""
        # Ensure title and version are set (non-empty)
        assert app.title
        assert app.version


class TestAPIServerRoutes:
    """API 서버 라우터 통합 테스트"""

    @pytest.fixture
    def client(self) -> TestClient:
        return TestClient(app)

    def test_health_route(self, client: TestClient) -> None:
        """/health 라우트 존재 확인"""
        response = client.get("/health")
        # 200 or 503 (if services down) but route exists
        assert response.status_code in [200, 500, 503]

    def test_root_route(self, client: TestClient) -> None:
        """Root 라우트 확인"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "version" in data

    def test_cors_headers(self, client: TestClient) -> None:
        """CORS 헤더 확인"""
        response = client.get("/", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] in {
            "*",
            "http://localhost:3000",
        }


class TestLifespan:
    """Lifespan 이벤트 테스트"""

    @pytest.mark.asyncio
    async def test_lifespan(self) -> None:
        """Lifespan 컨텍스트 매니저 테스트"""
        from AFO.api.config import get_lifespan_manager as lifespan

        # Use Any to avoid MyPy strictness on lifespan type
        # Disable strict startup checks by mocking
        # get_settings is imported in api_server, so we can patch it
        with patch("AFO.api.config.get_settings_safe"):
            async with lifespan(app):
                # Startup logic runs here
                pass
            # Shutdown logic runs here


class TestDependencyInjection:
    """의존성 주입 테스트"""

    def test_get_settings_injection(self) -> None:
        """설정 주입 테스트"""
        from AFO.config.settings import get_settings

        # Explicitly check if the function object exists to satisfy MyPy
        assert callable(get_settings)
        settings = get_settings()
        # POSTGRES_HOST should exist in settings
        assert hasattr(settings, "POSTGRES_HOST")


class TestLegacyImports:
    """레거시 import 호환성 테스트"""

    def test_path_setup(self) -> None:
        """sys.path 설정 확인"""
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        assert current_dir in sys.path
