"""
Exponential Backoff - 지수 백오프 재시도 클래스

네트워크 오류, API 타임아웃, 일시적 장애에 대한 지능적 재시도 전략
"""

from __future__ import annotations

import logging
import random
import time
from typing import TYPE_CHECKING, Any, TypeVar

from .metrics import (
    PROMETHEUS_AVAILABLE,
    RETRY_ATTEMPTS,
    RETRY_DURATION,
    RETRY_FAILURES,
    RETRY_SUCCESS,
)

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")

logger = logging.getLogger(__name__)


class ExponentialBackoff:
    """
    지수 백오프 재시도 클래스

    **수학적 원리**:
    대기_시간 = 초기_지연 × (지수_밑수 ^ 재시도_횟수) + Jitter

    **예시**:
    초기_지연=1초, 지수_밑수=2, Jitter=True
    - 재시도 1: 1 × 2^0 + random(0, 1) = 1~2초
    - 재시도 2: 1 × 2^1 + random(0, 2) = 2~4초
    - 재시도 3: 1 × 2^2 + random(0, 4) = 4~8초
    - 재시도 4: 1 × 2^3 + random(0, 8) = 8~16초

    Attributes:
        max_retries: 최대 재시도 횟수 (기본 5회)
        base_delay: 초기 지연 시간 초 (기본 1초)
        exponential_base: 지수 밑수 (기본 2)
        max_delay: 최대 지연 시간 초 (기본 60초)
        jitter: Jitter 사용 여부 (기본 True)
        retryable_exceptions: 재시도할 예외 튜플
        on_retry: 재시도 시 실행할 콜백 함수

    Example:
        >>> backoff = ExponentialBackoff(max_retries=3)
        >>> result = backoff.execute(lambda: api_call())
    """

    def __init__(
        self,
        max_retries: int = 5,
        base_delay: float = 1.0,
        exponential_base: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
        on_retry: Callable[[int, BaseException], None] | None = None,
    ) -> None:
        """
        Args:
            max_retries: 최대 재시도 횟수 (기본 5회)
            base_delay: 초기 지연 시간 (기본 1초)
            exponential_base: 지수 밑수 (기본 2)
            max_delay: 최대 지연 시간 (기본 60초)
            jitter: Jitter 사용 여부 (기본 True)
            retryable_exceptions: 재시도할 예외 튜플
            on_retry: 재시도 시 실행할 콜백 (시도 번호, 예외 받음)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.exponential_base = exponential_base
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions
        self.on_retry = on_retry

        # 통계
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0

    def _calculate_delay(self, attempt: int) -> float:
        """
        지연 시간 계산

        Args:
            attempt: 재시도 횟수 (0부터 시작)

        Returns:
            지연 시간 (초)
        """
        # 기본 지연 시간 계산
        delay = min(self.base_delay * (self.exponential_base**attempt), self.max_delay)

        # Jitter 추가 (Full Jitter 방식)
        if self.jitter:
            # Full Jitter: 0 ~ delay 범위의 무작위 값
            delay = random.uniform(0, delay)

        return delay

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        함수를 지수 백오프로 실행

        Args:
            func: 실행할 함수
            *args, **kwargs: 함수 인자

        Returns:
            함수 실행 결과

        Raises:
            마지막 재시도 실패 시 예외 발생

        Example:
            >>> backoff = ExponentialBackoff(max_retries=3)
            >>> result = backoff.execute(requests.get, "https://api.example.com")
        """
        last_exception = None
        func_name = getattr(func, "__name__", "unknown")
        start_time = time.time()

        for attempt in range(self.max_retries):
            self.total_attempts += 1

            # Prometheus 메트릭: 재시도 시도 횟수
            if PROMETHEUS_AVAILABLE and RETRY_ATTEMPTS is not None:
                RETRY_ATTEMPTS.labels(function_name=func_name).inc()

            try:
                # 함수 실행
                result = func(*args, **kwargs)
                self.total_successes += 1

                # Prometheus 메트릭: 성공
                if PROMETHEUS_AVAILABLE:
                    if RETRY_SUCCESS is not None:
                        RETRY_SUCCESS.labels(function_name=func_name).inc()
                    if RETRY_DURATION is not None:
                        duration = time.time() - start_time
                        RETRY_DURATION.labels(function_name=func_name).observe(duration)

                # 재시도 후 성공한 경우 로그
                if attempt > 0:
                    logger.info(
                        f"✅ [{func.__name__}] 재시도 성공 (시도 {attempt + 1}/{self.max_retries})"
                    )

                return result

            except self.retryable_exceptions as e:
                last_exception = e

                # 마지막 시도 실패
                if attempt == self.max_retries - 1:
                    self.total_failures += 1

                    # Prometheus 메트릭: 실패
                    if PROMETHEUS_AVAILABLE and RETRY_FAILURES is not None:
                        exception_type = type(e).__name__
                        RETRY_FAILURES.labels(
                            function_name=func_name, exception_type=exception_type
                        ).inc()

                    logger.error(
                        f"❌ [{func.__name__}] 재시도 최종 실패 (최대 {self.max_retries}회 초과)"
                    )
                    raise

                # 지연 시간 계산
                delay = self._calculate_delay(attempt)

                # 재시도 로그
                logger.warning(
                    f"⚠️ [{func.__name__}] 재시도 {attempt + 1}/{self.max_retries} "
                    f"(오류: {type(e).__name__}: {str(e)[:100]}, "
                    f"대기: {delay:.2f}초)"
                )

                # 콜백 실행
                if self.on_retry:
                    try:
                        self.on_retry(attempt, e)
                    except (TypeError, AttributeError, ValueError) as callback_error:
                        logger.error(
                            "재시도 콜백 오류 (타입/속성/값 에러): %s",
                            str(callback_error),
                        )
                    except (
                        Exception
                    ) as callback_error:  # - Intentional fallback for callback errors
                        logger.error(
                            "재시도 콜백 오류 (예상치 못한 에러): %s",
                            str(callback_error),
                        )

                # 대기
                time.sleep(delay)

        # 이 코드는 실행되지 않음 (위에서 raise 또는 return)
        if last_exception:
            raise last_exception
        # max_retries > 0이면 항상 위에서 return하거나 raise하므로 실행되지 않음
        raise RuntimeError("Unexpected execution path in ExponentialBackoff.execute")

    def get_stats(self) -> dict[str, Any]:
        """
        재시도 통계 반환

        Returns:
            {
                "total_attempts": 총 시도 횟수,
                "total_successes": 총 성공 횟수,
                "total_failures": 총 실패 횟수,
                "success_rate": 성공률 (0~1)
            }

        Example:
            >>> backoff = ExponentialBackoff()
            >>> backoff.execute(some_func)
            >>> stats = backoff.get_stats()
            >>> print(f"성공률: {stats['success_rate'] * 100:.1f}%")
        """
        return {
            "total_attempts": self.total_attempts,
            "total_successes": self.total_successes,
            "total_failures": self.total_failures,
            "success_rate": (
                self.total_successes / self.total_attempts if self.total_attempts > 0 else 0.0
            ),
        }

    def reset_stats(self) -> None:
        """통계 초기화"""
        self.total_attempts = 0
        self.total_successes = 0
        self.total_failures = 0
