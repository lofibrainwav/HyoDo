# Trinity Score: 90.0 (Established by Chancellor)
"""
KimYuSin Escalation Pattern Tests

Bottom-Up LLM 오케스트레이션 전략 검증:
- Vision 2단계 선택 (화타)
- Coder 에스컬레이션 (사마휘 → 좌자)
- Trinity Score 기반 품질 평가
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from infrastructure.llm.model_routing import (
    DEFAULT_ESCALATION_THRESHOLD,
    ModelConfig,
    TaskType,
    get_escalation_threshold,
    get_vision_model,
    should_escalate,
)
from scholars.kim_yu_sin import KimYuSinScholar
from scholars.kim_yu_sin.evaluator import QualityEvaluator
from scholars.kim_yu_sin.sages import ThreeSages

# Create a global instance for tests
kim_yu_sin = KimYuSinScholar()

# Create evaluator shortcut for backward-compatible test access
# Tests use kim_yu_sin._evaluate_* but the methods are on QualityEvaluator
kim_yu_sin._evaluate_response_quality = QualityEvaluator.evaluate_response_quality
kim_yu_sin._evaluate_code_quality = QualityEvaluator.evaluate_code_quality

# ============================================================================
# Model Routing Escalation Tests
# ============================================================================


class TestEscalationThreshold:
    """에스컬레이션 임계값 테스트"""

    def test_default_escalation_threshold_is_90(self) -> None:
        """SSOT: 기본 에스컬레이션 임계값은 90"""
        assert DEFAULT_ESCALATION_THRESHOLD == 90.0

    def test_task_specific_thresholds(self) -> None:
        """Task-specific thresholds are configured"""
        # OPTIMIZATION: CHAT threshold increased for Beauty Score improvement (was 88.0)
        assert get_escalation_threshold(TaskType.CHAT) == 92.0
        assert get_escalation_threshold(TaskType.VISION) == 90.0
        # OPTIMIZATION: CODE_GENERATE threshold lowered for quality (was 92.0)
        assert get_escalation_threshold(TaskType.CODE_GENERATE) == 90.0
        assert get_escalation_threshold(TaskType.DOCUMENT) == 85.0
        # Bypass cases (threshold 0.0)
        assert get_escalation_threshold(TaskType.REASONING) == 0.0
        assert get_escalation_threshold(TaskType.CODE_REVIEW) == 0.0
        assert get_escalation_threshold(TaskType.EMBED) == 0.0

    @pytest.mark.parametrize(
        ("trinity_score", "task_type", "expected"),
        [
            # 높은 점수 - 에스컬레이션 불필요
            (95.0, TaskType.CHAT, False),
            (92.0, TaskType.CHAT, False),  # CHAT threshold is 92.0 (optimized)
            (92.0, TaskType.VISION, False),  # VISION threshold is 90.0
            (90.0, TaskType.CHAT, True),  # 90.0 < 92.0 (CHAT threshold - needs escalation)
            # 낮은 점수 - 에스컬레이션 필요 (task-specific thresholds)
            (91.9, TaskType.CHAT, True),  # Below 92.0
            (89.9, TaskType.VISION, True),  # Below 90.0
            (89.9, TaskType.CODE_GENERATE, True),  # Below 90.0 (optimized)
            (84.9, TaskType.DOCUMENT, True),  # Below 85.0
            # 이미 최상위 모델 - 에스컬레이션 불필요 (bypass)
            (50.0, TaskType.REASONING, False),
            (60.0, TaskType.CODE_REVIEW, False),
            (70.0, TaskType.EMBED, False),
        ],
    )
    def test_should_escalate(
        self,
        trinity_score: float,
        task_type: TaskType,
        expected: bool,
    ) -> None:
        """should_escalate 함수 테스트 (task-specific thresholds)"""
        result = should_escalate(trinity_score, task_type)
        assert result == expected


class TestVisionModelSelection:
    """Vision 2단계 모델 선택 테스트"""

    def test_vision_stage1_no_score(self) -> None:
        """Trinity Score 없으면 Stage 1 (빠른 모델)"""
        model, stage = get_vision_model(None)
        assert model == ModelConfig.HEO_JUN_FAST
        assert "Stage 1" in stage

    def test_vision_stage1_high_score(self) -> None:
        """높은 점수면 Stage 1 유지"""
        model, stage = get_vision_model(95.0)
        assert model == ModelConfig.HEO_JUN_FAST
        assert "Sufficient" in stage

    def test_vision_stage2_low_score(self) -> None:
        """낮은 점수면 Stage 2 (정밀 모델)"""
        model, stage = get_vision_model(85.0)
        assert model == ModelConfig.HEO_JUN
        assert "Stage 2" in stage

    @pytest.mark.parametrize(
        ("trinity_score", "expected_model"),
        [
            (None, ModelConfig.HEO_JUN_FAST),
            (100.0, ModelConfig.HEO_JUN_FAST),
            (90.0, ModelConfig.HEO_JUN_FAST),
            (89.9, ModelConfig.HEO_JUN),
            (80.0, ModelConfig.HEO_JUN),
            (50.0, ModelConfig.HEO_JUN),
            (0.0, ModelConfig.HEO_JUN),
        ],
    )
    def test_vision_model_boundary(
        self,
        trinity_score: float | None,
        expected_model: str,
    ) -> None:
        """Vision 모델 선택 경계값 테스트"""
        model, _ = get_vision_model(trinity_score)
        assert model == expected_model


# ============================================================================
# KimYuSinScholar Constants Tests
# ============================================================================


class TestKimYuSinConstants:
    """KimYuSinScholar 상수 테스트"""

    def test_sage_models_defined(self) -> None:
        """3현사 모델 상수 정의 확인"""
        assert ThreeSages.SAGE_JEONG_YAK_YONG == "qwen2.5-coder:7b"
        assert ThreeSages.SAGE_RYU_SEONG_RYONG == "deepseek-r1:14b"
        assert ThreeSages.SAGE_HEO_JUN == "qwen3-vl:latest"
        assert ThreeSages.SAGE_HEO_JUN_FAST == "qwen3-vl:2b"

    def test_hwata_fast_is_different_from_hwata(self) -> None:
        """HEO_JUN_FAST는 HEO_JUN와 다른 모델"""
        assert ThreeSages.SAGE_HEO_JUN_FAST != ThreeSages.SAGE_HEO_JUN


# ============================================================================
# Quality Evaluation Tests
# ============================================================================


class TestResponseQualityEvaluation:
    """응답 품질 평가 테스트"""

    def test_short_response_penalty(self) -> None:
        """짧은 응답은 감점"""
        score = kim_yu_sin._evaluate_response_quality("짧은 응답", "질문")
        assert score < 80.0

    def test_long_response_bonus(self) -> None:
        """긴 응답은 가점"""
        long_response = "이것은 매우 긴 응답입니다. " * 20
        score = kim_yu_sin._evaluate_response_quality(long_response, "질문")
        assert score >= 85.0

    def test_error_response_penalty(self) -> None:
        """오류 메시지 포함시 감점"""
        error_response = "처리 실패: 연결 오류가 발생했습니다."
        score = kim_yu_sin._evaluate_response_quality(error_response, "질문")
        assert score < 70.0

    def test_structured_response_bonus(self) -> None:
        """구조화된 응답은 가점"""
        structured = """
        응답 내용:
        - 첫 번째 항목
        - 두 번째 항목
        - 세 번째 항목
        """
        score = kim_yu_sin._evaluate_response_quality(structured, "질문")
        assert score >= 85.0

    def test_keyword_overlap_bonus(self) -> None:
        """쿼리 키워드 포함시 가점"""
        query = "Python FastAPI 설명해줘"
        # 충분히 긴 응답 + 구조화 + 키워드 오버랩 = 80 + 5(길이) + 5(구조) + 5(오버랩) = 95
        # 키워드가 정확히 일치하도록 띄어쓰기 조정 (Python, FastAPI)
        response = """
        Python 과 FastAPI 는 웹 개발에 사용되는 도구입니다.
        - FastAPI 는 빠른 성능을 제공합니다.
        - Python 의 타입 힌트를 활용하여 자동 문서화를 지원합니다.
        비동기 처리도 지원하여 높은 처리량을 달성할 수 있습니다.
        설명해줘 라고 요청하신 내용에 대한 답변입니다.
        """
        score = kim_yu_sin._evaluate_response_quality(response, query)
        # 80 + 5(구조 "- ") + 5(키워드 overlap >= 2) = 90
        assert score >= 85.0


class TestCodeQualityEvaluation:
    """코드 품질 평가 테스트"""

    def test_code_block_bonus(self) -> None:
        """코드 블록 포함시 가점"""
        response = """
        다음은 예제 코드입니다:
        ```python
        def hello():
            return "Hello"
        ```
        """
        score = kim_yu_sin._evaluate_code_quality(response, "함수 만들어줘")
        assert score >= 90.0

    def test_python_code_extra_bonus(self) -> None:
        """Python 코드 패턴 감지시 추가 가점"""
        response = """
        ```python
        class MyClass:
            def __init__(self):
                pass
        ```
        """
        score = kim_yu_sin._evaluate_code_quality(response, "클래스 구현해줘")
        assert score >= 95.0

    def test_syntax_error_penalty(self) -> None:
        """SyntaxError 포함시 감점"""
        response = "SyntaxError: invalid syntax at line 10"
        score = kim_yu_sin._evaluate_code_quality(response, "코드 작성해줘")
        assert score < 70.0

    def test_short_code_response_penalty(self) -> None:
        """너무 짧은 코드 응답은 감점"""
        response = "def f(): pass"
        score = kim_yu_sin._evaluate_code_quality(response, "함수 만들어줘")
        assert score < 80.0

    def test_docstring_bonus(self) -> None:
        """독스트링 포함시 가점"""
        response = '''
        ```python
        def calculate(x, y):
            """
            두 수를 계산합니다.

            Args:
                x: 첫 번째 수
                y: 두 번째 수
            """
            return x + y
        ```
        '''
        score = kim_yu_sin._evaluate_code_quality(response, "함수 작성해줘")
        assert score >= 90.0


# ============================================================================
# Consult Method Escalation Tests (Mocked)
# ============================================================================


class TestConsultHwataEscalation:
    """화타 상담 에스컬레이션 테스트"""

    @pytest.mark.asyncio
    async def test_consult_hwata_no_score_uses_fast_model(self) -> None:
        """Trinity Score 없으면 빠른 모델 사용"""
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = "테스트 응답"
            await kim_yu_sin.consult_hwata("테스트 질문")

            # 빠른 모델(2b) 사용 확인
            call_args = mock.call_args
            assert call_args.kwargs["model_id"] == ThreeSages.SAGE_HEO_JUN_FAST

    @pytest.mark.asyncio
    async def test_consult_hwata_high_score_uses_fast_model(self) -> None:
        """높은 Trinity Score면 빠른 모델 유지"""
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = "테스트 응답"
            await kim_yu_sin.consult_hwata("테스트 질문", trinity_score=95.0)

            call_args = mock.call_args
            assert call_args.kwargs["model_id"] == ThreeSages.SAGE_HEO_JUN_FAST

    @pytest.mark.asyncio
    async def test_consult_hwata_low_score_uses_precise_model(self) -> None:
        """낮은 Trinity Score면 정밀 모델 사용"""
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = "테스트 응답"
            await kim_yu_sin.consult_hwata("테스트 질문", trinity_score=80.0)

            call_args = mock.call_args
            assert call_args.kwargs["model_id"] == ThreeSages.SAGE_HEO_JUN

    @pytest.mark.asyncio
    async def test_consult_hwata_force_precise(self) -> None:
        """force_precise=True면 정밀 모델 강제 사용"""
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = "테스트 응답"
            await kim_yu_sin.consult_hwata("테스트 질문", force_precise=True)

            call_args = mock.call_args
            assert call_args.kwargs["model_id"] == ThreeSages.SAGE_HEO_JUN


class TestConsultHwataWithEscalation:
    """화타 자동 에스컬레이션 테스트"""

    @pytest.mark.asyncio
    async def test_high_quality_response_no_escalation(self) -> None:
        """품질 좋은 응답은 에스컬레이션 없음"""
        # 충분히 긴 응답 + 구조화 + 이미지/분석 키워드 포함 = 80 + 5(길이) + 5(구조) + 5(키워드) = 95
        good_response = """
        이미지 분석 결과입니다. 다음은 상세한 분석 내용입니다.

        1. 해상도: 1920x1080 픽셀의 고해상도 이미지입니다.
        2. 색상 분석: RGB 색상 공간을 사용하며 밝은 톤이 지배적입니다.
        3. 주요 객체 감지:
           - 사람: 2명 감지됨
           - 건물: 배경에 고층 빌딩 존재
           - 자동차: 도로에 여러 대 위치

        전반적으로 고품질의 도시 풍경 이미지입니다. 노출과 화이트밸런스가 적절하게 설정되어 있습니다.
        """
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = good_response
            _, score, is_escalated = await kim_yu_sin.consult_hwata_with_escalation(
                "이미지 분석해줘"
            )

            assert is_escalated is False
            assert score is not None
            assert score >= DEFAULT_ESCALATION_THRESHOLD

    @pytest.mark.asyncio
    async def test_low_quality_response_triggers_escalation(self) -> None:
        """품질 낮은 응답은 에스컬레이션 발생"""
        bad_response = "오류"
        good_response = "상세한 분석 결과입니다. 이미지에서 다양한 요소를 발견했습니다."

        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            # 첫 번째 호출(Stage 1)은 나쁜 응답, 두 번째 호출(Stage 2)은 좋은 응답
            mock.side_effect = [bad_response, good_response]

            (
                result_response,
                result_score,
                is_escalated,
            ) = await kim_yu_sin.consult_hwata_with_escalation("이미지 분석해줘")

            assert is_escalated is True
            assert result_score is not None
            assert result_score < DEFAULT_ESCALATION_THRESHOLD
            assert result_response == good_response
            assert mock.call_count == 2


class TestConsultSamahwiEscalation:
    """사마휘 상담 에스컬레이션 테스트"""

    @pytest.mark.asyncio
    async def test_consult_samahwi_no_score_uses_coder(self) -> None:
        """Trinity Score 없으면 코더 모델 사용"""
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = "테스트 응답"
            await kim_yu_sin.consult_samahwi("함수 만들어줘")

            call_args = mock.call_args
            assert call_args.kwargs["model_id"] == ThreeSages.SAGE_JEONG_YAK_YONG

    @pytest.mark.asyncio
    async def test_consult_samahwi_low_score_escalates_to_jwaja(self) -> None:
        """낮은 Trinity Score면 좌자로 에스컬레이션"""
        with patch.object(kim_yu_sin.sages, "consult_jwaja", new_callable=AsyncMock) as mock_jwaja:
            mock_jwaja.return_value = "좌자 응답"
            response = await kim_yu_sin.consult_samahwi("복잡한 알고리즘", trinity_score=70.0)

            assert response == "좌자 응답"
            mock_jwaja.assert_called_once()

    @pytest.mark.asyncio
    async def test_consult_samahwi_force_escalate(self) -> None:
        """force_escalate=True면 좌자로 강제 에스컬레이션"""
        with patch.object(kim_yu_sin.sages, "consult_jwaja", new_callable=AsyncMock) as mock_jwaja:
            mock_jwaja.return_value = "좌자 응답"
            response = await kim_yu_sin.consult_samahwi("간단한 질문", force_escalate=True)

            assert response == "좌자 응답"
            mock_jwaja.assert_called_once()


class TestConsultSamahwiWithEscalation:
    """사마휘 자동 에스컬레이션 테스트"""

    @pytest.mark.asyncio
    async def test_good_code_no_escalation(self) -> None:
        """좋은 코드 응답은 에스컬레이션 없음"""
        good_code = '''
        다음은 요청하신 함수입니다:
        ```python
        def calculate_sum(numbers: list[int]) -> int:
            """
            숫자 리스트의 합계를 계산합니다.

            Args:
                numbers: 정수 리스트

            Returns:
                합계
            """
            return sum(numbers)
        ```
        '''
        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.return_value = good_code
            _, result_score, is_escalated = await kim_yu_sin.consult_samahwi_with_escalation(
                "함수 만들어줘"
            )

            assert is_escalated is False
            assert result_score >= DEFAULT_ESCALATION_THRESHOLD

    @pytest.mark.asyncio
    async def test_bad_code_triggers_escalation(self) -> None:
        """나쁜 코드 응답은 에스컬레이션 발생"""
        bad_code = "오류 발생"
        good_code = """
        ```python
        def solution():
            # 상세한 구현
            pass
        ```
        """

        with (
            patch.object(
                kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock
            ) as mock_sage,
            patch.object(kim_yu_sin.sages, "consult_jwaja", new_callable=AsyncMock) as mock_jwaja,
        ):
            mock_sage.return_value = bad_code
            mock_jwaja.return_value = good_code

            (
                result_response,
                result_score,
                is_escalated,
            ) = await kim_yu_sin.consult_samahwi_with_escalation("함수 만들어줘")

            assert is_escalated is True
            assert result_score < DEFAULT_ESCALATION_THRESHOLD
            assert result_response == good_code
            mock_jwaja.assert_called_once()


# ============================================================================
# Integration-like Tests (Still Mocked but Full Flow)
# ============================================================================


class TestEscalationFlow:
    """에스컬레이션 전체 흐름 테스트"""

    @pytest.mark.asyncio
    async def test_vision_escalation_flow(self) -> None:
        """Vision 에스컬레이션 전체 흐름"""
        # Stage 1: 짧은 응답 (낮은 품질)
        stage1_response = "이미지입니다."
        # Stage 2: 상세한 응답 (높은 품질)
        stage2_response = """
        이미지 분석 결과:
        - 해상도: 1920x1080
        - 색상: RGB
        - 주요 객체: 사람, 건물, 자동차
        - 배경: 도시 풍경
        전반적으로 고품질 사진입니다.
        """

        with patch.object(kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock) as mock:
            mock.side_effect = [stage1_response, stage2_response]

            result_response, _, is_escalated = await kim_yu_sin.consult_hwata_with_escalation(
                "이미지 분석해줘"
            )

            # Stage 1 응답이 낮은 품질이므로 에스컬레이션 발생
            assert is_escalated is True
            # 최종 응답은 Stage 2 응답
            assert result_response == stage2_response
            # 2번 호출됨 (Stage 1 + Stage 2)
            assert mock.call_count == 2

    @pytest.mark.asyncio
    async def test_coder_escalation_flow(self) -> None:
        """Coder 에스컬레이션 전체 흐름"""
        # Stage 1: 오류 포함 응답
        stage1_response = "SyntaxError: 코드에 오류가 있습니다."
        # Stage 2 (좌자): 정상 응답
        stage2_response = '''
        ```python
        def solution(data):
            """정확한 해결책"""
            return processed_data
        ```
        '''

        with (
            patch.object(
                kim_yu_sin.sages, "_consult_sage_core", new_callable=AsyncMock
            ) as mock_sage,
            patch.object(kim_yu_sin.sages, "consult_jwaja", new_callable=AsyncMock) as mock_jwaja,
        ):
            mock_sage.return_value = stage1_response
            mock_jwaja.return_value = stage2_response

            result_response, _, is_escalated = await kim_yu_sin.consult_samahwi_with_escalation(
                "함수 구현해줘"
            )

            assert is_escalated is True
            assert result_response == stage2_response
            # 좌자로 에스컬레이션됨
            mock_jwaja.assert_called_once()


# ============================================================================
# Boundary Tests
# ============================================================================


class TestBoundaryConditions:
    """경계 조건 테스트"""

    def test_trinity_score_exactly_at_threshold(self) -> None:
        """Trinity Score가 정확히 임계값일 때 (task-specific)"""
        # CHAT threshold is 92.0 (optimized), so 92.0 should not escalate
        assert should_escalate(92.0, TaskType.CHAT) is False
        # VISION threshold is 90.0, so 90.0 should not escalate
        assert should_escalate(90.0, TaskType.VISION) is False
        # CODE_GENERATE threshold is 90.0 (optimized), so 90.0 should not escalate
        assert should_escalate(90.0, TaskType.CODE_GENERATE) is False

    def test_trinity_score_just_below_threshold(self) -> None:
        """Trinity Score가 임계값 바로 아래일 때 (task-specific)"""
        # CHAT threshold is 92.0 (optimized), so 91.99 should escalate
        assert should_escalate(91.99, TaskType.CHAT) is True
        # VISION threshold is 90.0, so 89.99 should escalate
        assert should_escalate(89.99, TaskType.VISION) is True
        # CODE_GENERATE threshold is 90.0 (optimized), so 89.99 should escalate
        assert should_escalate(89.99, TaskType.CODE_GENERATE) is True

    def test_empty_response_quality(self) -> None:
        """빈 응답 품질 평가"""
        score = kim_yu_sin._evaluate_response_quality("", "질문")
        assert score < 70.0  # 매우 낮은 점수

    def test_very_long_response_quality(self) -> None:
        """매우 긴 응답 품질 평가"""
        long_response = "응답 내용 " * 1000
        score = kim_yu_sin._evaluate_response_quality(long_response, "질문")
        assert score >= 85.0  # 길이 보너스


# ============================================================================
# Self-Test Runner
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
