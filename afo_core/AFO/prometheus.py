"""AFO Prometheus Module (眞善美孝永)

Complete Prometheus metrics middleware implementation for FastAPI.
Provides HTTP metrics, Trinity Score metrics, and 11臟六腑 organ health metrics.

Phase: 117 | Ticket: TICKET-113
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    Info,
    generate_latest,
)
from prometheus_client.registry import CollectorRegistry

if TYPE_CHECKING:
    from fastapi import FastAPI

logger = logging.getLogger(__name__)

# Create a dedicated registry for AFO metrics
AFO_REGISTRY = CollectorRegistry()

# HTTP Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "afo_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=AFO_REGISTRY,
)

HTTP_REQUEST_DURATION = Histogram(
    "afo_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=AFO_REGISTRY,
)

HTTP_REQUEST_SIZE = Histogram(
    "afo_http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=AFO_REGISTRY,
)

HTTP_RESPONSE_SIZE = Histogram(
    "afo_http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=AFO_REGISTRY,
)

ACTIVE_CONNECTIONS = Gauge(
    "afo_active_connections",
    "Number of active connections",
    registry=AFO_REGISTRY,
)

# Trinity Score Metrics
TRINITY_SCORE = Gauge(
    "afo_trinity_score",
    "Trinity Score by pillar",
    ["pillar"],
    registry=AFO_REGISTRY,
)

TRINITY_SCORE_TOTAL = Gauge(
    "afo_trinity_score_total",
    "Total Trinity Score (0-100)",
    registry=AFO_REGISTRY,
)

TRINITY_CHECKS_TOTAL = Counter(
    "afo_trinity_checks_total",
    "Total Trinity checks run",
    ["result"],
    registry=AFO_REGISTRY,
)

# 11臟六腑 Organ Metrics
ORGAN_HEALTH = Gauge(
    "afo_organ_health",
    "Organ health score (0-100)",
    ["organ_name"],
    registry=AFO_REGISTRY,
)

ORGAN_RESPONSE_TIME = Gauge(
    "afo_organ_response_time_ms",
    "Organ response time in milliseconds",
    ["organ_name"],
    registry=AFO_REGISTRY,
)

ORGAN_ERRORS_TOTAL = Counter(
    "afo_organ_errors_total",
    "Total organ errors",
    ["organ_name", "error_type"],
    registry=AFO_REGISTRY,
)

# Application Info
APP_INFO = Info(
    "afo_app",
    "AFO Application information",
    registry=AFO_REGISTRY,
)


class PrometheusMiddleware:
    """Prometheus metrics middleware for FastAPI.

    Collects HTTP request metrics including:
    - Request count by method, endpoint, status code
    - Request duration
    - Request/response sizes
    - Active connections
    """

    def __init__(self, app: Any = None) -> None:
        self.app = app
        logger.info("PrometheusMiddleware initialized")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        """ASGI middleware entry point."""
        if scope["type"] != "http":
            # Non-HTTP requests (WebSocket, etc.) pass through
            if self.app:
                await self.app(scope, receive, send)
            return

        # Track active connections
        ACTIVE_CONNECTIONS.inc()

        request_start_time = time.time()
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "unknown")

        # Capture response info
        response_status = 0
        response_size = 0

        async def wrapped_send(message: dict) -> None:
            nonlocal response_status, response_size

            if message["type"] == "http.response.start":
                response_status = message.get("status", 0)
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_size += len(body)

            await send(message)

        try:
            if self.app:
                await self.app(scope, receive, wrapped_send)
        finally:
            # Record metrics
            duration = time.time() - request_start_time
            status_str = str(response_status)

            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=path,
                status_code=status_str,
            ).inc()

            HTTP_REQUEST_DURATION.labels(
                method=method,
                endpoint=path,
            ).observe(duration)

            HTTP_RESPONSE_SIZE.labels(
                method=method,
                endpoint=path,
            ).observe(response_size)

            ACTIVE_CONNECTIONS.dec()


async def metrics_endpoint() -> str:
    """Prometheus metrics endpoint.

    Returns:
        Prometheus exposition format metrics.
    """
    return generate_latest(AFO_REGISTRY).decode("utf-8")


def setup_prometheus(app: FastAPI) -> None:
    """Setup Prometheus middleware on FastAPI app.

    Args:
        app: FastAPI application instance
    """
    from fastapi.responses import PlainTextResponse

    # Add middleware
    app.add_middleware(PrometheusMiddleware)

    # Add metrics endpoint
    @app.get("/metrics", response_class=PlainTextResponse)
    async def get_metrics() -> PlainTextResponse:
        content = await metrics_endpoint()
        return PlainTextResponse(
            content=content,
            media_type=CONTENT_TYPE_LATEST,
        )

    # Set app info
    APP_INFO.info(
        {
            "version": "1.0.0",
            "phase": "117",
        }
    )

    logger.info("Prometheus middleware setup complete")


def update_trinity_score(pillar: str, score: float) -> None:
    """Update Trinity Score metric for a specific pillar.

    Args:
        pillar: Pillar name (眞, 善, 美, 孝, 永)
        score: Score value (0-100)
    """
    TRINITY_SCORE.labels(pillar=pillar).set(score)
    logger.debug(f"Trinity Score updated: {pillar}={score}")


def update_trinity_score_total(score: float) -> None:
    """Update total Trinity Score.

    Args:
        score: Total score (0-100)
    """
    TRINITY_SCORE_TOTAL.set(score)
    logger.debug(f"Total Trinity Score updated: {score}")


def record_trinity_check(result: str) -> None:
    """Record a Trinity check result.

    Args:
        result: Check result ("pass", "fail", "warn")
    """
    TRINITY_CHECKS_TOTAL.labels(result=result).inc()


def update_organ_health(organ_name: str, health_score: float) -> None:
    """Update organ health metric.

    Args:
        organ_name: Name of the organ (心, 肝, 腦, etc.)
        health_score: Health score (0-100)
    """
    ORGAN_HEALTH.labels(organ_name=organ_name).set(health_score)
    logger.debug(f"Organ health updated: {organ_name}={health_score}")


def update_organ_response_time(organ_name: str, response_time_ms: float) -> None:
    """Update organ response time metric.

    Args:
        organ_name: Name of the organ
        response_time_ms: Response time in milliseconds
    """
    ORGAN_RESPONSE_TIME.labels(organ_name=organ_name).set(response_time_ms)


def record_organ_error(organ_name: str, error_type: str) -> None:
    """Record an organ error.

    Args:
        organ_name: Name of the organ
        error_type: Type of error
    """
    ORGAN_ERRORS_TOTAL.labels(
        organ_name=organ_name,
        error_type=error_type,
    ).inc()
    logger.warning(f"Organ error recorded: {organ_name} - {error_type}")


__all__ = [
    "PrometheusMiddleware",
    "metrics_endpoint",
    "setup_prometheus",
    "AFO_REGISTRY",
    # Metric update functions
    "update_trinity_score",
    "update_trinity_score_total",
    "record_trinity_check",
    "update_organ_health",
    "update_organ_response_time",
    "record_organ_error",
    # Metric objects (for direct access)
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION",
    "TRINITY_SCORE",
    "ORGAN_HEALTH",
]
