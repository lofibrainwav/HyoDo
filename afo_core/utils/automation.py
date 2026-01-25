# Trinity Score: 90.0 (Established by Chancellor)
"""孝 (Serenity) 자동화 유틸리티

AFO 왕국의 마찰 제거 및 자동화 패턴
"""

import asyncio
import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class RetryConfig:
    """재시도 설정"""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential: bool = True,
    ) -> None:
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential


def auto_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """자동 재시도 데코레이터 (孝 패턴)

    Args:
        config: 재시도 설정

    Returns:
        데코레이터

    Example:
        >>> @auto_retry(RetryConfig(max_retries=3))
        ... def call_api(): ...

    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < config.max_retries - 1:
                        delay = config.base_delay
                        if config.exponential:
                            delay = min(config.base_delay * (2**attempt), config.max_delay)
                        logger.warning(
                            f"[孝] 재시도 {attempt + 1}/{config.max_retries}: "
                            f"{func.__name__} ({e}) - {delay:.1f}s 대기"
                        )
                        time.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in auto_retry")

        return wrapper

    return decorator


def async_auto_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """비동기 자동 재시도 데코레이터 (孝 패턴)

    Args:
        config: 재시도 설정

    Returns:
        데코레이터

    Example:
        >>> @async_auto_retry(RetryConfig(max_retries=3))
        ... async def call_api(): ...

    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Exception | None = None

            for attempt in range(config.max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < config.max_retries - 1:
                        delay = config.base_delay
                        if config.exponential:
                            delay = min(config.base_delay * (2**attempt), config.max_delay)
                        logger.warning(
                            f"[孝] 비동기 재시도 {attempt + 1}/{config.max_retries}: "
                            f"{func.__name__} ({e}) - {delay:.1f}s 대기"
                        )
                        await asyncio.sleep(delay)

            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in async_auto_retry")

        return wrapper

    return decorator


class CircuitBreaker:
    """서킷 브레이커 패턴 (孝 패턴)

    연속 실패 시 호출 차단하여 시스템 보호
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: float = 60.0,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time: float | None = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # 상태 체크
            if self.state == "OPEN":
                if (
                    self.last_failure_time
                    and time.time() - self.last_failure_time > self.reset_timeout
                ):
                    self.state = "HALF_OPEN"
                    logger.info(f"[孝] 서킷 브레이커 HALF_OPEN: {func.__name__}")
                else:
                    raise RuntimeError(f"서킷 브레이커 OPEN: {func.__name__} 호출 차단")

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failures = 0
                    logger.info(f"[孝] 서킷 브레이커 CLOSED: {func.__name__}")
                return result
            except Exception:
                self.failures += 1
                self.last_failure_time = time.time()
                if self.failures >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(
                        f"[孝] 서킷 브레이커 OPEN: {func.__name__} ({self.failures}회 실패)"
                    )
                raise

        return wrapper


def cache_result(
    ttl_seconds: float = 300.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """결과 캐싱 데코레이터 (孝 패턴)

    Args:
        ttl_seconds: 캐시 유효 시간

    Returns:
        데코레이터

    """
    cache: dict[str, tuple[Any, float]] = {}

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            key = str((args, tuple(sorted(kwargs.items()))))
            now = time.time()

            if key in cache:
                result, cached_time = cache[key]
                if now - cached_time < ttl_seconds:
                    logger.debug(f"[孝] 캐시 히트: {func.__name__}")
                    # Result is already type T
                    return result  # type: ignore[no-any-return]

            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result

        return wrapper

    return decorator
