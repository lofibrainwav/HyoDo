# Trinity Score: 90.0 (Established by Chancellor)
"""善·孝 유틸리티 테스트"""

from typing import Any

import pytest
from utils.automation import RetryConfig, auto_retry, cache_result
from utils.error_handling import (
    AFOError,
    ValidationError,
    log_and_return_error,
    require_not_none,
    safe_execute,
    validate_input,
)


class TestErrorHandling:
    """善 에러 처리 테스트"""

    def test_safe_execute_success(self) -> None:
        """정상 실행 테스트 (Decorator Pattern)"""

        @safe_execute
        def multiply(x) -> None:
            return x * 2

        result = multiply(5)
        # safe_execute in error_handling.py returns RAW result
        assert result == 10

    def test_safe_execute_failure_with_default(self) -> None:
        """실패 시 안전 폴백 테스트"""

        @safe_execute
        def failing_func() -> None:
            raise ValueError("Test error")

        # To test default behavior, we must manually wrap with default since decorator syntax doesn't support arg binding in this implementation easily without partial
        # Or just verify that the wrapper catches error and returns default=None (default default)

        result = failing_func()
        assert result is None

        # precise test with specific default
        def failing_func_2() -> None:
            raise ValueError("Test error 2")

        wrapped = safe_execute(failing_func_2, default="fallback", log_error=False)
        assert wrapped() == "fallback"

    def test_validate_input_success(self) -> None:
        """입력 검증 성공 테스트"""
        api_key = "sk-test123"
        result = validate_input(api_key, "api_key", lambda k: k.startswith("sk-"))
        assert result == api_key

    def test_validate_input_failure(self) -> None:
        """입력 검증 실패 테스트"""
        with pytest.raises(ValidationError):
            validate_input("invalid", "api_key", lambda k: k.startswith("sk-"))

    def test_require_not_none_success(self) -> None:
        """None 검증 성공 테스트"""
        value = require_not_none("test", "param")
        assert value == "test"

    def test_require_not_none_failure(self) -> None:
        """None 검증 실패 테스트"""
        with pytest.raises(ValidationError):
            require_not_none(None, "param")

    def test_log_and_return_error(self) -> None:
        """에러 응답 생성 테스트"""
        error = AFOError("Test error", code="TEST_CODE")
        result = log_and_return_error(error, "test_context")
        assert result["success"] is False
        assert result["error_code"] == "TEST_CODE"


class TestAutomation:
    """孝 자동화 테스트"""

    def test_auto_retry_success(self) -> None:
        """재시도 성공 테스트"""
        call_count = 0

        @auto_retry(RetryConfig(max_retries=3, base_delay=0.01))
        def flaky_func() -> None:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_auto_retry_failure(self) -> None:
        """재시도 실패 테스트"""

        @auto_retry(RetryConfig(max_retries=2, base_delay=0.01))
        def always_fails() -> None:
            raise ValueError("Permanent error")

        with pytest.raises(ValueError):
            always_fails()

    def test_cache_result(self) -> None:
        """캐싱 테스트"""
        call_count = 0

        @cache_result(ttl_seconds=10.0)
        def expensive_func(x) -> None:
            nonlocal call_count
            call_count += 1
            return x * 2

        # 첫 호출
        result1 = expensive_func(5)
        # 캐시 히트
        result2 = expensive_func(5)
        # 다른 인자
        result3 = expensive_func(10)

        assert result1 == 10
        assert result2 == 10
        assert result3 == 20
        assert call_count == 2  # 5와 10 각각 한 번씩
