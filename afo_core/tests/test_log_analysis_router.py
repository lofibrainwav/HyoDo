# Trinity Score: 90.0 (Established by Chancellor)
"""
Log Analysis Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - log_analysis.py

眞 (Truth): 로그 분석 API 엔드포인트 테스트
"""

from unittest.mock import MagicMock, patch

import pytest
from api.routers.log_analysis import (
    AnalysisRequest,
    AnalysisResponse,
    ReportSummary,
    get_report_content,
    list_reports,
    router,
    trigger_analysis,
)
from fastapi import HTTPException


class TestPydanticModels:
    """Pydantic 모델 테스트"""

    def test_analysis_request_valid(self):
        """유효한 분석 요청"""
        request = AnalysisRequest(log_path="/var/log/test.log")
        assert request.log_path == "/var/log/test.log"
        assert request.chunk_size is None

    def test_analysis_request_with_chunk_size(self):
        """청크 사이즈 포함 요청"""
        request = AnalysisRequest(log_path="/var/log/test.log", chunk_size=1000)
        assert request.chunk_size == 1000

    def test_analysis_response_success(self):
        """성공 응답 생성"""
        response = AnalysisResponse(
            status="success",
            message="Analysis completed",
            report_file="/reports/test.md",
            chunks_created=10,
        )
        assert response.status == "success"
        assert response.chunks_created == 10

    def test_report_summary(self):
        """리포트 요약 생성"""
        summary = ReportSummary(
            id="test_report",
            filename="test_report.md",
            created_at=1737446400.0,
            size=1024,
        )
        assert summary.id == "test_report"
        assert summary.size == 1024


class TestRouterEndpoints:
    """라우터 존재 확인"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert router is not None
        assert router.prefix == "/log-analysis"

    def test_router_has_endpoints(self):
        """엔드포인트 존재 확인"""
        routes = [route.path for route in router.routes]
        assert "/log-analysis/analyze" in routes
        assert "/log-analysis/reports" in routes
        assert "/log-analysis/reports/{filename}" in routes


class TestTriggerAnalysis:
    """trigger_analysis 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """존재하지 않는 파일 처리"""
        request = AnalysisRequest(log_path="/nonexistent/path.log")
        background_tasks = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            await trigger_analysis(request, background_tasks)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_analysis_success(self, tmp_path):
        """성공적인 분석"""
        # 임시 로그 파일 생성
        log_file = tmp_path / "test.log"
        log_file.write_text("Test log content")

        request = AnalysisRequest(log_path=str(log_file))
        background_tasks = MagicMock()

        mock_result = {
            "sequential": {"status": "success", "report_file": "/reports/test.md"},
            "chunking": {"status": "success", "chunks_created": 5},
        }

        with patch("api.routers.log_analysis._service") as mock_service:
            mock_service.run_pipeline.return_value = mock_result
            response = await trigger_analysis(request, background_tasks)

        assert response.status == "success"
        assert response.report_file == "/reports/test.md"
        assert response.chunks_created == 5

    @pytest.mark.asyncio
    async def test_analysis_partial_failure(self, tmp_path):
        """부분 실패 처리"""
        log_file = tmp_path / "test.log"
        log_file.write_text("Test log content")

        request = AnalysisRequest(log_path=str(log_file))
        background_tasks = MagicMock()

        mock_result = {
            "sequential": {"status": "failed"},
            "chunking": {"status": "success", "chunks_created": 3},
        }

        with patch("api.routers.log_analysis._service") as mock_service:
            mock_service.run_pipeline.return_value = mock_result
            response = await trigger_analysis(request, background_tasks)

        assert response.status == "partial_failure"

    @pytest.mark.asyncio
    async def test_analysis_exception(self, tmp_path):
        """분석 중 예외 처리 - shield decorator가 fallback 반환"""
        log_file = tmp_path / "test.log"
        log_file.write_text("Test log content")

        request = AnalysisRequest(log_path=str(log_file))
        background_tasks = MagicMock()

        with patch("api.routers.log_analysis._service") as mock_service:
            mock_service.run_pipeline.side_effect = RuntimeError("Pipeline error")

            # shield decorator catches RuntimeError and returns fallback response
            response = await trigger_analysis(request, background_tasks)

        # Fallback response from shield decorator
        assert response.status == "failure"
        assert "Resilience shield" in response.message


class TestListReports:
    """list_reports 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_empty_reports(self, tmp_path):
        """빈 리포트 목록"""
        with patch("api.routers.log_analysis.log_analysis_settings") as mock_settings:
            mock_settings.OUTPUT_DIR = tmp_path
            reports = await list_reports()

        assert reports == []

    @pytest.mark.asyncio
    async def test_list_reports_with_files(self, tmp_path):
        """리포트 파일 있는 경우"""
        # 테스트 리포트 파일 생성
        (tmp_path / "test1_report.md").write_text("Report 1")
        (tmp_path / "test2_report.md").write_text("Report 2")

        with patch("api.routers.log_analysis.log_analysis_settings") as mock_settings:
            mock_settings.OUTPUT_DIR = tmp_path
            reports = await list_reports()

        assert len(reports) == 2
        filenames = [r.filename for r in reports]
        assert "test1_report.md" in filenames
        assert "test2_report.md" in filenames


class TestGetReportContent:
    """get_report_content 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_directory_traversal_blocked(self):
        """디렉토리 탐색 공격 차단"""
        with pytest.raises(HTTPException) as exc_info:
            await get_report_content("../etc/passwd")

        assert exc_info.value.status_code == 400
        assert "Invalid filename" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_slash_blocked(self):
        """슬래시 포함 파일명 차단"""
        with pytest.raises(HTTPException) as exc_info:
            await get_report_content("path/to/file.md")

        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_report_not_found(self, tmp_path):
        """리포트 없음"""
        with patch("api.routers.log_analysis.log_analysis_settings") as mock_settings:
            mock_settings.OUTPUT_DIR = tmp_path

            with pytest.raises(HTTPException) as exc_info:
                await get_report_content("nonexistent.md")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_report_success(self, tmp_path):
        """리포트 조회 성공"""
        report_content = "# Test Report\n\nThis is a test."
        report_file = tmp_path / "test_report.md"
        report_file.write_text(report_content)

        with patch("api.routers.log_analysis.log_analysis_settings") as mock_settings:
            mock_settings.OUTPUT_DIR = tmp_path
            result = await get_report_content("test_report.md")

        assert result["filename"] == "test_report.md"
        assert result["content"] == report_content
