# Trinity Score: 90.0 (Established by Chancellor)
"""
Debugging Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - debugging.py

眞 (Truth): 자동화 디버깅 엔드포인트 테스트
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.debugging import (
    get_debugging_history,
    get_debugging_status,
    router,
    run_debugging,
)
from fastapi import HTTPException


class TestDebuggingRouter:
    """라우터 기본 테스트"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert router is not None
        assert router.prefix == "/api/debugging"

    def test_router_has_endpoints(self):
        """엔드포인트 존재 확인"""
        routes = [route.path for route in router.routes]
        assert "/api/debugging/run" in routes
        assert "/api/debugging/status" in routes
        assert "/api/debugging/history" in routes


class TestRunDebugging:
    """run_debugging 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_run_debugging_success(self):
        """성공적인 디버깅 실행"""
        mock_report = MagicMock()
        mock_report.report_id = "test-report-123"
        mock_report.timestamp = datetime(2026, 1, 21, 12, 0, 0)
        mock_report.total_errors = 5
        mock_report.errors_by_severity = {"high": 2, "low": 3}
        mock_report.errors_by_category = {"syntax": 3, "type": 2}
        mock_report.auto_fixed = 3
        mock_report.manual_required = 2
        mock_report.trinity_score = 85.0
        mock_report.recommendations = ["Fix type errors"]
        mock_report.execution_time = 1.5

        with patch(
            "api.routes.debugging.run_automated_debugging",
            new_callable=AsyncMock,
            return_value=mock_report,
        ):
            result = await run_debugging()

        assert result["status"] == "success"
        assert result["report"]["report_id"] == "test-report-123"
        assert result["report"]["total_errors"] == 5

    @pytest.mark.asyncio
    async def test_run_debugging_failure(self):
        """디버깅 실행 실패"""
        with patch(
            "api.routes.debugging.run_automated_debugging",
            side_effect=RuntimeError("Debug system error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await run_debugging()

        assert exc_info.value.status_code == 500
        assert "Debug system error" in exc_info.value.detail


class TestGetDebuggingStatus:
    """get_debugging_status 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """상태 조회 성공"""
        mock_system = MagicMock()
        mock_system.project_root = "/test/path"

        with patch(
            "api.routes.debugging.AutomatedDebuggingSystem",
            return_value=mock_system,
        ):
            result = await get_debugging_status()

        assert result["status"] == "ready"
        assert "components" in result

    @pytest.mark.asyncio
    async def test_get_status_failure(self):
        """상태 조회 실패"""
        with patch(
            "api.routes.debugging.AutomatedDebuggingSystem",
            side_effect=RuntimeError("System init failed"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_debugging_status()

        assert exc_info.value.status_code == 500


class TestGetDebuggingHistory:
    """get_debugging_history 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_get_history_no_file(self):
        """히스토리 파일 없음"""
        mock_system = MagicMock()
        mock_path = MagicMock()
        mock_path.exists.return_value = False
        mock_system.project_root.__truediv__.return_value.__truediv__.return_value = mock_path

        with patch(
            "api.routes.debugging.AutomatedDebuggingSystem",
            return_value=mock_system,
        ):
            result = await get_debugging_history()

        assert result["status"] == "success"
        assert result["total_sessions"] == 0
        assert result["sessions"] == []

    @pytest.mark.asyncio
    async def test_get_history_with_data(self):
        """히스토리 데이터 있음"""
        mock_system = MagicMock()
        mock_path = MagicMock()
        mock_path.exists.return_value = True

        mock_system.project_root.__truediv__.return_value.__truediv__.return_value = mock_path

        mock_data = [{"session": 1}, {"session": 2}, {"session": 3}]

        with patch(
            "api.routes.debugging.AutomatedDebuggingSystem",
            return_value=mock_system,
        ):
            with patch("builtins.open", MagicMock()):
                with patch("json.load", return_value=mock_data):
                    result = await get_debugging_history(limit=2)

        assert result["status"] == "success"
        assert result["total_sessions"] == 3

    @pytest.mark.asyncio
    async def test_get_history_failure(self):
        """히스토리 조회 실패"""
        with patch(
            "api.routes.debugging.AutomatedDebuggingSystem",
            side_effect=RuntimeError("History error"),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_debugging_history()

        assert exc_info.value.status_code == 500
