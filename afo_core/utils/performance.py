"""
AFO Kingdom Performance Utilities
Trinity Score: 眞 (Truth) - Precision Measurement
Author: AFO Kingdom Development Team
"""

import functools
import logging
import tracemalloc
from collections.abc import Callable
from typing import Any

# Use structured logger if available, else standard logging
try:
    from AFO.utils.structured_logger import StructuredLogger

    logger = StructuredLogger(__name__)
except ImportError:
    logger = logging.getLogger(__name__)


def monitor_memory(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to monitor memory usage of a function.
    Logs memory difference before and after execution.
    Target: TICKET-040 (Performance Optimization)
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check if already tracing
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()

        snapshot_start = tracemalloc.take_snapshot()

        try:
            result = func(*args, **kwargs)
        finally:
            snapshot_end = tracemalloc.take_snapshot()

            # Only stop if we started it
            if not was_tracing:
                tracemalloc.stop()

            # Calculate difference
            top_stats = snapshot_end.compare_to(snapshot_start, "lineno")

            # Sum up total memory difference
            total_diff = sum(stat.size_diff for stat in top_stats)
            total_diff_mb = total_diff / 1024 / 1024

            context = {
                "function": func.__name__,
                "memory_diff_mb": round(total_diff_mb, 4),
                "top_allocation_diff": str(top_stats[0]) if top_stats else "None",
            }

            if hasattr(logger, "info") and isinstance(logger, StructuredLogger):
                logger.info(
                    f"Memory Usage: {func.__name__} used {total_diff_mb:.4f} MB",
                    context=context,
                )
            else:
                logger.info(f"Memory Usage: {func.__name__} used {total_diff_mb:.4f} MB")

        return result

    return wrapper
