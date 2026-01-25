# Trinity Score: 90.0 (Established by Chancellor)
# Phase 25: Ollama 통일 - 테스트 업데이트
from typing import Any, Union
from unittest.mock import MagicMock, patch

import pytest

from AFO.services.hybrid_rag import (
    blend_results,
    generate_answer,
    get_embedding,
    get_embedding_async,
    query_pgvector,
    query_pgvector_async,
    query_redis,
    select_context,
)

# Default embedding dimension for embeddinggemma
_DEFAULT_EMBED_DIM = 768


# 1. Embedding Tests (Ollama 기반)
def test_get_embedding_success() -> None:
    """眞 (Truth): Ollama 임베딩 생성 성공 테스트"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.1, 0.2]}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_response):
        emb = get_embedding("test", None)
        assert emb == [0.1, 0.2]


def test_get_embedding_failure() -> None:
    """眞 (Truth): Ollama 임베딩 생성 실패 시 폴백 테스트"""
    with patch("requests.post", side_effect=Exception("API Error")):
        emb = get_embedding("test", None)
        assert len(emb) == _DEFAULT_EMBED_DIM  # Returns random embedding on failure (768D)


def test_get_embedding_no_client() -> None:
    """眞 (Truth): Ollama 직접 호출 테스트 (client 파라미터 무시)"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.5] * _DEFAULT_EMBED_DIM}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_response):
        emb: list[float] = get_embedding("test", None)
        assert len(emb) == _DEFAULT_EMBED_DIM


# 2. PGVector Query Tests (Manual Similarity)
def test_query_pgvector_logic() -> None:
    """眞 (Truth): PGVector 검색 로직 검증"""
    mock_pool: Any = MagicMock()
    mock_conn: Any = MagicMock()
    mock_cursor: Any = MagicMock()
    mock_pool.getconn.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    # Mock rows: [id, title, url, content, embedding]
    # Row 1: perfect match (emb=[1.0, 0.0])
    # Row 2: orthogonal (emb=[0.0, 1.0])
    mock_cursor.fetchall.return_value = [
        {"id": 1, "title": "A", "url": "u1", "content": "c1", "embedding": [1.0, 0.0]},
        {"id": 2, "title": "B", "url": "u2", "content": "c2", "embedding": [0.0, 1.0]},
    ]

    query_emb = [1.0, 0.0]

    # Patch register_vector to prevent it from trying to run SQL on mock_conn
    with patch("AFO.services.hybrid_rag.queries.register_vector", MagicMock()):
        results = query_pgvector(query_emb, top_k=2, pg_pool=mock_pool)

    assert len(results) == 2
    assert results[0]["id"] == "1"
    assert results[0]["score"] > 0.99
    assert results[1]["id"] == "2"
    assert results[1]["score"] < 0.01


def test_query_pgvector_failure() -> None:
    """眞 (Truth): PGVector 검색 실패 케이스 검증"""
    mock_pool: Any = MagicMock()
    # Trigger error INSIDE the try block (e.g., cursor) to test the exception handling -> return [] path
    mock_conn: Any = MagicMock()
    mock_pool.getconn.return_value = mock_conn
    mock_conn.cursor.side_effect = Exception("DB Cursor Error")

    results: list[dict[str, Any]] = query_pgvector([0.1], 5, mock_pool)
    assert results == []


# 3. Redis Query Tests
def test_query_redis_logic() -> None:
    """眞 (Truth): Redis 검색 로직 검증"""
    mock_client: Any = MagicMock()
    mock_search_result: Any = MagicMock()

    # Mock docs
    doc1: Any = MagicMock()
    doc1.id = "doc1"
    doc1.content = "c1"
    doc1.score = "0.1"  # distance? usually lower is better in vector search but hybrid_rag code treats score as similarity if higher?
    # Redis vector search usually returns distance.
    # But check hybrid_rag.py implementation:
    # It reads "score" from payload. And blends it.
    # Code assumes "score" comes from the query return field.

    # Let's assume standard score behavior (higher is better for similarity or hybrid_rag handles it)
    # The code takes `float(score_value)`.

    # Let's populate __dict__ for payload
    doc1.__dict__ = {"id": "doc1", "content": "c1", "score": "0.9"}

    mock_search_result.docs = [doc1]
    mock_client.ft.return_value.search.return_value = mock_search_result

    results = query_redis([0.1], 5, mock_client)

    assert len(results) == 1
    assert results[0]["id"] == "doc1"
    assert results[0]["score"] == 0.9


def test_query_redis_failure() -> None:
    """眞 (Truth): Redis 검색 실패 케이스 검증"""
    mock_client: Any = MagicMock()
    mock_client.ft.side_effect = Exception("Redis Error")
    results: list[dict[str, Any]] = query_redis([0.1], 5, mock_client)
    assert results == []


# 4. Blend Results
def test_blend_results() -> None:
    """美 (Beauty): 결과 혼합 로직 정합성 테스트"""
    pg_rows: list[dict[str, Any]] = [{"id": "1", "content": "c1", "score": 0.5}]
    redis_rows: list[dict[str, Any]] = [
        {"id": "1", "content": "c1", "score": 0.6},
        {"id": "2", "content": "c2", "score": 0.4},
    ]

    # pg boost is 1.1
    # pg row 1 score becomes 0.5 * 1.1 = 0.55
    # redis row 1 score is 0.6
    # so row 1 score should be max(0.55, 0.6) = 0.6

    merged: list[dict[str, Any]] = blend_results(pg_rows, redis_rows, top_k=2)

    assert len(merged) == 2
    assert merged[0]["id"] == "1"
    assert merged[0]["score"] == 0.6
    assert merged[1]["id"] == "2"


def test_select_context() -> None:
    """眞 (Truth): 컨텍스트 선별 로직(글자수 제한) 테스트"""
    rows: list[dict[str, Any]] = [
        {"content": "short"},  # len 5
        {"content": "very long content that exceeds limit"},  # len 34
    ]
    selected: list[dict[str, Any]] = select_context(rows, limit=10)

    assert len(selected) == 1
    assert selected[0]["content"] == "short"


# 5. Generate Answer (Ollama 기반)
def test_generate_answer_openai() -> None:
    """眞 (Truth): Ollama 기반 답변 생성 테스트 (openai_client 파라미터 무시)"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "Answer"}}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_response):
        ans: Union[str, dict[str, Any]] = generate_answer(
            "q", ["c1"], 0.7, "markdown", "", openai_client=None
        )
        assert ans == "Answer"


def test_generate_answer_no_client() -> None:
    """眞 (Truth): Ollama 직접 호출 테스트 (client 없어도 동작)"""
    mock_response = MagicMock()
    mock_response.json.return_value = {"message": {"content": "Ollama Response"}}
    mock_response.raise_for_status = MagicMock()

    with patch("requests.post", return_value=mock_response):
        ans: Union[str, dict[str, Any]] = generate_answer("q", [], 0.7, "", "", openai_client=None)
        assert ans == "Ollama Response"


# 6. Async Wrappers (Ollama 기반)
@pytest.mark.asyncio
async def test_async_wrappers() -> None:
    """眞 (Truth): 비동기 래퍼 동작 검증 (Ollama)"""
    from unittest.mock import AsyncMock

    # Test get_embedding_async with mocked httpx
    mock_response = MagicMock()
    mock_response.json.return_value = {"embedding": [0.1]}
    mock_response.raise_for_status = MagicMock()

    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        emb: list[float] = await get_embedding_async("test", None)
        assert emb == [0.1]

    # Test query_pgvector_async
    pool: Any = MagicMock()
    pool.getconn.return_value.cursor.return_value.__enter__.return_value.fetchall.return_value = []
    res: list[dict[str, Any]] = await query_pgvector_async([0.1], 5, pool)
    assert res == []
