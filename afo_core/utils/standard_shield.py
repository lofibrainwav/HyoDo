from __future__ import annotations

import asyncio
import logging
import traceback
from functools import wraps
from typing import Any, TypeVar

from AFO.utils.error_handling import AFOError, GoodnessError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def shield(
    default_return: Any = None,
    log_error: bool = True,
    reraise: bool = False,
    pillar: str = "善",
) -> Any:
    """
    Standardized 'Goodness Shield' decorator (善의 방패).

    Standardizes error handling across the kingdom, ensuring consistent logging
    and graceful degradation.

    Args:
        default_return: Value to return if an error occurs and reraise is False.
        log_error: Whether to log the error with full traceback.
        reraise: Whether to reraise the original error (wrapped in AFOError if not already).
        pillar: The Trinity pillar associated with this operation (default: 善).
    """

    def decorator(func: Any) -> Any:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return _handle_exception(func, e, default_return, log_error, reraise, pillar)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return _handle_exception(func, e, default_return, log_error, reraise, pillar)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def _handle_exception(
    func: Any,
    e: Exception,
    default_return: Any,
    log_error: bool,
    reraise: bool,
    pillar: str,
) -> Any:
    """Internal helper to handle exceptions consistently."""
    if log_error:
        func_name = getattr(func, "__name__", "unknown")
        logger.error(
            f"[{pillar}] Shield activated for {func_name}: {e}",
            exc_info=True,
            extra={
                "pillar": pillar,
                "function": func_name,
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
            },
        )

    if reraise:
        if isinstance(e, AFOError):
            raise e
        raise GoodnessError(f"Shielded Error in {func.__name__}: {e}") from e

    return default_return
