"""
AFO Kingdom Resilience Decorator (@shield)
Phase 73: The Truth Crusade & Quality Fortress
Pillar: 善 (Goodness) - Harmony & Resilience

Provides a unified decorator to protect critical services from unhandled exceptions.
"""

import functools
import inspect
import logging
from typing import Any, Callable, TypeVar

# Import HTTPException for exclusion (if available)
try:
    from fastapi import HTTPException as FastAPIHTTPException
except ImportError:
    FastAPIHTTPException = None  # type: ignore[misc, assignment]

T = TypeVar("T")

# Standard AFO Shield Logger
logger = logging.getLogger("AFO.Shield")


def shield(
    fallback: Any = None,
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    pillar: str = "善",
    log_level: int = logging.ERROR,
    exclude: tuple[type[Exception], ...] | None = None,
) -> Callable:
    """
    Trinity Resilience Shield (@shield)

    A universal decorator to protect functions from unhandled exceptions.
    Optimized for AFO Kingdom's Phase 73 standards.

    Args:
        fallback: The value to return if the function fails.
        exceptions: Single exception or tuple of exceptions to catch.
        pillar: The Trinity Pillar this protector belongs to (Default: 善/Goodness).
        log_level: The logging level to use for failures.
        exclude: Exception types to re-raise instead of catching.
                 HTTPException is excluded by default for FastAPI compatibility.
    """
    exceptions_tuple = (exceptions,) if isinstance(exceptions, type) else exceptions

    # Default exclude HTTPException for FastAPI compatibility
    if exclude is None and FastAPIHTTPException is not None:
        exclude = (FastAPIHTTPException,)
    elif exclude is None:
        exclude = ()

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except exclude:
                # Re-raise excluded exceptions (like HTTPException)
                raise
            except exceptions_tuple as e:
                logger.log(
                    log_level,
                    f"🛡️ [Shield:{pillar}] Async failure in '{func.__name__}': {e}",
                    extra={
                        "pillar": pillar,
                        "resilience": "shield",
                        "func": func.__name__,
                    },
                    exc_info=True,
                )
                return fallback

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exclude:
                # Re-raise excluded exceptions (like HTTPException)
                raise
            except exceptions_tuple as e:
                logger.log(
                    log_level,
                    f"🛡️ [Shield:{pillar}] Sync failure in '{func.__name__}': {e}",
                    extra={
                        "pillar": pillar,
                        "resilience": "shield",
                        "func": func.__name__,
                    },
                    exc_info=True,
                )
                return fallback

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
