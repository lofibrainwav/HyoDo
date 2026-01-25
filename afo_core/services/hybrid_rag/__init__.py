"""
HybridRAG 패키지

리팩터링: 500줄 규칙 준수를 위해 모듈 분리
- models.py: Pydantic 모델
- embedding.py: 임베딩 관련 함수
- queries.py: DB 쿼리 함수
- fusion.py: 결과 통합/Reranking
- generation.py: LLM 답변 생성

Trinity Score: 90.0 (Established by Chancellor)
"""

from AFO.services.hybrid_rag.embedding import (
    generate_hyde_query,
    generate_hyde_query_async,
    get_embedding,
    get_embedding_async,
    random_embedding,
)
from AFO.services.hybrid_rag.fusion import (
    blend_results,
    blend_results_advanced,
    blend_results_async,
    rerank_results,
    select_context,
)
from AFO.services.hybrid_rag.generation import (
    generate_answer,
    generate_answer_async,
    generate_answer_stream_async,
)
from AFO.services.hybrid_rag.models import (
    HybridChunk,
    HybridQueryRequest,
    HybridQueryResponse,
)
from AFO.services.hybrid_rag.queries import (
    query_graph_context,
    query_pgvector,
    query_pgvector_async,
    query_qdrant,
    query_qdrant_async,
    query_redis,
    query_redis_async,
)

__all__ = [
    # Models
    "HybridQueryRequest",
    "HybridChunk",
    "HybridQueryResponse",
    # Embedding
    "random_embedding",
    "get_embedding",
    "get_embedding_async",
    "generate_hyde_query",
    "generate_hyde_query_async",
    # Queries
    "query_pgvector",
    "query_pgvector_async",
    "query_redis",
    "query_redis_async",
    "query_graph_context",
    "query_qdrant",
    "query_qdrant_async",
    # Fusion
    "rerank_results",
    "blend_results",
    "blend_results_async",
    "blend_results_advanced",
    "select_context",
    # Generation
    "generate_answer",
    "generate_answer_async",
    "generate_answer_stream_async",
    # Class
    "HybridRAG",
]


from typing import Any


class HybridRAG:
    """Wrapper class for HybridRAG functional implementation."""

    available = True

    @staticmethod
    async def generate_answer_async(
        query: str,
        contexts: list[str],
        temperature: float,
        response_format: str,
        additional_instructions: str,
        openai_client: Any = None,
        graph_context: list[dict[str, Any]] | None = None,
    ) -> str | dict[str, Any]:
        try:
            return await generate_answer_async(
                query,
                contexts,
                temperature,
                response_format,
                additional_instructions,
                openai_client=openai_client,
                graph_context=graph_context,
            )
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"HybridRAG failed to generate answer: {e}", exc_info=True, extra={"pillar": "善"}
            )
            return "RAG Generation failed due to internal error."

    @staticmethod
    async def generate_hyde_query_async(query: str, client: Any) -> str:
        return await generate_hyde_query_async(query, client)

    @staticmethod
    async def get_embedding_async(text: str, client: Any) -> list[float]:
        try:
            return await get_embedding_async(text, client)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"HybridRAG failed to get embedding: {e}", exc_info=True, extra={"pillar": "善"}
            )
            return random_embedding()  # Fallback to random to prevent complete failure

    @staticmethod
    async def query_qdrant_async(
        embedding: list[float],
        top_k: int,
        client: Any,
    ) -> list[dict[str, Any]]:
        try:
            return await query_qdrant_async(embedding, top_k, client)
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(
                f"HybridRAG failed to query Qdrant: {e}", exc_info=True, extra={"pillar": "善"}
            )
            return []

    @staticmethod
    def query_graph_context(entities: list[str]) -> list[dict[str, Any]]:
        return query_graph_context(entities)

    @staticmethod
    async def generate_answer_stream_async(
        query: str,
        contexts: list[str],
        temperature: float,
        response_format: str,
        additional_instructions: str,
        openai_client: Any = None,
    ) -> Any:
        return generate_answer_stream_async(
            query,
            contexts,
            temperature,
            response_format,
            additional_instructions,
            openai_client,
        )
