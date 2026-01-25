# Trinity Score: 90.0 (Established by Chancellor)
"""OpenTelemetry AI Observability Module (TICKET-099)
Real-time monitoring and performance tracking for AFO Kingdom agents.

Features:
- Agent behavior tracing with spans
- Performance metrics (latency, throughput, error rates)
- Compliance violation detection
- Integration with existing observability stack

Philosophy:
- 眞 (Truth): Accurate, unbiased measurement of system behavior
- 善 (Goodness): Early detection of issues before they impact users
- 美 (Beauty): Clear, actionable dashboards and alerts
"""

import inspect
import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

logger = logging.getLogger(__name__)


@dataclass
class Span:
    """A trace span representing a unit of work."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None
    start_time: float
    end_time: float | None = None
    status: str = "OK"
    attributes: dict[str, Any] = field(default_factory=lambda: {})
    events: list[dict[str, Any]] = field(default_factory=lambda: [])

    @property
    def duration_ms(self) -> float | None:
        if self.end_time:
            return (self.end_time - self.start_time) * 1000
        return None


@dataclass
class Metric:
    """A metric data point."""

    name: str
    value: float
    unit: str
    labels: dict[str, str] = field(default_factory=lambda: {})
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class AIObservability:
    """OpenTelemetry-inspired observability for AI agents.

    Provides:
    1. Distributed tracing for agent workflows
    2. Metrics collection for performance monitoring
    3. Compliance and anomaly alerting
    """

    def __init__(self, service_name: str = "afo-kingdom") -> None:
        self.service_name = service_name
        self._active_spans: dict[str, Span] = {}
        self._completed_spans: list[Span] = []
        self._metrics: list[Metric] = []

        # Performance thresholds for alerting
        self.thresholds = {
            "max_latency_ms": 5000,  # 5 seconds
            "max_error_rate": 0.05,  # 5%
            "min_throughput_per_min": 10,  # 10 operations
        }

        # Compliance rules
        self.compliance_rules = {
            "require_trinity_check": True,
            "require_governance_approval": True,
            "log_all_llm_calls": True,
        }

        self._trace_counter = 0
        self._span_counter = 0

    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        self._trace_counter += 1
        return f"trace-{self._trace_counter:08d}-{int(time.time() * 1000)}"

    def _generate_span_id(self) -> str:
        """Generate a unique span ID."""
        self._span_counter += 1
        return f"span-{self._span_counter:08d}"

    @contextmanager
    def trace(
        self, operation_name: str, parent_span_id: str | None = None, **attributes: Any
    ) -> Generator[Span, None, None]:
        """Context manager for tracing an operation.

        Usage:
            with observability.trace("llm_call", model="gpt-4") as span:
                result = call_llm(...)
                span.attributes["tokens"] = result.usage.total_tokens
        """
        trace_id = self._generate_trace_id()
        span_id = self._generate_span_id()

        span = Span(
            name=operation_name,
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            start_time=time.perf_counter(),
            attributes={
                "service.name": self.service_name,
                **attributes,
            },
        )

        self._active_spans[span_id] = span

        try:
            yield span
            span.status = "OK"
        except Exception as e:
            span.status = "ERROR"
            span.attributes["error.type"] = type(e).__name__
            span.attributes["error.message"] = str(e)
            raise
        finally:
            span.end_time = time.perf_counter()
            del self._active_spans[span_id]
            self._completed_spans.append(span)

            if span.duration_ms:
                self.record_metric(
                    name=f"{operation_name}.latency",
                    value=span.duration_ms,
                    unit="ms",
                    labels={"status": span.status},
                )

            # Persist span
            self._persist_span(span)

            # Check compliance
            self._check_compliance(span)

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "count",
        labels: dict[str, str] | None = None,
    ) -> None:
        """Record a metric data point."""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            labels=labels or {},
        )
        self._metrics.append(metric)

        # Check thresholds
        if name.endswith(".latency") and value > self.thresholds["max_latency_ms"]:
            logger.warning(f"[Observability] High latency alert: {name}={value}ms")

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        """Record LLM call metrics."""
        self.record_metric("llm.calls", 1, labels={"model": model, "success": str(success)})
        self.record_metric("llm.prompt_tokens", prompt_tokens, labels={"model": model})
        self.record_metric("llm.completion_tokens", completion_tokens, labels={"model": model})
        self.record_metric("llm.latency", latency_ms, unit="ms", labels={"model": model})
        self.record_metric(
            "llm.total_tokens",
            prompt_tokens + completion_tokens,
            labels={"model": model},
        )

    def record_agent_action(
        self,
        agent_name: str,
        action: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """Record agent action metrics."""
        self.record_metric(
            f"agent.{agent_name}.actions",
            1,
            labels={"action": action, "success": str(success)},
        )
        self.record_metric(
            f"agent.{agent_name}.latency",
            duration_ms,
            unit="ms",
            labels={"action": action},
        )

    def _check_compliance(self, span: Span) -> None:
        """Check span for compliance violations."""
        violations: list[str] = []

        # Check if Trinity check was performed
        if (
            self.compliance_rules["require_trinity_check"]
            and "trinity_score" not in span.attributes
        ):
            violations.append("missing_trinity_check")

        # Check if governance approval was obtained for certain operations
        if self.compliance_rules["require_governance_approval"]:
            sensitive_ops = ["file_write", "api_call", "execute_code"]
            if span.name in sensitive_ops and "governance_approved" not in span.attributes:
                violations.append("missing_governance_approval")

        if violations:
            logger.warning(f"[Observability] Compliance violations in {span.name}: {violations}")
            span.attributes["compliance_violations"] = violations

    def _persist_span(self, span: Span) -> None:
        """Persist span to file for analysis."""
        try:
            traces_dir = (
                Path(__file__).parent.parent.parent.parent.parent / "docs" / "ssot" / "traces"
            )
            traces_dir.mkdir(parents=True, exist_ok=True)

            import json
            from dataclasses import asdict

            trace_file = traces_dir / "traces.jsonl"
            with trace_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(asdict(span), ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist span: {e}")

    def get_metrics_summary(self, last_n_minutes: int = 5) -> dict[str, Any]:
        """Get summary of recent metrics."""
        from collections import defaultdict

        cutoff = time.time() - (last_n_minutes * 60)
        recent_metrics = [
            m
            for m in self._metrics
            if datetime.fromisoformat(m.timestamp.replace("Z", "+00:00")).timestamp() > cutoff
        ]

        # Aggregate by name
        aggregated: dict[str, list[float]] = defaultdict(list)
        for m in recent_metrics:
            aggregated[m.name].append(m.value)

        summary = {}
        for name, values in aggregated.items():
            summary[name] = {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
            }

        return summary

    def get_trace_summary(self) -> dict[str, Any]:
        """Get summary of traces."""
        total_spans = len(self._completed_spans)
        error_spans = sum(1 for s in self._completed_spans if s.status == "ERROR")

        latencies = [s.duration_ms for s in self._completed_spans if s.duration_ms]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return {
            "total_spans": total_spans,
            "error_count": error_spans,
            "error_rate": error_spans / total_spans if total_spans > 0 else 0,
            "avg_latency_ms": avg_latency,
            "active_spans": len(self._active_spans),
        }


# Singleton instance
observability = AIObservability()


P = ParamSpec("P")
R = TypeVar("R")


# Convenience decorator for tracing functions
# Note: This decorator handles both sync and async functions. The type: ignore
# comments are necessary because Python's type system cannot express a decorator
# that preserves the async/sync nature of the decorated function. The runtime
# behavior is correct - async functions return coroutines, sync functions return
# their normal return type.
def traced(
    operation_name: str | None = None, **default_attributes: Any
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Decorator to automatically trace a function.

    Works with both sync and async functions. The tracing context is
    automatically managed around the function execution.
    """

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        op_name = operation_name or func.__name__

        @wraps(func)
        async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with observability.trace(op_name, **default_attributes):
                # type: ignore is safe - func is verified async by iscoroutinefunction
                return await func(*args, **kwargs)  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            with observability.trace(op_name, **default_attributes):
                return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            # type: ignore is safe - async_wrapper matches func's async signature
            return async_wrapper  # type: ignore[return-value]
        return sync_wrapper

    return decorator
