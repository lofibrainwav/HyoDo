# Trinity Score: 90.0 (Established by Chancellor)
"""
Edge Revalidate Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - edge_revalidate.py

眞 (Truth): ISR Revalidation API 테스트
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.edge_revalidate import (
    RevalidateRequest,
    RevalidateResponse,
    RevalidateStatusResponse,
    batch_revalidate,
    get_revalidation_status,
    router,
    trigger_revalidation,
    trigger_vercel_revalidate,
)


class TestPydanticModels:
    """Pydantic 모델 테스트"""

    def test_revalidate_request_valid(self):
        """유효한 재검증 요청"""
        request = RevalidateRequest(fragment_key="hero-section")
        assert request.fragment_key == "hero-section"
        assert request.path is None

    def test_revalidate_request_with_path(self):
        """경로 포함 요청"""
        request = RevalidateRequest(fragment_key="hero-section", path="/home")
        assert request.path == "/home"

    def test_revalidate_response(self):
        """재검증 응답 생성"""
        response = RevalidateResponse(
            success=True,
            fragment_key="hero-section",
            revalidated_at=datetime.now(),
            vercel_status=200,
            message="Success",
        )
        assert response.success is True
        assert response.vercel_status == 200

    def test_revalidate_status_response(self):
        """상태 응답 생성"""
        response = RevalidateStatusResponse(
            configured=True,
            revalidate_url="https://example.com",
            total_requests_today=5,
        )
        assert response.configured is True
        assert response.total_requests_today == 5


class TestRouterEndpoints:
    """라우터 존재 확인"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert router is not None
        assert router.prefix == "/edge"

    def test_router_has_endpoints(self):
        """엔드포인트 존재 확인"""
        routes = [route.path for route in router.routes]
        assert "/edge/revalidate" in routes
        assert "/edge/revalidate/status" in routes
        assert "/edge/revalidate/batch" in routes


class TestTriggerVercelRevalidate:
    """trigger_vercel_revalidate 헬퍼 테스트"""

    @pytest.mark.asyncio
    async def test_not_configured(self):
        """환경 변수 미설정 시"""
        with patch.dict("os.environ", {}, clear=True):
            success, status, message = await trigger_vercel_revalidate("test-key")

        assert success is False
        assert status == 0
        assert "not configured" in message

    @pytest.mark.asyncio
    async def test_success(self):
        """성공적인 재검증"""
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch.dict(
            "os.environ",
            {"REVALIDATE_URL": "https://example.com", "REVALIDATE_SECRET": "secret"},
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_client.return_value = mock_instance

                success, status, _ = await trigger_vercel_revalidate("test-key")

        assert success is True
        assert status == 200

    @pytest.mark.asyncio
    async def test_vercel_error(self):
        """Vercel 에러 응답"""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch.dict(
            "os.environ",
            {"REVALIDATE_URL": "https://example.com", "REVALIDATE_SECRET": "secret"},
        ):
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post.return_value = mock_response
                mock_instance.__aenter__.return_value = mock_instance
                mock_instance.__aexit__.return_value = None
                mock_client.return_value = mock_instance

                success, status, _ = await trigger_vercel_revalidate("test-key")

        assert success is False
        assert status == 500


class TestTriggerRevalidation:
    """trigger_revalidation 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_trigger_success(self):
        """재검증 트리거 성공"""
        request = RevalidateRequest(fragment_key="hero-section")
        background_tasks = MagicMock()

        with patch(
            "api.routes.edge_revalidate.trigger_vercel_revalidate",
            return_value=(True, 200, "Success"),
        ):
            response = await trigger_revalidation(request, background_tasks, None)

        assert response.success is True
        assert response.fragment_key == "hero-section"
        assert response.vercel_status == 200

    @pytest.mark.asyncio
    async def test_trigger_failure(self):
        """재검증 트리거 실패"""
        request = RevalidateRequest(fragment_key="hero-section")
        background_tasks = MagicMock()

        with patch(
            "api.routes.edge_revalidate.trigger_vercel_revalidate",
            return_value=(False, 0, "Not configured"),
        ):
            response = await trigger_revalidation(request, background_tasks, None)

        assert response.success is False
        assert response.vercel_status is None


class TestGetRevalidationStatus:
    """get_revalidation_status 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_not_configured(self):
        """미설정 상태"""
        with patch.dict("os.environ", {}, clear=True):
            response = await get_revalidation_status()

        assert response.configured is False
        assert response.revalidate_url is None

    @pytest.mark.asyncio
    async def test_configured(self):
        """설정된 상태"""
        with patch.dict(
            "os.environ",
            {"REVALIDATE_URL": "https://example.com", "REVALIDATE_SECRET": "secret"},
        ):
            response = await get_revalidation_status()

        assert response.configured is True
        assert response.revalidate_url == "https://example.com"


class TestBatchRevalidate:
    """batch_revalidate 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_batch_all_success(self):
        """모든 키 재검증 성공"""
        keys = ["key1", "key2", "key3"]
        background_tasks = MagicMock()

        with patch(
            "api.routes.edge_revalidate.trigger_vercel_revalidate",
            return_value=(True, 200, "Success"),
        ):
            with patch("asyncio.sleep", return_value=None):  # Skip delay
                result = await batch_revalidate(keys, background_tasks)

        assert result["total"] == 3
        assert result["successful"] == 3

    @pytest.mark.asyncio
    async def test_batch_partial_success(self):
        """부분 성공"""
        keys = ["key1", "key2"]
        background_tasks = MagicMock()

        # First call succeeds, second fails
        with patch(
            "api.routes.edge_revalidate.trigger_vercel_revalidate",
            side_effect=[
                (True, 200, "Success"),
                (False, 500, "Error"),
            ],
        ):
            with patch("asyncio.sleep", return_value=None):
                result = await batch_revalidate(keys, background_tasks)

        assert result["total"] == 2
        assert result["successful"] == 1
