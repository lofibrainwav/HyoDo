"""
Async Exponential Backoff - 비동기 지수 백오프

비동기 컨텍스트에서 사용 가능한 지수 백오프 함수를 제공합니다.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, TypeVar, overload

from .backoff import ExponentialBackoff

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

# TypeVar for generic return type preservation
T = TypeVar("T")


@overload
async def exponential_backoff(  # noqa: UP047 - TypeVar used for @overload compatibility
    func: Callable[..., Awaitable[T]],
    max_retries: int = ...,
    base_delay: float = ...,
    exponential_base: float = ...,
    max_delay: float = ...,
    jitter: bool = ...,
    retryable_exceptions: tuple[type[BaseException], ...] = ...,
    *args: Any,
    **kwargs: Any,
) -> T: ...


@overload
async def exponential_backoff(  # noqa: UP047 - TypeVar used for @overload compatibility
    func: Callable[..., T],
    max_retries: int = ...,
    base_delay: float = ...,
    exponential_base: float = ...,
    max_delay: float = ...,
    jitter: bool = ...,
    retryable_exceptions: tuple[type[BaseException], ...] = ...,
    *args: Any,
    **kwargs: Any,
) -> T: ...


async def exponential_backoff(
    func: Callable[..., Any],
    max_retries: int = 5,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Async wrapper for ExponentialBackoff.execute()

    This function allows using ExponentialBackoff in async contexts.

    Args:
        func: 실행할 함수 (동기 또는 비동기)
        max_retries: 최대 재시도 횟수
        base_delay: 초기 지연 시간
        exponential_base: 지수 밑수
        max_delay: 최대 지연 시간
        jitter: Jitter 사용 여부
        retryable_exceptions: 재시도할 예외 튜플
        *args, **kwargs: 함수 인자

    Returns:
        함수 실행 결과

    Example:
        >>> await exponential_backoff(
        ...     lambda: redis_client.ping(),
        ...     max_retries=3,
        ...     base_delay=1.0
        ... )
    """

    backoff = ExponentialBackoff(
        max_retries=max_retries,
        base_delay=base_delay,
        exponential_base=exponential_base,
        max_delay=max_delay,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions,
    )

    # Check if func is async
    if asyncio.iscoroutinefunction(func):
        # For async functions, we need to await them
        async def async_wrapper():
            last_exception = None
            for attempt in range(backoff.max_retries):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"✅ [{getattr(func, '__name__', 'unknown')}] 재시도 성공 "
                            f"(시도 {attempt + 1}/{backoff.max_retries})"
                        )
                    return result
                except backoff.retryable_exceptions as e:
                    last_exception = e
                    if attempt == backoff.max_retries - 1:
                        logger.error(
                            f"❌ [{getattr(func, '__name__', 'unknown')}] "
                            f"재시도 최종 실패 (최대 {backoff.max_retries}회 초과)"
                        )
                        raise
                    delay = backoff._calculate_delay(attempt)
                    logger.warning(
                        f"⚠️ [{getattr(func, '__name__', 'unknown')}] "
                        f"재시도 {attempt + 1}/{backoff.max_retries} "
                        f"(오류: {type(e).__name__}: {str(e)[:100]}, 대기: {delay:.2f}초)"
                    )
                    await asyncio.sleep(delay)
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected execution path in async exponential_backoff")

        # Note: type: ignore is safe here because @overload signatures
        # above provide proper type inference for callers. The implementation
        # returns Any but callers see the correct generic return type T.
        return await async_wrapper()  # type: ignore[no-any-return]
    else:
        # For sync functions, run in executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, backoff.execute, func, *args, **kwargs)
