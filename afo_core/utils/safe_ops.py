import functools
import logging
import traceback
from typing import Any, Callable, TypeVar

T = TypeVar("T")

logger = logging.getLogger("AFO.Goodness")


class SafeOperation:
    """
    Goodness (善) Pillar Utility: SafeOperation

    Wraps critical operations in a safety net to prevent system crashes.
    Follows the 'Shield' philosophy of Yi Sun-sin.
    """

    @staticmethod
    def run(
        operation: Callable[..., T],
        *args,
        error_msg: str = "Operation failed",
        fallback: T | Callable[[], T] | None = None,
        raise_error: bool = False,
        **kwargs,
    ) -> T | None:
        """
        Execute a function safely.

        Args:
            operation: The function to execute.
            error_msg: Log message prefix on failure.
            fallback: Value to return or function to call on failure.
            raise_error: If True, re-raise the exception after logging.
        """
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            error_details = traceback.format_exc()
            logger.error(f"🛡️ [SafeOperation] {error_msg}: {e!s}\n{error_details}")

            if raise_error:
                raise e

            if callable(fallback):
                try:
                    return fallback()
                except Exception as fb_e:
                    logger.critical(f"🛡️ [SafeOperation] Fallback also failed: {fb_e!s}")
                    return None
            return fallback

    @staticmethod
    def decorator(error_msg: str = "Function failed", fallback: Any = None) -> None:
        """Decorator for safe execution"""

        def decorator_wrapper(func) -> None:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> None:
                return SafeOperation.run(
                    func,
                    *args,
                    error_msg=f"{error_msg} ({func.__name__})",
                    fallback=fallback,
                    **kwargs,
                )

            return wrapper

        return decorator_wrapper
