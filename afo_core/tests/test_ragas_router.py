# Trinity Score: 90.0 (Established by Chancellor)
"""
Ragas Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - ragas.py

眞 (Truth): RAG 평가 API 테스트
"""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Store original ragas module state for cleanup
_original_ragas = sys.modules.get("ragas")

# Mock ragas module before importing the router
_mock_ragas = MagicMock()
_mock_ragas.evaluate = MagicMock()
sys.modules["ragas"] = _mock_ragas

from api.routes.ragas import (
    RAGAS_METRICS,
    RagasEvalRequest,
    RagasEvalResponse,
    ragas_router,
)

# Restore original state after import (for test isolation)
if _original_ragas is not None:
    sys.modules["ragas"] = _original_ragas
else:
    # Keep mock but mark it for potential cleanup
    pass


class TestConstants:
    """상수 테스트"""

    def test_ragas_metrics_defined(self):
        """RAGAS_METRICS 정의 확인"""
        assert RAGAS_METRICS is not None
        assert len(RAGAS_METRICS) == 6
        assert "faithfulness" in RAGAS_METRICS
        assert "answer_relevancy" in RAGAS_METRICS
        assert "context_precision" in RAGAS_METRICS
        assert "context_recall" in RAGAS_METRICS
        assert "conciseness" in RAGAS_METRICS
        assert "coherence" in RAGAS_METRICS


class TestPydanticModels:
    """Pydantic 모델 테스트"""

    def test_ragas_eval_request_minimal(self):
        """최소 평가 요청"""
        request = RagasEvalRequest(dataset=[{"question": "q", "answer": "a"}])
        assert len(request.dataset) == 1
        assert request.metrics is None

    def test_ragas_eval_request_with_metrics(self):
        """메트릭 지정 요청"""
        request = RagasEvalRequest(
            dataset=[{"q": "q"}],
            metrics=["faithfulness", "coherence"],
        )
        assert len(request.metrics) == 2

    def test_ragas_eval_response(self):
        """평가 응답 생성"""
        response = RagasEvalResponse(
            scores={"faithfulness": 0.9, "coherence": 0.85},
            coverage=0.875,
            timestamp="2025-01-21T12:00:00",
        )
        assert response.scores["faithfulness"] == 0.9
        assert response.coverage == 0.875

    def test_ragas_eval_response_default_coverage(self):
        """기본 커버리지"""
        response = RagasEvalResponse(
            scores={},
            timestamp="2025-01-21T12:00:00",
        )
        assert response.coverage == 0.85  # Default


class TestRouterEndpoints:
    """라우터 존재 확인"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert ragas_router is not None
        assert ragas_router.prefix == "/api/ragas"

    def test_router_has_tags(self):
        """태그 확인"""
        assert "Ragas" in ragas_router.tags


class TestGetRedisClient:
    """_get_redis_client 함수 테스트"""

    @pytest.mark.asyncio
    async def test_redis_connection_success(self):
        """Redis 연결 성공"""
        from api.routes.ragas import _get_redis_client

        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(return_value=True)

        with patch("api.routes.ragas.redis.from_url", return_value=mock_client):
            with patch("api.routes.ragas.settings") as mock_settings:
                mock_settings.get_redis_url.return_value = "redis://localhost:6379"
                mock_settings.REDIS_TIMEOUT = 5

                client = await _get_redis_client()

                assert client is not None

    @pytest.mark.asyncio
    async def test_redis_connection_failure(self):
        """Redis 연결 실패"""
        from api.routes.ragas import _get_redis_client

        with patch("api.routes.ragas.redis.from_url") as mock_from_url:
            mock_from_url.side_effect = ConnectionError("Connection refused")

            with patch("api.routes.ragas.settings") as mock_settings:
                mock_settings.get_redis_url.return_value = "redis://localhost:6379"
                mock_settings.REDIS_TIMEOUT = 5

                client = await _get_redis_client()

                assert client is None


class TestEvaluateRagas:
    """evaluate_ragas 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_evaluate_mock_mode(self):
        """Mock 모드 평가"""
        from api.routes.ragas import evaluate_ragas

        request = RagasEvalRequest(
            dataset=[{"question": "q", "answer": "a"}],
            metrics=["faithfulness", "coherence"],
        )

        # Mock evaluate to return dict format
        with patch(
            "api.routes.ragas.evaluate", return_value={"faithfulness": 0.9, "coherence": 0.85}
        ):
            with patch("api.routes.ragas._get_redis_client", return_value=None):
                result = await evaluate_ragas(request)

        assert "faithfulness" in result.scores
        assert "coherence" in result.scores
        assert result.scores["faithfulness"] == 0.9

    @pytest.mark.asyncio
    async def test_evaluate_with_redis(self):
        """Redis 저장 포함 평가"""
        from api.routes.ragas import evaluate_ragas

        request = RagasEvalRequest(dataset=[{"q": "q"}])

        mock_redis = AsyncMock()
        mock_redis.hset = AsyncMock()

        with patch(
            "api.routes.ragas._get_redis_client",
            return_value=mock_redis,
        ):
            result = await evaluate_ragas(request)

        assert result.timestamp is not None
        mock_redis.hset.assert_called()

    @pytest.mark.asyncio
    async def test_evaluate_all_metrics(self):
        """전체 메트릭 평가"""
        from api.routes.ragas import evaluate_ragas

        request = RagasEvalRequest(dataset=[{"q": "q"}])  # No metrics = all

        # Mock evaluate to return all 6 metrics
        all_scores = {metric: 0.85 for metric in RAGAS_METRICS}
        with patch("api.routes.ragas.evaluate", return_value=all_scores):
            with patch("api.routes.ragas._get_redis_client", return_value=None):
                result = await evaluate_ragas(request)

        # Should have all 6 metrics
        assert len(result.scores) == 6


class TestBenchmarkRagas:
    """benchmark_ragas 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_benchmark_response(self):
        """벤치마크 응답"""
        from api.routes.ragas import benchmark_ragas

        request = RagasEvalRequest(dataset=[{"q": "q"}])

        with patch("api.routes.ragas._get_redis_client", return_value=None):
            result = await benchmark_ragas(request)

        assert "benchmark" in result
        assert "baseline" in result
        assert result["baseline"] == 0.80
        assert "improvement" in result

    @pytest.mark.asyncio
    async def test_benchmark_improvement_calculation(self):
        """개선도 계산"""
        from api.routes.ragas import benchmark_ragas

        request = RagasEvalRequest(
            dataset=[{"q": "q"}],
            metrics=["faithfulness"],  # Single metric for easier calculation
        )

        with patch("api.routes.ragas._get_redis_client", return_value=None):
            result = await benchmark_ragas(request)

        # Mock score is 0.85, baseline is 0.80, so improvement is 0.05
        assert result["improvement"] == pytest.approx(0.05, abs=0.01)


class TestGetRagasMetrics:
    """get_ragas_metrics 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_metrics_no_redis(self):
        """Redis 없이 메트릭 조회"""
        from api.routes.ragas import get_ragas_metrics

        with patch("api.routes.ragas._get_redis_client", return_value=None):
            result = await get_ragas_metrics()

        assert "metrics" in result
        assert "available_metrics" in result
        assert result["timestamp"] is None
        # All metrics should be 0.0 (default)
        for metric in RAGAS_METRICS:
            assert result["metrics"][metric] == 0.0

    @pytest.mark.asyncio
    async def test_metrics_from_redis(self):
        """Redis에서 메트릭 조회"""
        from api.routes.ragas import get_ragas_metrics

        mock_redis = AsyncMock()
        mock_redis.hgetall = AsyncMock(
            return_value={
                "faithfulness": "0.92",
                "coherence": "0.88",
                "timestamp": "2025-01-21T12:00:00",
            }
        )

        with patch(
            "api.routes.ragas._get_redis_client",
            return_value=mock_redis,
        ):
            result = await get_ragas_metrics()

        assert result["metrics"]["faithfulness"] == 0.92
        assert result["metrics"]["coherence"] == 0.88
        assert result["timestamp"] == "2025-01-21T12:00:00"

    @pytest.mark.asyncio
    async def test_metrics_redis_error(self):
        """Redis 에러 처리"""
        from api.routes.ragas import get_ragas_metrics

        mock_redis = AsyncMock()
        mock_redis.hgetall = AsyncMock(side_effect=ConnectionError("Redis error"))

        with patch(
            "api.routes.ragas._get_redis_client",
            return_value=mock_redis,
        ):
            result = await get_ragas_metrics()

        # Should return defaults on error
        assert "metrics" in result
        assert all(v == 0.0 for v in result["metrics"].values())

    @pytest.mark.asyncio
    async def test_available_metrics_list(self):
        """사용 가능한 메트릭 목록"""
        from api.routes.ragas import get_ragas_metrics

        with patch("api.routes.ragas._get_redis_client", return_value=None):
            result = await get_ragas_metrics()

        assert result["available_metrics"] == RAGAS_METRICS
