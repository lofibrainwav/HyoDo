"""
Exponential Backoff Decorator - 재시도 데코레이터

함수에 적용할 수 있는 재시도 데코레이터를 제공합니다.
"""

from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

from .backoff import ExponentialBackoff

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")


def retry_with_exponential_backoff(
    max_retries: int = 5,
    base_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    지수 백오프 재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수 (기본 5회)
        base_delay: 초기 지연 시간 (기본 1초)
        exponential_base: 지수 밑수 (기본 2)
        max_delay: 최대 지연 시간 (기본 60초)
        jitter: Jitter 사용 여부 (기본 True)
        retryable_exceptions: 재시도할 예외 튜플
        on_retry: 재시도 시 실행할 콜백

    Example:
        >>> @retry_with_exponential_backoff(max_retries=3)
        ... def fetch_data():
        ...     return requests.get("https://api.example.com").json()
        >>> data = fetch_data()
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            backoff = ExponentialBackoff(
                max_retries=max_retries,
                base_delay=base_delay,
                exponential_base=exponential_base,
                max_delay=max_delay,
                jitter=jitter,
                retryable_exceptions=retryable_exceptions,
                on_retry=on_retry,
            )
            return backoff.execute(func, *args, **kwargs)

        return wrapper

    return decorator
