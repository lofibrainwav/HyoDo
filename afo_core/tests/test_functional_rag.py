# Trinity Score: 95.0 (Phase 29B Functional Coverage)
"""Functional Tests - Hybrid RAG

Split from test_coverage_functional.py for 500-line rule compliance.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =============================================================================
# Hybrid RAG Functional Tests
# =============================================================================


def test_hybrid_rag_basics() -> None:
    """Verify HybridRAG basic functions in services/hybrid_rag.py.
    Phase 25: Ollama 통일 - 테스트 업데이트
    """
    import services.hybrid_rag as hrag

    # 眞 (Truth): 난수 임베딩
    emb = hrag.random_embedding(10)
    assert len(emb) == 10

    # 善 (Goodness): 임베딩 (Ollama embeddinggemma - 768D)
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.1] * 768}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_response):
        emb2 = hrag.get_embedding("test", None)
        assert len(emb2) == 768  # embeddinggemma dimension

    # RRF / Blend
    rows = [{"id": "1", "score": 0.5, "content": "c1"}]
    blended = hrag.blend_results(rows, rows, top_k=5)
    assert len(blended) == 1


@pytest.mark.asyncio
async def test_hybrid_rag_answer():
    """Verify generate_answer_async in services/hybrid_rag.py.
    Phase 25: Ollama 통일 - 테스트 업데이트
    """
    import services.hybrid_rag as hrag

    # Ollama 응답 mock
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "Ollama response"}}
    mock_response.raise_for_status = MagicMock()

    # httpx.AsyncClient mock
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        ans = await hrag.generate_answer_async(
            "test query", ["context 1", "context 2"], 0.7, "markdown", "", None
        )
        assert "Ollama response" in ans


def test_hybrid_rag_deep() -> None:
    """Verify more paths in services/hybrid_rag.py.
    Phase 25: Ollama 통일 - 테스트 업데이트
    """
    from services.hybrid_rag import (
        generate_hyde_query,
        query_graph_context,
        query_pgvector,
        query_qdrant,
        query_redis,
        rerank_results,
    )

    # query_pgvector error path
    assert query_pgvector([0.1], 5, None) == []

    # query_redis error path
    assert query_redis([0.1], 5, None) == []

    # query_graph_context (hits 250-282 if simple)
    assert query_graph_context(["A"], 5) == []

    # query_qdrant (hits 302-313)
    assert query_qdrant([0.1], 5, None) == []

    # generate_hyde_query (Ollama mock)
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "hypothetical answer"}}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_response):
        result = generate_hyde_query("test", None)
        assert "test" in result  # Original query should be in result
        assert "hypothetical answer" in result  # HyDE answer appended

    # rerank_results - use different IDs to avoid skipping during deduplication
    res = [{"id": "1", "score": 0.5}, {"id": "2", "score": 0.6}]
    ranked = rerank_results(res)
    assert len(ranked) == 2
    assert ranked[0]["score"] == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
