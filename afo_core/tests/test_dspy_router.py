# Trinity Score: 90.0 (Established by Chancellor)
"""
DSPy Router Tests
TICKET-150: 0% 커버리지 모듈 테스트 - dspy.py

眞 (Truth): DSPy MIPROv2 최적화 API 테스트
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from api.routes.dspy import (
    MIPROv2Optimizer,
    OptimizationRequest,
    OptimizationResponse,
    _default_trinity_metric,
    router,
)
from fastapi import HTTPException


class TestPydanticModels:
    """Pydantic 모델 테스트"""

    def test_optimization_request_defaults(self):
        """기본값이 있는 최적화 요청"""
        request = OptimizationRequest(task="Test task", dataset=[])
        assert request.task == "Test task"
        assert request.num_candidates == 10
        assert request.max_bootstrapped_demos == 4
        assert request.num_trials == 20
        assert request.use_context7 is True
        assert request.use_skills is True

    def test_optimization_request_custom(self):
        """사용자 정의 최적화 요청"""
        request = OptimizationRequest(
            task="Custom",
            dataset=[{"q": "q", "a": "a"}],
            num_candidates=5,
            max_bootstrapped_demos=2,
            num_trials=10,
            use_context7=False,
            use_skills=False,
        )
        assert request.num_candidates == 5
        assert request.use_context7 is False

    def test_optimization_response(self):
        """최적화 응답 생성"""
        response = OptimizationResponse(
            optimized_prompt={"prompt": "test"},
            trinity_score={"truth": 0.9, "goodness": 0.85},
            execution_time=10.5,
            trials_completed=20,
            best_score=0.9,
        )
        assert response.execution_time == 10.5
        assert response.best_score == 0.9


class TestRouterEndpoints:
    """라우터 존재 확인"""

    def test_router_exists(self):
        """라우터 존재 확인"""
        assert router is not None
        assert router.prefix == "/dspy"

    def test_router_has_tags(self):
        """태그 확인"""
        assert "DSPy Optimization" in router.tags


class TestDefaultTrinityMetric:
    """_default_trinity_metric 함수 테스트"""

    def test_overlap_scoring(self):
        """중복 단어 기반 점수"""
        score = _default_trinity_metric("hello world test", "hello world")
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Some overlap expected

    def test_no_overlap(self):
        """중복 없음"""
        score = _default_trinity_metric("abc", "xyz")
        assert score == 0.0

    def test_empty_target(self):
        """빈 타겟"""
        score = _default_trinity_metric("hello", "")
        assert score == 0.5  # Default for empty

    def test_full_overlap(self):
        """완전 중복"""
        score = _default_trinity_metric("hello world", "hello world")
        assert score == 1.0


class TestMIPROv2Optimizer:
    """MIPROv2Optimizer 클래스 테스트"""

    def test_optimizer_initialization(self):
        """옵티마이저 초기화"""
        with patch("api.routes.dspy.Context7Manager"):
            with patch("api.routes.dspy.SkillRegistry"):
                with patch("api.routes.dspy.TrinityMetricWrapper"):
                    optimizer = MIPROv2Optimizer()
                    assert optimizer is not None

    def test_prepare_dataset_empty(self):
        """빈 데이터셋 준비"""
        with patch("api.routes.dspy.Context7Manager"):
            with patch("api.routes.dspy.SkillRegistry"):
                with patch("api.routes.dspy.TrinityMetricWrapper"):
                    with patch("api.routes.dspy.DSPY_AVAILABLE", False):
                        optimizer = MIPROv2Optimizer()
                        result = optimizer.prepare_dataset([])
                        assert result == []

    def test_trinity_metric_function(self):
        """Trinity 메트릭 함수"""
        with patch("api.routes.dspy.Context7Manager"):
            with patch("api.routes.dspy.SkillRegistry"):
                mock_wrapper = MagicMock()
                mock_wrapper.calculate_trinity_score.return_value = {
                    "truth": 0.9,
                    "goodness": 0.85,
                    "beauty": 0.8,
                    "serenity": 0.9,
                    "eternity": 0.95,
                }

                with patch(
                    "api.routes.dspy.TrinityMetricWrapper",
                    return_value=mock_wrapper,
                ):
                    optimizer = MIPROv2Optimizer()

                    # Mock example and prediction
                    example = MagicMock()
                    example.question = "test question"
                    prediction = MagicMock()
                    prediction.answer = "test answer"

                    score = optimizer.trinity_metric_function(example, prediction)

                    assert 0.0 <= score <= 1.0

    def test_trinity_metric_function_exception(self):
        """Trinity 메트릭 함수 예외 처리"""
        with patch("api.routes.dspy.Context7Manager"):
            with patch("api.routes.dspy.SkillRegistry"):
                mock_wrapper = MagicMock()
                mock_wrapper.calculate_trinity_score.side_effect = RuntimeError("Error")

                with patch(
                    "api.routes.dspy.TrinityMetricWrapper",
                    return_value=mock_wrapper,
                ):
                    optimizer = MIPROv2Optimizer()
                    example = MagicMock()
                    prediction = MagicMock()

                    score = optimizer.trinity_metric_function(example, prediction)
                    assert score == 0.5  # Neutral score on error


class TestOptimizeEndpoint:
    """optimize_prompt 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_insufficient_data(self):
        """데이터 부족"""
        from api.routes.dspy import optimize_prompt

        request = OptimizationRequest(
            task="Test",
            dataset=[{"question": "q1", "answer": "a1"}],  # Only 1 item
        )
        background_tasks = MagicMock()

        with patch("api.routes.dspy.optimizer") as mock_optimizer:
            mock_optimizer.context7.get_relevant_context = AsyncMock(return_value=[])
            mock_optimizer.create_task_module.return_value = MagicMock()
            mock_optimizer.prepare_dataset.return_value = [MagicMock()]  # Less than 5

            with pytest.raises(HTTPException) as exc_info:
                await optimize_prompt(request, background_tasks)

            assert exc_info.value.status_code == 400
            assert "Insufficient" in exc_info.value.detail


class TestStatusEndpoint:
    """get_optimization_status 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_status_response(self):
        """상태 응답"""
        from api.routes.dspy import get_optimization_status

        with patch("api.routes.dspy.DSPY_AVAILABLE", True):
            with patch("api.routes.dspy.optimizer") as mock_optimizer:
                mock_optimizer.lm = MagicMock()  # LLM configured

                result = await get_optimization_status()

                assert result["dspy_available"] is True
                assert result["llm_configured"] is True
                assert result["context7_available"] is True

    @pytest.mark.asyncio
    async def test_status_no_llm(self):
        """LLM 미설정 상태"""
        from api.routes.dspy import get_optimization_status

        with patch("api.routes.dspy.DSPY_AVAILABLE", False):
            with patch("api.routes.dspy.optimizer") as mock_optimizer:
                mock_optimizer.lm = None

                result = await get_optimization_status()

                assert result["dspy_available"] is False
                assert result["llm_configured"] is False


class TestExamplesEndpoint:
    """get_example_requests 엔드포인트 테스트"""

    @pytest.mark.asyncio
    async def test_examples_response(self):
        """예제 응답"""
        from api.routes.dspy import get_example_requests

        result = await get_example_requests()

        assert "examples" in result
        assert len(result["examples"]) > 0
        assert "task" in result["examples"][0]
        assert "dataset" in result["examples"][0]


class TestSaveOptimizationResult:
    """save_optimization_result 함수 테스트"""

    @pytest.mark.asyncio
    async def test_save_success(self):
        """저장 성공"""
        from api.routes.dspy import save_optimization_result

        with patch("api.routes.dspy.Path") as mock_path:
            mock_path.return_value.mkdir = MagicMock()

            # Mock file open
            with patch("builtins.open", MagicMock()):
                await save_optimization_result(
                    task="test",
                    result={"optimized_module": {}, "execution_time": 1.0},
                    trinity_scores={"truth": 0.9},
                )

    @pytest.mark.asyncio
    async def test_save_exception(self):
        """저장 예외"""
        from api.routes.dspy import save_optimization_result

        with patch("builtins.open", side_effect=IOError("Write error")):
            # Should not raise, just log
            await save_optimization_result(
                task="test",
                result={},
                trinity_scores={},
            )


class TestModuleExports:
    """모듈 exports 테스트"""

    def test_all_exports(self):
        """__all__ 확인"""
        from api.routes import dspy as module

        assert "MIPROv2Optimizer" in module.__all__
        assert "optimize_prompt" in module.__all__
        assert "router" in module.__all__
