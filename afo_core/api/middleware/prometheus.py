# Trinity Score: 90.0 (Established by Chancellor)
"""Prometheus Metrics Middleware for AFO Kingdom API

Provides comprehensive monitoring metrics including:
- HTTP request/response metrics
- Trinity score tracking
- API performance monitoring
- Error rate tracking
"""

import time
from collections.abc import Callable

import prometheus_client as prom
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# HTTP Metrics
REQUEST_COUNT = prom.Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code", "service"],
)

REQUEST_LATENCY = prom.Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint", "status_code", "service"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
)

# Business Logic Metrics
ACTIVE_CONNECTIONS = prom.Gauge("active_connections", "Number of active connections", ["service"])

TRINITY_SCORE = prom.Gauge(
    "trinity_score",
    "Current Trinity score (Truth/Goodness/Beauty)",
    ["pillar", "service"],
)

SKILLS_EXECUTIONS = prom.Counter(
    "skills_executions_total",
    "Total number of skill executions",
    ["skill_id", "category", "status"],
)

API_ERRORS = prom.Counter(
    "api_errors_total",
    "Total number of API errors",
    ["error_type", "endpoint", "service"],
)

# System Metrics
MEMORY_USAGE = prom.Gauge("memory_usage_bytes", "Current memory usage in bytes", ["service"])

CPU_USAGE = prom.Gauge("cpu_usage_percent", "Current CPU usage percentage", ["service"])


class PrometheusMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for Prometheus metrics collection"""

    def __init__(self, app, service_name: str = "afo-kingdom-api") -> None:
        super().__init__(app)
        self.service_name = service_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Increment active connections
        ACTIVE_CONNECTIONS.labels(service=self.service_name).inc()

        # Record request start time
        start_time = time.time()

        # Extract endpoint info
        endpoint = self._get_endpoint_path(request)

        try:
            # Process the request
            response = await call_next(request)

            # Calculate latency
            latency = time.time() - start_time

            # Record metrics
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(response.status_code),
                service=self.service_name,
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(response.status_code),
                service=self.service_name,
            ).observe(latency)

            # Record errors
            if response.status_code >= 400:
                API_ERRORS.labels(
                    error_type=self._get_error_type(response.status_code),
                    endpoint=endpoint,
                    service=self.service_name,
                ).inc()

            return response  # type: ignore[no-any-return]

        except Exception:
            # Record exception metrics
            latency = time.time() - start_time

            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code="500",
                service=self.service_name,
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=endpoint,
                status_code="500",
                service=self.service_name,
            ).observe(latency)

            API_ERRORS.labels(
                error_type="exception", endpoint=endpoint, service=self.service_name
            ).inc()

            raise

        finally:
            # Decrement active connections
            ACTIVE_CONNECTIONS.labels(service=self.service_name).dec()

    def _get_endpoint_path(self, request: Request) -> str:
        """Extract clean endpoint path for metrics"""
        path = request.url.path

        # Remove path parameters (e.g., /api/skills/detail/123 -> /api/skills/detail/{id})
        for param in request.path_params:
            if param in path:
                path = path.replace(str(request.path_params[param]), f"{{{param}}}")

        return path

    def _get_error_type(self, status_code: int) -> str:
        """Categorize error types based on status code"""
        if status_code >= 500:
            return "server_error"
        elif status_code >= 400:
            return "client_error"
        else:
            return "unknown"


# Utility functions for business metrics
def record_trinity_score(pillar: str, score: float, service: str = "afo-kingdom-api") -> None:
    """Record Trinity score metrics"""
    TRINITY_SCORE.labels(pillar=pillar, service=service).set(score)


def record_skill_execution(skill_id: str, category: str, status: str = "success") -> None:
    """Record skill execution metrics"""
    SKILLS_EXECUTIONS.labels(skill_id=skill_id, category=category, status=status).inc()


def record_memory_usage(bytes_used: int, service: str = "afo-kingdom-api") -> None:
    """Record memory usage metrics"""
    MEMORY_USAGE.labels(service=service).set(bytes_used)


def record_cpu_usage(percent: float, service: str = "afo-kingdom-api") -> None:
    """Record CPU usage metrics"""
    CPU_USAGE.labels(service=service).set(percent)


# Health check endpoint for metrics
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    # Use the same registry as utils/metrics.py for consistency
    from AFO.utils.metrics import get_metrics_response

    return await get_metrics_response()


# Middleware factory function
def create_prometheus_middleware(service_name: str = "afo-kingdom-api") -> None:
    """Factory function to create Prometheus middleware"""

    def middleware_factory(app) -> None:
        return PrometheusMiddleware(app, service_name=service_name)

    return middleware_factory
