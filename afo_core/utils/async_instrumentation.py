import contextlib
import logging
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from functools import wraps
from typing import Any

import anyio

logger = logging.getLogger(__name__)


def instrument_task(task_name: str | None = None) -> Callable:
    """
    Decorator to instrument an async task for structured concurrency tracking.

    Provides '眞 (Truth)' into the task's life-cycle, including duration and status.
    Compatible with Anyio/Trio philosophy.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        name = task_name or func.__name__

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                import sentry_sdk

                sentry_sdk.add_breadcrumb(
                    category="task", message=f"🚀 Task START: {name}", level="info"
                )
            except ImportError:
                pass

            start_time = datetime.now(UTC)
            logger.info(f"🚀 [Async Task START] {name}")
            try:
                result = await func(*args, **kwargs)
                duration = (datetime.now(UTC) - start_time).total_seconds()
                logger.info(f"✅ [Async Task END] {name} (Duration: {duration:.3f}s)")
                with contextlib.suppress(NameError):
                    sentry_sdk.add_breadcrumb(
                        category="task",
                        message=f"✅ Task END: {name} ({duration:.3f}s)",
                        level="info",
                    )
                return result
            except anyio.get_cancelled_exc_class():
                logger.warning(f"🛑 [Async Task CANCELLED] {name}")
                with contextlib.suppress(NameError):
                    sentry_sdk.add_breadcrumb(
                        category="task",
                        message=f"🛑 Task CANCELLED: {name}",
                        level="warning",
                    )
                raise  # 핵심: 취소 신호를 절대로 삼키지 않고 재전파
            except Exception as e:
                logger.error(f"❌ [Async Task ERROR] {name}: {type(e).__name__}: {e}")
                try:
                    with sentry_sdk.push_scope() as scope:
                        scope.set_tag("task_name", name)
                        scope.set_extra("task_args", args)
                        scope.set_extra("task_kwargs", kwargs)
                        sentry_sdk.capture_exception(e)
                except NameError:
                    pass
                raise

        return wrapper

    return decorator


async def track_task_group_status(tg_name: str):
    """
    Utility to log the status of an Anyio TaskGroup.
    (Placeholder for Trio-specific instruments which provide deeper hooks)
    """
    logger.info(f"🛡️  [TaskGroup ACTIVE] {tg_name}")
