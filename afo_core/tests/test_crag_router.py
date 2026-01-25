# Trinity Score: 90.0 (Established by Chancellor)
"""
CRAG Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - crag.py

眞 (Truth): Corrective RAG 파이프라인 API 테스트
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.crag import (
    CragRequest,
    CragResponse,
    generate_answer,
    grade_documents,
    perform_web_fallback,
    router,
)
from fastapi import HTTPException


class TestPydanticModels:
    """Pydantic 모델 테스트"""

    def test_crag_request_minimal(self):
        """최소 요청 생성"""
        request = CragRequest(question="테스트 질문")
        assert request.question == "테스트 질문"
        assert request.documents == []

    def test_crag_request_with_documents(self):
        """문서 포함 요청"""
        request = CragRequest(
            question="테스트 질문",
            documents=["문서1", "문서2"],
        )
        assert len(request.documents) == 2

    def test_crag_response(self):
        """응답 생성"""
        response = CragResponse(
            answer="테스트 답변",
            graded_docs={"doc1": 0.8, "doc2": 0.5},
            used_web_fallback=False,
        )
        assert response.answer == "테스트 답변"
        assert response.graded_docs["doc1"] == 0.8
        assert response.used_web_fallback is False


class TestRouterEndpoints:
    """라우터 존재 확인"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert router is not None
        assert router.prefix == "/api/crag"

    def test_router_has_crag_tag(self):
        """CRAG 태그 확인"""
        assert "CRAG" in router.tags


class TestGradeDocuments:
    """grade_documents 함수 테스트"""

    @pytest.mark.asyncio
    async def test_empty_documents(self):
        """빈 문서 리스트"""
        result = await grade_documents("질문", [])
        assert result == {}

    @pytest.mark.asyncio
    async def test_grade_with_llm_router(self):
        """LLM Router로 문서 채점"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.return_value = {"response": "0.85"}

        with patch("api.routes.crag.llm_router", mock_router):
            result = await grade_documents("테스트 질문", ["문서1"])

        assert "문서1" in result
        assert result["문서1"] == 0.85

    @pytest.mark.asyncio
    async def test_grade_clamps_to_range(self):
        """점수 0-1 범위로 클램핑"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.return_value = {"response": "1.5"}  # Over 1.0

        with patch("api.routes.crag.llm_router", mock_router):
            result = await grade_documents("질문", ["문서"])

        assert result["문서"] <= 1.0

    @pytest.mark.asyncio
    async def test_grade_handles_invalid_response(self):
        """잘못된 응답 처리"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.return_value = {"response": "invalid"}

        with patch("api.routes.crag.llm_router", mock_router):
            result = await grade_documents("질문", ["문서"])

        assert result["문서"] == 0.0

    @pytest.mark.asyncio
    async def test_grade_handles_exception(self):
        """예외 처리"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.side_effect = RuntimeError("LLM Error")

        with patch("api.routes.crag.llm_router", mock_router):
            result = await grade_documents("질문", ["문서"])

        assert result["문서"] == 0.0


class TestPerformWebFallback:
    """perform_web_fallback 함수 테스트"""

    def test_no_web_search_configured(self):
        """웹 검색 미설정"""
        with patch("api.routes.crag.web_search", None):
            result = perform_web_fallback("테스트 질문")
        assert result == []

    def test_web_search_list_results(self):
        """웹 검색 리스트 결과"""
        mock_search = MagicMock()
        mock_search.run.return_value = [
            {"content": "결과1"},
            {"text": "결과2"},
        ]

        with patch("api.routes.crag.web_search", mock_search):
            result = perform_web_fallback("테스트 질문")

        assert len(result) == 2
        assert "결과1" in result
        assert "결과2" in result

    def test_web_search_string_result(self):
        """웹 검색 문자열 결과"""
        mock_search = MagicMock()
        mock_search.run.return_value = "단일 결과 문자열"

        with patch("api.routes.crag.web_search", mock_search):
            result = perform_web_fallback("테스트 질문")

        assert len(result) == 1
        assert result[0] == "단일 결과 문자열"

    def test_web_search_exception(self):
        """웹 검색 예외"""
        mock_search = MagicMock()
        mock_search.run.side_effect = RuntimeError("Search Error")

        with patch("api.routes.crag.web_search", mock_search):
            result = perform_web_fallback("테스트 질문")

        assert result == []


class TestGenerateAnswer:
    """generate_answer 함수 테스트"""

    @pytest.mark.asyncio
    async def test_no_llm_router(self):
        """LLM Router 없음"""
        with patch("api.routes.crag.llm_router", None):
            result = await generate_answer("질문", "컨텍스트")

        assert "not available" in result

    @pytest.mark.asyncio
    async def test_generate_with_context(self):
        """컨텍스트로 답변 생성"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.return_value = {"response": "생성된 답변"}

        with patch("api.routes.crag.llm_router", mock_router):
            result = await generate_answer("질문", "컨텍스트 내용")

        assert result == "생성된 답변"
        mock_router.execute_with_routing.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_without_context(self):
        """컨텍스트 없이 답변 생성"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.return_value = {"response": "답변"}

        with patch("api.routes.crag.llm_router", mock_router):
            result = await generate_answer("질문", "")

        assert result == "답변"

    @pytest.mark.asyncio
    async def test_generate_empty_response(self):
        """빈 응답 처리"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.return_value = {"response": ""}

        with patch("api.routes.crag.llm_router", mock_router):
            result = await generate_answer("질문", "컨텍스트")

        assert "could not generate" in result

    @pytest.mark.asyncio
    async def test_generate_exception(self):
        """예외 처리"""
        mock_router = AsyncMock()
        mock_router.execute_with_routing.side_effect = RuntimeError("LLM Error")

        with patch("api.routes.crag.llm_router", mock_router):
            result = await generate_answer("질문", "컨텍스트")

        assert "Error" in result


class TestCragEndpoint:
    """crag_endpoint 테스트 (통합)"""

    @pytest.mark.asyncio
    async def test_empty_question(self):
        """빈 질문 처리"""
        from api.routes.crag import crag_endpoint

        request = CragRequest(question="  ", documents=[])

        with pytest.raises(HTTPException) as exc_info:
            await crag_endpoint(request)

        assert exc_info.value.status_code == 400
        assert "required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_no_llm_router_raises_503(self):
        """LLM Router 없으면 503"""
        from api.routes.crag import crag_endpoint

        request = CragRequest(question="질문", documents=[])

        with patch("api.routes.crag.llm_router", None):
            with pytest.raises(HTTPException) as exc_info:
                await crag_endpoint(request)

        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_full_pipeline_no_fallback(self):
        """전체 파이프라인 - fallback 없음"""
        from api.routes.crag import crag_endpoint

        mock_router = AsyncMock()
        # grade_documents response (high score)
        mock_router.execute_with_routing.side_effect = [
            {"response": "0.9"},  # grading
            {"response": "최종 답변"},  # answer generation
        ]

        request = CragRequest(question="질문", documents=["문서"])

        with patch("api.routes.crag.llm_router", mock_router):
            result = await crag_endpoint(request)

        assert result.answer == "최종 답변"
        assert result.used_web_fallback is False
        assert result.graded_docs["문서"] == 0.9

    @pytest.mark.asyncio
    async def test_full_pipeline_with_fallback(self):
        """전체 파이프라인 - fallback 사용"""
        from api.routes.crag import crag_endpoint

        mock_router = AsyncMock()
        mock_router.execute_with_routing.side_effect = [
            {"response": "0.3"},  # low score triggers fallback
            {"response": "웹 보강 답변"},
        ]

        mock_search = MagicMock()
        mock_search.run.return_value = [{"content": "웹 결과"}]

        request = CragRequest(question="질문", documents=["문서"])

        with patch("api.routes.crag.llm_router", mock_router):
            with patch("api.routes.crag.web_search", mock_search):
                result = await crag_endpoint(request)

        assert result.used_web_fallback is True
        assert result.graded_docs["문서"] == 0.3
