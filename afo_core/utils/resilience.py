"""
AFO Kingdom Resilience Utilities
Trinity Score: 善 (Goodness) - System Stability & Safety
Author: AFO Kingdom Development Team

Provides standard resilience patterns:
1. Circuit Breaker: Prevents cascading failures when external services are down.
2. Exponential Backoff: Retries failed operations politely.
3. Safe Step: Catches exceptions and returns fallback.
"""

import asyncio
import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe_step(
    fallback_return: Any = None,
    log_level: int = logging.ERROR,
    step_name: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T | Any]]:
    """
    Decorator to make a pipeline step resilient to failures.

    Args:
        fallback_return: Value to return if the step fails.
        log_level: Logging level for the error exception.
        step_name: Optional custom name for the step in logs.

    Returns:
        Decorated function that returns fallback_return on exception.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T | Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T | Any:
            name = step_name or func.__name__
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(
                    log_level,
                    f"❌ [Resilience] Step '{name}' failed: {e}",
                    exc_info=True,
                )
                return fallback_return

        return wrapper

    return decorator


class CircuitBreakerOpenException(Exception):
    """Circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Simple Circuit Breaker implementation.

    States: CLOSED (Normal), OPEN (Failing), HALF-OPEN (Recovering)
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "CLOSED"

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = "HALF-OPEN"
                    logger.info(f"Circuit Breaker for {func.__name__} entering HALF-OPEN state.")
                else:
                    logger.warning(f"Circuit Breaker for {func.__name__} is OPEN. Call rejected.")
                    raise CircuitBreakerOpenException(f"Circuit is OPEN for {func.__name__}")

            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF-OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                    logger.info(f"Circuit Breaker for {func.__name__} closed (recovered).")
                elif self.state == "CLOSED":
                    self.failure_count = 0  # Reset on success
                return result

            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                logger.warning(
                    f"Circuit Breaker: Failure detected via {func.__name__} ({self.failure_count}/{self.failure_threshold}): {e}"
                )

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.error(f"Circuit Breaker for {func.__name__} OPENED!")
                raise e

        return wrapper


def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for exponential backoff retries.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        f"Retry {attempt + 1}/{retries} for {func.__name__} failed: {e}. Retrying in {delay}s..."
                    )
                    if attempt < retries - 1:
                        await asyncio.sleep(delay)
                        delay *= backoff_factor

            logger.error(f"All {retries} retries failed for {func.__name__}.")
            raise last_exception  # type: ignore

        return wrapper

    return decorator
