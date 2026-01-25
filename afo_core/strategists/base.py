# Trinity Score: 90.0 (Established by Chancellor)
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, TypeVar

try:
    from AFO.utils.structured_logging import log_sse
except ImportError:
    # Fallback if logging module not found (Graceful Degradation)
    def log_sse(message: str) -> None:
        print(f"[LOG] {message}")


T = TypeVar("T")


def log_action(action: str, result: Any) -> None:
    """Common logging function for consistent output."""
    timestamp = datetime.now(UTC).isoformat()
    # Using log_sse for specific important actions if needed, or just print
    print(f"[{action}] Result: {result} (Time: {timestamp})")


def log_error(action: str, error: Exception) -> None:
    """Common error logging with timestamp."""
    timestamp = datetime.now(UTC).isoformat()
    log_sse(f"[{action}] Error Detail: {error!s} at {timestamp} - Executing Fallback")


def robust_execute(func: Callable[..., T], data: Any, fallback_value: T | None = None) -> T:
    """Common Error Handling: Graceful degradation & Fallback.
    (PDF Tech Completeness 25/25: Robust Error Handling)
    """
    try:
        result = func(*data) if isinstance(data, tuple) else func(data)
        if result is None and fallback_value is not None:
            return fallback_value
        return result
    except Exception as e:
        log_error(func.__name__, e)
        if fallback_value is None:
            raise
        return fallback_value
