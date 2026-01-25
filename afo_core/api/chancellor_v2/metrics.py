from __future__ import annotations

import contextlib
import logging
from pathlib import Path

from prometheus_client import Counter, Gauge

"""Chancellor Graph V2 - Prometheus Metrics.

Exposes metrics for AlertManager integration.
"""


logger = logging.getLogger(__name__)

# Try to import prometheus_client, gracefully degrade if not available
try:
    PROMETHEUS_AVAILABLE = True

    # V2 execution metrics
    chancellor_v2_trace_created_total = Counter(
        "chancellor_v2_trace_created_total",
        "Total number of V2 traces created",
    )

    chancellor_v2_verify_pass_total = Counter(
        "chancellor_v2_verify_pass_total",
        "Total number of V2 VERIFY passes",
    )

    chancellor_v2_verify_fail_total = Counter(
        "chancellor_v2_verify_fail_total",
        "Total number of V2 VERIFY failures",
    )

    chancellor_v2_execute_blocked_total = Counter(
        "chancellor_v2_execute_blocked_total",
        "Total number of V2 EXECUTE blocked by Allowlist",
    )

    chancellor_v2_execute_success_total = Counter(
        "chancellor_v2_execute_success_total",
        "Total number of V2 EXECUTE successes",
    )

    chancellor_v2_execute_error_total = Counter(
        "chancellor_v2_execute_error_total",
        "Total number of V2 EXECUTE errors",
    )

    # Artifacts gauge
    chancellor_v2_artifacts_bytes = Gauge(
        "chancellor_v2_artifacts_bytes",
        "Total bytes used by V2 artifacts",
    )

    chancellor_v2_traces_count = Gauge(
        "chancellor_v2_traces_count",
        "Current number of V2 traces stored",
    )

except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available, metrics disabled")

    # Stub implementations
    class _StubCounter:
        def inc(self, _amount: float = 1) -> None:
            pass

    class _StubGauge:
        def set(self, _value: float) -> None:
            pass

    chancellor_v2_trace_created_total = _StubCounter()
    chancellor_v2_verify_pass_total = _StubCounter()
    chancellor_v2_verify_fail_total = _StubCounter()
    chancellor_v2_execute_blocked_total = _StubCounter()
    chancellor_v2_execute_success_total = _StubCounter()
    chancellor_v2_execute_error_total = _StubCounter()
    chancellor_v2_artifacts_bytes = _StubGauge()
    chancellor_v2_traces_count = _StubGauge()


def update_artifact_metrics() -> None:
    """Update artifact-related gauges from disk state."""
    if not PROMETHEUS_AVAILABLE:
        return

    events_dir = Path("artifacts/chancellor_events")
    checkpoints_dir = Path("artifacts/chancellor_checkpoints")

    total_bytes = 0
    trace_count = 0

    if events_dir.exists():
        for f in events_dir.glob("*.jsonl"):
            try:
                total_bytes += f.stat().st_size
                trace_count += 1
            except FileNotFoundError:
                pass

    if checkpoints_dir.exists():
        for d in checkpoints_dir.iterdir():
            if d.is_dir():
                for f in d.rglob("*"):
                    if f.is_file():
                        with contextlib.suppress(FileNotFoundError):
                            total_bytes += f.stat().st_size

    chancellor_v2_artifacts_bytes.set(total_bytes)
    chancellor_v2_traces_count.set(trace_count)
