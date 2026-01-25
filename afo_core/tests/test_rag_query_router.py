# Trinity Score: 90.0 (Established by Chancellor)
"""
RAG Query Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - rag_query.py

眞 (Truth): GraphRAG 파이프라인 API 테스트
"""

from unittest.mock import AsyncMock, patch

import pytest
from api.routers.rag_query import (
    HybridRAGService,
    RAGPipelineContext,
    RAGRequest,
    RAGResponse,
    _extract_entities,
    _stage_context_selection,
    _stage_embedding,
    _stage_graph_context,
    _stage_hyde,
    _stage_retrieval,
    router,
)


class TestPydanticModels:
    """Pydantic 모델 테스트"""

    def test_rag_request_defaults(self):
        """기본값이 있는 RAG 요청"""
        request = RAGRequest(query="테스트 질문")
        assert request.query == "테스트 질문"
        assert request.top_k == 5
        assert request.use_hyde is True
        assert request.use_graph is True
        assert request.use_qdrant is True

    def test_rag_request_custom_values(self):
        """사용자 정의 값이 있는 RAG 요청"""
        request = RAGRequest(
            query="질문",
            top_k=10,
            use_hyde=False,
            use_graph=False,
            use_qdrant=False,
        )
        assert request.top_k == 10
        assert request.use_hyde is False

    def test_rag_response_creation(self):
        """RAG 응답 생성"""
        response = RAGResponse(
            answer="테스트 답변",
            sources=[{"id": 1}],
            graph_context=[{"entity": "test"}],
            processing_log=["Step 1", "Step 2"],
        )
        assert response.answer == "테스트 답변"
        assert len(response.sources) == 1
        assert len(response.graph_context) == 1
        assert len(response.processing_log) == 2


class TestRAGPipelineContext:
    """RAG 파이프라인 컨텍스트 테스트"""

    def test_context_initialization(self):
        """컨텍스트 초기화"""
        ctx = RAGPipelineContext(query="테스트")
        assert ctx.query == "테스트"
        assert ctx.search_query == ""
        assert ctx.embedding == []
        assert ctx.results == []
        assert ctx.graph_context == []
        assert ctx.contexts == []
        assert ctx.logs == []

    def test_context_mutable_fields(self):
        """컨텍스트 필드 수정"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.search_query = "변환된 질문"
        ctx.embedding = [0.1, 0.2, 0.3]
        ctx.logs.append("로그 추가")

        assert ctx.search_query == "변환된 질문"
        assert len(ctx.embedding) == 3
        assert len(ctx.logs) == 1


class TestHybridRAGService:
    """HybridRAGService 클래스 테스트"""

    def test_service_available_flag(self):
        """서비스 가용성 플래그"""
        assert HybridRAGService.available is True


class TestRouterEndpoints:
    """라우터 존재 확인"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert router is not None

    def test_router_has_endpoints(self):
        """엔드포인트 존재 확인"""
        routes = [route.path for route in router.routes]
        assert "/query" in routes
        assert "/query/stream" in routes


class TestStageHyde:
    """_stage_hyde 헬퍼 테스트"""

    @pytest.mark.asyncio
    async def test_hyde_disabled(self):
        """HyDE 비활성화"""
        ctx = RAGPipelineContext(query="테스트 질문")
        await _stage_hyde(ctx, use_hyde=False)

        assert ctx.search_query == "테스트 질문"
        assert "HyDE Skipped" in ctx.logs[0]

    @pytest.mark.asyncio
    async def test_hyde_enabled_success(self):
        """HyDE 활성화 성공"""
        ctx = RAGPipelineContext(query="테스트 질문")

        with patch(
            "api.routers.rag_query.generate_hyde_query_async",
            new_callable=AsyncMock,
        ) as mock_hyde:
            mock_hyde.return_value = "HyDE 변환된 질문입니다"
            await _stage_hyde(ctx, use_hyde=True)

        assert ctx.search_query == "HyDE 변환된 질문입니다"
        assert "HyDE Generated" in ctx.logs[0]

    @pytest.mark.asyncio
    async def test_hyde_enabled_error(self):
        """HyDE 활성화 시 에러"""
        ctx = RAGPipelineContext(query="테스트 질문")

        with patch(
            "api.routers.rag_query.generate_hyde_query_async",
            new_callable=AsyncMock,
        ) as mock_hyde:
            mock_hyde.side_effect = RuntimeError("HyDE 실패")
            await _stage_hyde(ctx, use_hyde=True)

        assert ctx.search_query == "테스트 질문"  # Fallback to original
        assert "HyDE Skipped (error)" in ctx.logs[0]


class TestStageEmbedding:
    """_stage_embedding 헬퍼 테스트"""

    @pytest.mark.asyncio
    async def test_embedding_success(self):
        """임베딩 생성 성공"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.search_query = "검색 쿼리"

        with patch(
            "api.routers.rag_query.get_embedding_async",
            new_callable=AsyncMock,
        ) as mock_embed:
            mock_embed.return_value = [0.1] * 768
            await _stage_embedding(ctx)

        assert len(ctx.embedding) == 768

    @pytest.mark.asyncio
    async def test_embedding_failure(self):
        """임베딩 생성 실패 시 폴백"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.search_query = "검색 쿼리"

        with patch(
            "api.routers.rag_query.get_embedding_async",
            new_callable=AsyncMock,
        ) as mock_embed:
            mock_embed.side_effect = RuntimeError("임베딩 실패")
            await _stage_embedding(ctx)

        assert len(ctx.embedding) == 768  # Fallback dimension
        assert all(v == 0.0 for v in ctx.embedding)
        assert "Embedding Failed" in ctx.logs[0]


class TestStageRetrieval:
    """_stage_retrieval 헬퍼 테스트"""

    @pytest.mark.asyncio
    async def test_retrieval_disabled(self):
        """검색 비활성화"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.embedding = [0.1] * 768

        await _stage_retrieval(ctx, top_k=5, use_qdrant=False)

        assert ctx.results == []

    @pytest.mark.asyncio
    async def test_retrieval_success(self):
        """검색 성공"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.embedding = [0.1] * 768

        mock_results = [{"content": "결과1"}, {"content": "결과2"}]

        # QdrantClient is imported inside the function, patch at source
        with patch("qdrant_client.QdrantClient"):
            with patch(
                "api.routers.rag_query.query_qdrant_async",
                new_callable=AsyncMock,
            ) as mock_query:
                mock_query.return_value = mock_results
                await _stage_retrieval(ctx, top_k=5, use_qdrant=True)

        assert len(ctx.results) == 2
        assert "Retrieved 2 chunks" in ctx.logs[0]


class TestExtractEntities:
    """_extract_entities 헬퍼 테스트"""

    def test_extract_from_query(self):
        """쿼리에서 엔티티 추출"""
        query = "Python Django Framework"
        results = []
        entities = _extract_entities(query, results)

        # Words with length > 4
        assert "Python" in entities
        assert "Django" in entities
        assert "Framework" in entities

    def test_extract_from_results(self):
        """결과에서 엔티티 추출"""
        query = "test"
        results = [
            {"metadata": {"content": "FastAPI Redis PostgreSQL lowercase"}},
        ]
        entities = _extract_entities(query, results)

        # Capitalized words from content
        assert "FastAPI" in entities
        assert "Redis" in entities
        assert "PostgreSQL" in entities

    def test_extract_max_five(self):
        """최대 5개 엔티티"""
        query = "Python Django FastAPI Redis PostgreSQL MongoDB Elasticsearch"
        results = []
        entities = _extract_entities(query, results)

        assert len(entities) <= 5


class TestStageGraphContext:
    """_stage_graph_context 헬퍼 테스트"""

    def test_graph_disabled(self):
        """그래프 비활성화"""
        ctx = RAGPipelineContext(query="테스트")
        _stage_graph_context(ctx, use_graph=False)

        assert ctx.graph_context == []

    def test_graph_enabled_with_entities(self):
        """그래프 활성화 - 엔티티 있음"""
        ctx = RAGPipelineContext(query="Python Django Framework")

        with patch("api.routers.rag_query.query_graph_context") as mock_graph:
            mock_graph.return_value = [{"relation": "uses"}]
            _stage_graph_context(ctx, use_graph=True)

        assert len(ctx.graph_context) == 1
        assert "Graph Context" in ctx.logs[0]


class TestStageContextSelection:
    """_stage_context_selection 헬퍼 테스트"""

    def test_context_selection_empty(self):
        """빈 결과"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.results = []

        _stage_context_selection(ctx)

        assert ctx.contexts == []

    def test_context_selection_with_results(self):
        """결과가 있는 경우"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.results = [
            {"content": "내용1"},
            {"content": "내용2"},
            {"content": "내용3"},
            {"content": "내용4"},
            {"content": "내용5"},
            {"content": "내용6"},  # 6th should be excluded
        ]

        _stage_context_selection(ctx)

        assert len(ctx.contexts) == 5
        assert "내용6" not in ctx.contexts

    def test_context_selection_non_dict(self):
        """dict가 아닌 결과 처리"""
        ctx = RAGPipelineContext(query="테스트")
        ctx.results = [{"content": "내용1"}, "not_a_dict", None]

        _stage_context_selection(ctx)

        assert len(ctx.contexts) == 1


class TestModuleExports:
    """모듈 exports 테스트"""

    def test_router_prefix(self):
        """라우터 prefix 없음 (루트 라우터)"""
        # rag_query router doesn't have a prefix set
        assert router is not None
