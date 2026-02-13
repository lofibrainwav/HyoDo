"""API Metrics Module.

Provides detailed API request/response metrics collection.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any

from ..prometheus import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUEST_SIZE,
    HTTP_REQUESTS_TOTAL,
    HTTP_RESPONSE_SIZE,
)

logger = logging.getLogger(__name__)


@dataclass
class APIMetric:
    """Single API call metric."""

    method: str
    endpoint: str
    status_code: int
    duration_seconds: float
    request_size_bytes: int
    response_size_bytes: int
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "endpoint": self.endpoint,
            "status_code": self.status_code,
            "duration_seconds": self.duration_seconds,
            "request_size_bytes": self.request_size_bytes,
            "response_size_bytes": self.response_size_bytes,
            "timestamp": self.timestamp,
        }


class APIMetricsCollector:
    """Collects API request/response metrics."""

    def __init__(self, max_history: int = 1000) -> None:
        self.max_history = max_history
        self._history: list[APIMetric] = []
        logger.info("APIMetricsCollector initialized")

    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_seconds: float,
        request_size_bytes: int = 0,
        response_size_bytes: int = 0,
    ) -> None:
        """Record an API request metric.

        Args:
            method: HTTP method
            endpoint: API endpoint path
            status_code: HTTP status code
            duration_seconds: Request duration
            request_size_bytes: Request body size
            response_size_bytes: Response body size
        """
        metric = APIMetric(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_seconds=duration_seconds,
            request_size_bytes=request_size_bytes,
            response_size_bytes=response_size_bytes,
        )

        self._history.append(metric)

        # Trim history if needed
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history :]

        logger.debug(f"API metric recorded: {method} {endpoint} -> {status_code}")

    def get_summary(self) -> dict[str, Any]:
        """Get API metrics summary."""
        if not self._history:
            return {
                "total_requests": 0,
                "avg_duration_ms": 0.0,
                "error_rate": 0.0,
                "top_endpoints": [],
            }

        total = len(self._history)
        errors = sum(1 for m in self._history if m.status_code >= 400)
        avg_duration = sum(m.duration_seconds for m in self._history) / total

        # Count by endpoint
        endpoint_counts: dict[str, int] = {}
        for m in self._history:
            key = f"{m.method} {m.endpoint}"
            endpoint_counts[key] = endpoint_counts.get(key, 0) + 1

        top_endpoints = sorted(
            endpoint_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "total_requests": total,
            "avg_duration_ms": avg_duration * 1000,
            "error_rate": errors / total if total > 0 else 0.0,
            "top_endpoints": [{"endpoint": ep, "count": cnt} for ep, cnt in top_endpoints],
        }

    def get_history(self, limit: int = 100) -> list[APIMetric]:
        """Get recent API metrics history."""
        return self._history[-limit:]

    def clear_history(self) -> None:
        """Clear metrics history."""
        self._history.clear()
        logger.info("API metrics history cleared")


def record_api_call(
    method: str,
    endpoint: str,
    status_code: int,
    duration_seconds: float,
    request_size_bytes: int = 0,
    response_size_bytes: int = 0,
) -> None:
    """Convenience function to record API metrics directly to Prometheus.

    Args:
        method: HTTP method
        endpoint: API endpoint path
        status_code: HTTP status code
        duration_seconds: Request duration
        request_size_bytes: Request body size
        response_size_bytes: Response body size
    """
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code),
    ).inc()

    HTTP_REQUEST_DURATION.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration_seconds)

    if request_size_bytes > 0:
        HTTP_REQUEST_SIZE.labels(
            method=method,
            endpoint=endpoint,
        ).observe(request_size_bytes)

    if response_size_bytes > 0:
        HTTP_RESPONSE_SIZE.labels(
            method=method,
            endpoint=endpoint,
        ).observe(response_size_bytes)


__all__ = [
    "APIMetric",
    "APIMetricsCollector",
    "record_api_call",
]
