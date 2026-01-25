from __future__ import annotations

import time
from functools import wraps
from typing import TYPE_CHECKING, Any, TypeVar

from fastapi import APIRouter
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request

# Trinity Score: 90.0 (Established by Chancellor)
"""Prometheus Metrics for AFO Kingdom
Provides observability for the Soul Engine API.
"""


try:
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("⚠️ prometheus_client not installed. Run: pip install prometheus-client")


T = TypeVar("T")

# ============================================================================
# Core Metrics Definition
# ============================================================================

if PROMETHEUS_AVAILABLE:

    def get_or_create_metric(
        metric_class: type[Any],
        name: str,
        documentation: str,
        labelnames: tuple[str, ...] = (),
        **kwargs: Any,
    ) -> Any:
        """Helper to avoid duplicated timeseries error."""
        if name in REGISTRY._names_to_collectors:
            return REGISTRY._names_to_collectors[name]
        return metric_class(name, documentation, labelnames, **kwargs)

    # HTTP Request Metrics
    http_requests_total = get_or_create_metric(
        Counter,
        "afo_http_requests_total",
        "Total HTTP requests",
        ("method", "endpoint", "status_code"),
    )

    http_request_duration_seconds = get_or_create_metric(
        Histogram,
        "afo_http_request_duration_seconds",
        "HTTP request duration in seconds",
        ("method", "endpoint"),
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

    # Circuit Breaker Metrics
    circuit_breaker_state = get_or_create_metric(
        Gauge,
        "afo_circuit_breaker_state",
        "Circuit breaker state (0=CLOSED, 1=OPEN, 2=HALF_OPEN)",
        ("service",),
    )

    circuit_breaker_failures = get_or_create_metric(
        Counter,
        "afo_circuit_breaker_failures_total",
        "Total circuit breaker failures",
        ("service",),
    )

    # Ollama Metrics
    ollama_calls_total = get_or_create_metric(
        Counter,
        "afo_ollama_calls_total",
        "Total Ollama API calls",
        ("status", "model"),  # status: success, failure, timeout
    )

    ollama_request_duration_seconds = get_or_create_metric(
        Histogram,
        "afo_ollama_request_duration_seconds",
        "Ollama request duration in seconds",
        ("model",),
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    )

    # LLM Routing Metrics
    llm_router_calls_total = get_or_create_metric(
        Counter,
        "afo_llm_router_calls_total",
        "Total LLM router calls",
        ("provider", "status"),  # provider: ollama, gemini, claude, openai
    )

    # CRAG Metrics
    crag_queries_total = get_or_create_metric(
        Counter,
        "afo_crag_queries_total",
        "Total CRAG queries",
        ("status",),  # status: success, no_docs, web_fallback
    )

    # Trinity Score Metrics
    trinity_score = get_or_create_metric(
        Gauge,
        "afo_trinity_score",
        "Current Trinity Score",
        ("pillar",),  # pillar: truth, goodness, beauty, serenity, eternity
    )

    trinity_score_total = get_or_create_metric(
        Gauge, "afo_trinity_score_total", "Total weighted Trinity Score"
    )

    # Health Metrics
    organ_health = get_or_create_metric(
        Gauge,
        "afo_organ_health",
        "Health status of organs (1=healthy, 0=unhealthy)",
        ("organ",),  # organ: redis, postgres, ollama, api_server
    )

    # Memory System Metrics
    memory_entries = get_or_create_metric(
        Gauge,
        "afo_memory_entries",
        "Number of memory entries",
        ("store",),  # store: short_term, long_term
    )

    # Log Analysis Metrics (TICKET-039)
    log_analysis_chunks_processed_total = get_or_create_metric(
        Counter,
        "afo_log_analysis_chunks_processed_total",
        "Total number of log chunks processed",
    )

    log_analysis_errors_total = get_or_create_metric(
        Counter,
        "afo_log_analysis_errors_total",
        "Total errors during log analysis",
        ("phase",),  # phase: parsing, analysis, reporting
    )

    log_analysis_processing_seconds = get_or_create_metric(
        Histogram,
        "afo_log_analysis_processing_seconds",
        "Time spent processing log chunks",
        buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0),
    )

# ============================================================================
# Metrics Middleware
# ============================================================================


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect HTTP metrics."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not PROMETHEUS_AVAILABLE:
            return await call_next(request)

        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        start_time = time.perf_counter()
        status_code = 500  # Default in case of exception

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration = time.perf_counter() - start_time
            endpoint = self._normalize_endpoint(request.url.path)

            http_requests_total.labels(
                method=request.method, endpoint=endpoint, status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(method=request.method, endpoint=endpoint).observe(
                duration
            )

    def _normalize_endpoint(self, path: str) -> str:
        """Normalize endpoint to avoid high cardinality."""
        # Replace UUIDs and IDs with placeholders
        parts = path.split("/")
        normalized = []
        for part in parts:
            # Check if it looks like an ID (UUID or numeric)
            if self._is_id(part):
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/".join(normalized)

    def _is_id(self, part: str) -> bool:
        """Check if a path part looks like an ID."""
        if not part:
            return False
        # UUID pattern
        if len(part) == 36 and part.count("-") == 4:
            return True
        # Numeric ID
        return bool(part.isdigit() and len(part) > 3)


# ============================================================================
# Decorator for Function Metrics
# ============================================================================


def track_ollama_call(
    model: str = "default",
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to track Ollama call metrics.

    Args:
        model: Ollama model name

    Returns:
        Decorator function

    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)

            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                ollama_calls_total.labels(status="success", model=model).inc()
                return result
            except TimeoutError:
                ollama_calls_total.labels(status="timeout", model=model).inc()
                raise
            except Exception:
                ollama_calls_total.labels(status="failure", model=model).inc()
                raise
            finally:
                duration = time.perf_counter() - start_time
                ollama_request_duration_seconds.labels(model=model).observe(duration)

        return wrapper

    return decorator


def track_llm_call(
    provider: str,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator to track LLM router calls.

    Args:
        provider: LLM provider name

    Returns:
        Decorator function

    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)

            try:
                result = await func(*args, **kwargs)
                llm_router_calls_total.labels(provider=provider, status="success").inc()
                return result
            except Exception:
                llm_router_calls_total.labels(provider=provider, status="failure").inc()
                raise

        return wrapper

    return decorator


# ============================================================================
# Circuit Breaker Metrics Integration
# ============================================================================


def update_circuit_breaker_metrics(service: str, state: str) -> None:
    """Update circuit breaker metrics.

    Args:
        service: Service name
        state: Circuit breaker state (closed/open/half_open)

    """
    if not PROMETHEUS_AVAILABLE:
        return

    state_value = {"closed": 0, "open": 1, "half_open": 2}.get(state.lower(), 0)
    circuit_breaker_state.labels(service=service).set(state_value)


def record_circuit_breaker_failure(service: str) -> None:
    """Record a circuit breaker failure.

    Args:
        service: Service name

    """
    if not PROMETHEUS_AVAILABLE:
        return

    circuit_breaker_failures.labels(service=service).inc()


# ============================================================================
# Health & Trinity Metrics
# ============================================================================


def update_organ_health(organ: str, is_healthy: bool) -> None:
    """Update organ health metric.

    Args:
        organ: Organ name
        is_healthy: Health status

    """
    if not PROMETHEUS_AVAILABLE:
        return

    organ_health.labels(organ=organ).set(1 if is_healthy else 0)


def update_trinity_scores(scores: dict[str, float]) -> None:
    """Update Trinity Score metrics.

    Args:
        scores: Dictionary of pillar scores

    """
    if not PROMETHEUS_AVAILABLE:
        return

    for pillar, value in scores.items():
        if pillar != "total":
            trinity_score.labels(pillar=pillar).set(value)

    if "total" in scores:
        trinity_score_total.set(scores["total"])


def update_memory_metrics(short_term: int, long_term: int) -> None:
    """Update memory system metrics.

    Args:
        short_term: Short-term memory entries count
        long_term: Long-term memory entries count

    """
    if not PROMETHEUS_AVAILABLE:
        return

    memory_entries.labels(store="short_term").set(short_term)
    memory_entries.labels(store="long_term").set(long_term)


# ============================================================================
# SSE Health Metrics
# ============================================================================

if PROMETHEUS_AVAILABLE:
    # SSE connection metrics
    sse_open_connections = get_or_create_metric(
        Gauge,
        "afo_sse_open_connections",
        "Number of currently open SSE connections",
    )

    sse_reconnect_count = get_or_create_metric(
        Counter,
        "afo_sse_reconnect_count_total",
        "Total number of SSE reconnection attempts",
    )

    sse_last_event_age_seconds = get_or_create_metric(
        Gauge,
        "afo_sse_last_event_age_seconds",
        "Time in seconds since the last SSE event was received",
    )

    sse_connection_status = get_or_create_metric(
        Gauge,
        "afo_sse_connection_status",
        "SSE connection status (0=down, 1=stale, 2=healthy)",
        labelnames=("status",),
    )


def update_sse_health_metrics(
    open_connections: int = 0,
    reconnect_count: int = 0,
    last_event_age_seconds: float = 0.0,
) -> None:
    """
    Update SSE health metrics.

    Args:
        open_connections: Number of currently open SSE connections
        reconnect_count: Total number of SSE reconnection attempts
        last_event_age_seconds: Time since last SSE event in seconds
    """
    if not PROMETHEUS_AVAILABLE:
        return

    # Update gauge metrics
    sse_open_connections.set(open_connections)
    sse_last_event_age_seconds.set(last_event_age_seconds)

    # Update counter metric (increment by the difference)
    # Note: This assumes reconnect_count is cumulative
    # Counter metrics don't have a simple _value access, just increment
    sse_reconnect_count.inc(reconnect_count)

    # Update status gauge based on age
    if last_event_age_seconds > 60:  # Down
        sse_connection_status.labels(status="down").set(1)
        sse_connection_status.labels(status="stale").set(0)
        sse_connection_status.labels(status="healthy").set(0)
    elif last_event_age_seconds > 30:  # Stale
        sse_connection_status.labels(status="down").set(0)
        sse_connection_status.labels(status="stale").set(1)
        sse_connection_status.labels(status="healthy").set(0)
    else:  # Healthy
        sse_connection_status.labels(status="down").set(0)
        sse_connection_status.labels(status="stale").set(0)
        sse_connection_status.labels(status="healthy").set(1)


# ============================================================================
# Metrics Endpoint Handler
# ============================================================================


async def get_metrics_response() -> Response:
    """Generate Prometheus metrics response."""
    if not PROMETHEUS_AVAILABLE:
        return Response(content="# prometheus_client not installed", media_type="text/plain")

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# ============================================================================
# FastAPI Router
# ============================================================================


def create_metrics_router() -> Any:
    """Create a FastAPI router for metrics endpoint.

    Returns:
        FastAPI router with /metrics endpoint

    """

    router = APIRouter(tags=["Metrics"])

    @router.get("/metrics")
    async def metrics() -> Response:
        """Prometheus metrics endpoint."""
        return await get_metrics_response()

    return router
