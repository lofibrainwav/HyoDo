from __future__ import annotations

import asyncio
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

T = TypeVar("T")

# Trinity Score: 90.0 (Established by Chancellor)
"""DRY_RUN 메커니즘 - 眞(Truth) 점수 향상
모든 주요 기능에 DRY_RUN 지원 추가
"""


class DryRunMode:
    """DRY_RUN 모드 관리"""

    _enabled = False

    @classmethod
    def enable(cls) -> None:
        """DRY_RUN 모드 활성화"""
        cls._enabled = True

    @classmethod
    def disable(cls) -> None:
        """DRY_RUN 모드 비활성화"""
        cls._enabled = False

    @classmethod
    def is_enabled(cls) -> bool:
        """DRY_RUN 모드 확인"""
        return cls._enabled


def dry_run[T](func: Callable[..., T]) -> Callable[..., Any]:
    """DRY_RUN 데코레이터"""

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        if DryRunMode.is_enabled():
            # DRY_RUN 모드: 실제 실행 없이 시뮬레이션
            return {
                "dry_run": True,
                "function": func.__name__,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100],
                "simulated_result": "success",
            }
        else:
            # 실제 실행

            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        if DryRunMode.is_enabled():
            # DRY_RUN 모드: 실제 실행 없이 시뮬레이션
            return {
                "dry_run": True,
                "function": func.__name__,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100],
                "simulated_result": "success",
            }
        else:
            # 실제 실행
            return func(*args, **kwargs)

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper
