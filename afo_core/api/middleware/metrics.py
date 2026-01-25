# Trinity Score: 90.0 (Established by Chancellor)
"""Metrics Middleware for AFO Kingdom API

Lightweight metrics collection middleware that integrates with Prometheus.
"""

import time
from collections.abc import Callable
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

try:
    from AFO.api.middleware.prometheus import (
        ACTIVE_CONNECTIONS,
        REQUEST_COUNT,
        REQUEST_LATENCY,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting request metrics."""

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        """Process request and collect metrics."""
        start_time = time.perf_counter()

        # Track active connections
        if PROMETHEUS_AVAILABLE:
            ACTIVE_CONNECTIONS.labels(service="afo-api").inc()

        try:
            response = await call_next(request)
        finally:
            if PROMETHEUS_AVAILABLE:
                ACTIVE_CONNECTIONS.labels(service="afo-api").dec()

        # Record metrics
        duration = time.perf_counter() - start_time
        endpoint = request.url.path
        method = request.method
        status_code = str(response.status_code)

        if PROMETHEUS_AVAILABLE:
            REQUEST_COUNT.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                service="afo-api",
            ).inc()
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                service="afo-api",
            ).observe(duration)

        return response
