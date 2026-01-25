from __future__ import annotations

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
    get_all_circuit_statuses,
    ollama_circuit,
    qdrant_circuit,
    redis_circuit,
)
from .exponential_backoff import (
    BackoffStrategies,
    ExponentialBackoff,
    retry_with_exponential_backoff,
)
from .metrics import (
    MetricsMiddleware,
    create_metrics_router,
    get_metrics_response,
    track_llm_call,
    track_ollama_call,
    update_circuit_breaker_metrics,
    update_organ_health,
    update_trinity_scores,
)

# Trinity Score: 90.0 (Established by Chancellor)
"""
AFO Soul Engine Utilities

유틸리티 함수 및 클래스 모음
"""


# Circuit Breaker (Phase 5: Monitoring)
try:
    CIRCUIT_BREAKER_AVAILABLE = True
except ImportError:
    CIRCUIT_BREAKER_AVAILABLE = False
    CircuitBreaker = None
    CircuitBreakerOpenError = None
    CircuitState = None
    get_all_circuit_statuses = None
    ollama_circuit = None
    qdrant_circuit = None
    redis_circuit = None

# Prometheus Metrics (Phase 5: Monitoring)
try:
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    MetricsMiddleware = None
    create_metrics_router = None
    get_metrics_response = None
    track_llm_call = None
    track_ollama_call = None
    update_circuit_breaker_metrics = None
    update_organ_health = None
    update_trinity_scores = None

__all__ = [
    "CIRCUIT_BREAKER_AVAILABLE",
    "METRICS_AVAILABLE",
    "BackoffStrategies",
    "ExponentialBackoff",
    "retry_with_exponential_backoff",
    # Circuit breaker exports (if available)
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    "CircuitState",
    "get_all_circuit_statuses",
    "ollama_circuit",
    "qdrant_circuit",
    "redis_circuit",
    # Metrics exports (if available)
    "MetricsMiddleware",
    "create_metrics_router",
    "get_metrics_response",
    "track_llm_call",
    "track_ollama_call",
    "update_circuit_breaker_metrics",
    "update_organ_health",
    "update_trinity_scores",
]
