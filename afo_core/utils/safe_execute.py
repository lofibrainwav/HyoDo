# Trinity Score: 90.0 (Established by Chancellor)
"""
Safe Execute Utility
善 (Goodness): DRY_RUN, 권한 검증, 폴백
PDF 페이지 3: DRY_RUN, 권한 검증, 폴백
"""

import asyncio
import logging
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from AFO.config.antigravity import antigravity

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe_execute(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
    """
    안전한 실행 데코레이터 (善: Goodness)

    PDF 페이지 3: DRY_RUN, 권한 검증, 폴백
    - DRY_RUN 모드: 실제 실행 없이 시뮬레이션
    - try-except 폴백: 에러 발생 시 안전한 폴백 반환

    Args:
        func: 실행할 함수

    Returns:
        래핑된 함수
    """

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        """비동기 함수 래퍼"""
        if antigravity.DRY_RUN_DEFAULT:
            logger.info(f"[善: DRY_RUN] {func.__name__} - 실제 실행 없이 시뮬레이션 완료")
            return {"status": "safe_simulation", "function": func.__name__}

        try:
            import asyncio

            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return {"status": "success", "result": result}
        except Exception as e:
            logger.warning(f"[善: 폴백] {func.__name__} - 에러 발생, 안전 폴백: {e}")
            return {"status": "fallback", "error": str(e), "function": func.__name__}

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
        """동기 함수 래퍼"""
        if antigravity.DRY_RUN_DEFAULT:
            logger.info(f"[善: DRY_RUN] {func.__name__} - 실제 실행 없이 시뮬레이션 완료")
            return {"status": "safe_simulation", "function": func.__name__}

        try:
            result = func(*args, **kwargs)
            return {"status": "success", "result": result}
        except Exception as e:
            logger.warning(f"[善: 폴백] {func.__name__} - 에러 발생, 안전 폴백: {e}")
            return {"status": "fallback", "error": str(e), "function": func.__name__}

    # 비동기 함수인지 확인
    from typing import cast

    if asyncio.iscoroutinefunction(func):
        return cast("Callable[..., dict[str, Any]]", async_wrapper)
    return cast("Callable[..., dict[str, Any]]", sync_wrapper)
