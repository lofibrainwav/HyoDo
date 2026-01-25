# Trinity Score: 90.0 (Established by Chancellor)
"""
Heal Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - heal_router.py

眞 (Truth): 시스템 복구 엔드포인트 테스트
善 (Goodness): Mock을 사용한 안전한 테스트
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.heal_router import HealResponse, heal_kingdom, router
from fastapi import HTTPException
from fastapi.testclient import TestClient


class TestHealResponse:
    """HealResponse 모델 테스트"""

    def test_valid_response(self):
        """유효한 응답 생성"""
        response = HealResponse(
            success=True,
            message="Services restarted",
            action="docker_restart",
        )
        assert response.success is True
        assert response.action == "docker_restart"

    def test_failed_response(self):
        """실패 응답 생성"""
        response = HealResponse(
            success=False,
            message="Docker daemon down",
            action="manual_intervention_required",
        )
        assert response.success is False


class TestHealKingdomEndpoint:
    """heal_kingdom 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_heal_success(self):
        """성공적인 시스템 복구"""
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.communicate = AsyncMock(return_value=(b"Success", b""))

        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            result = await heal_kingdom()

        assert result.success is True
        assert result.action == "docker_restart"
        assert "successfully" in result.message.lower()

    @pytest.mark.asyncio
    async def test_heal_docker_daemon_down(self):
        """Docker 데몬 다운 시 처리"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Cannot connect to the Docker daemon")
        )

        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            result = await heal_kingdom()

        assert result.success is False
        assert result.action == "manual_intervention_required"

    @pytest.mark.asyncio
    async def test_heal_generic_failure(self):
        """일반 실패 시 HTTPException 발생"""
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_process.communicate = AsyncMock(return_value=(b"", b"Some other error"))

        with patch("asyncio.create_subprocess_shell", return_value=mock_process):
            with pytest.raises(HTTPException) as exc_info:
                await heal_kingdom()

        assert exc_info.value.status_code == 500
        assert "Some other error" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_heal_critical_exception(self):
        """Critical exception 처리"""
        with patch(
            "asyncio.create_subprocess_shell",
            side_effect=OSError("Permission denied"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await heal_kingdom()

        assert exc_info.value.status_code == 500
        assert "Permission denied" in exc_info.value.detail


class TestHealRouterIntegration:
    """라우터 통합 테스트"""

    def test_router_exists(self):
        """라우터가 존재하는지 확인"""
        assert router is not None
        routes = [route.path for route in router.routes]
        assert "/heal" in routes
