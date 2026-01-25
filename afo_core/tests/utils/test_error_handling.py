"""
Tests for error_handling.py (Phase 70 - Coverage Crusade)
眞 (Truth): 정확한 에러 타입 및 메시지 검증
善 (Goodness): 안전한 에러 처리 및 복구
"""

import pytest

from AFO.utils.error_handling import (
    AFOError,
    BeautyError,
    EternityError,
    GoodnessError,
    SerenityError,
    TruthError,
    ValidationError,
    handle_async_errors,
    handle_errors,
    log_and_return_error,
    require_not_none,
    safe_execute,
    safe_execute_async,
    validate_input,
)


class TestAFOError:
    """AFOError 기본 에러 클래스 테스트"""

    def test_basic_error(self):
        error = AFOError("Test error")
        assert error.message == "Test error"
        assert error.error_code is None
        assert error.details == {}

    def test_error_with_code(self):
        error = AFOError("Test error", error_code="TEST_001")
        assert error.error_code == "TEST_001"

    def test_error_with_code_alias(self):
        error = AFOError("Test error", code="CODE_001")
        assert error.error_code == "CODE_001"

    def test_error_with_details(self):
        error = AFOError("Test error", details={"key": "value"})
        assert error.details == {"key": "value"}


class TestPillarErrors:
    """5기둥 전용 에러 클래스 테스트"""

    def test_truth_error(self):
        error = TruthError("Technical inaccuracy")
        assert isinstance(error, AFOError)

    def test_goodness_error(self):
        error = GoodnessError("Security concern")
        assert isinstance(error, AFOError)

    def test_beauty_error(self):
        error = BeautyError("Ugly code structure")
        assert isinstance(error, AFOError)

    def test_serenity_error(self):
        error = SerenityError("Friction detected")
        assert isinstance(error, AFOError)

    def test_eternity_error(self):
        error = EternityError("Non-persistent change")
        assert isinstance(error, AFOError)

    def test_validation_error(self):
        error = ValidationError("Input validation failed")
        assert isinstance(error, AFOError)


class TestHandleErrors:
    """handle_errors 데코레이터 테스트"""

    def test_no_error(self):
        @handle_errors()
        def simple_func():
            return 42

        result = simple_func()
        assert result == 42

    def test_error_with_logging(self, caplog):
        @handle_errors(log_error=True)
        def failing_func():
            raise ValueError("Test error")

        result = failing_func()
        assert result is None
        assert "Test error" in caplog.text

    def test_error_with_default_return(self):
        @handle_errors(default_return="fallback")
        def failing_func():
            raise ValueError("Test error")

        result = failing_func()
        assert result == "fallback"

    def test_reraise(self):
        @handle_errors(reraise=True, error_type=GoodnessError)
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(GoodnessError):
            failing_func()


class TestValidateInput:
    """입력값 검증 함수 테스트"""

    def test_valid_input(self):
        result = validate_input(10, "test_value", lambda x: x > 0)
        assert result == 10

    def test_invalid_input(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_input(-1, "test_value", lambda x: x > 0)

        assert "test_value" in str(exc_info.value)

    def test_custom_error_message(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_input(
                "invalid",
                "field",
                lambda x: False,
                error_message="Custom message",
            )

        assert "Custom message" in str(exc_info.value)


class TestRequireNotNone:
    """None 값 검증 함수 테스트"""

    def test_valid_value(self):
        result = require_not_none(42, "test_field")
        assert result == 42

    def test_none_value(self):
        with pytest.raises(ValidationError) as exc_info:
            require_not_none(None, "test_field")

        assert "test_field cannot be None" in str(exc_info.value)


class TestLogAndReturnError:
    """에러 로깅 함수 테스트"""

    def test_log_and_return(self, caplog):
        error = ValidationError("Test error", error_code="TEST_001")
        result = log_and_return_error(error, "test_context")

        assert result["success"] is False
        assert result["error_code"] == "TEST_001"
        assert result["error_message"] == "Test error"
        assert result["context"] == "test_context"
        assert "test_context" in caplog.text
