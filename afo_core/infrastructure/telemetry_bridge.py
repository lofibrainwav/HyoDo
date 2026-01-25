"""Telemetry Bridge - Phase 80 Core Infrastructure

Connects Prometheus metrics to Trinity Score routing for intelligent decision making.
Implements Active Inference pattern: metrics → entropy → Chancellor routing.

Author: AFO Kingdom Phase 80
Trinity Score: 眞(Truth) - Observability Foundation
"""

import asyncio
import inspect
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

import httpx

logger = logging.getLogger("afo.infrastructure.telemetry_bridge")

# Configuration
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
TELEMETRY_BRIDGE_ENABLED = os.getenv("TELEMETRY_BRIDGE_ENABLED", "true").lower() == "true"
ENTROPY_THRESHOLD = float(os.getenv("ENTROPY_THRESHOLD", "0.5"))
SCRAPE_INTERVAL_SECONDS = int(os.getenv("TELEMETRY_SCRAPE_INTERVAL", "30"))


class AlertSeverity(Enum):
    """Alert severity levels aligned with Trinity Score routing."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class TelemetryMetrics:
    """Current system metrics snapshot."""

    error_rate: float = 0.0
    request_latency_p99: float = 0.0
    memory_usage_percent: float = 0.0
    cpu_usage_percent: float = 0.0
    active_connections: int = 0
    irs_api_latency_ms: float = 0.0
    trinity_score: float = 100.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class TelemetryAlert:
    """Alert generated from telemetry analysis."""

    alert_id: str
    severity: AlertSeverity
    source: str
    message: str
    metrics: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    acknowledged: bool = False


class TelemetryBridge:
    """Bridge between Prometheus metrics and Trinity Score routing.

    Implements the Active Inference pattern:
    1. Observe: Scrape Prometheus metrics
    2. Analyze: Calculate entropy/surprise
    3. Route: Trigger Chancellor decisions based on entropy

    Usage:
        bridge = TelemetryBridge()
        await bridge.start()
        # Bridge runs continuously, routing decisions automatically
        await bridge.stop()
    """

    def __init__(self) -> None:
        self.enabled = TELEMETRY_BRIDGE_ENABLED
        self.prometheus_url = PROMETHEUS_URL
        self.entropy_threshold = ENTROPY_THRESHOLD
        self.scrape_interval = SCRAPE_INTERVAL_SECONDS

        self.running = False
        self.current_metrics = TelemetryMetrics()
        self.current_entropy: float = 0.0
        self.alerts: list[TelemetryAlert] = []
        self._alert_handlers: list[Any] = []

        logger.info(
            f"TelemetryBridge initialized (enabled={self.enabled}, "
            f"threshold={self.entropy_threshold})"
        )

    def register_alert_handler(self, handler: Any) -> None:
        """Register a handler to receive alerts when entropy exceeds threshold."""
        self._alert_handlers.append(handler)
        logger.info(f"Registered alert handler: {handler}")

    async def start(self) -> None:
        """Start the telemetry bridge background loop."""
        if not self.enabled:
            logger.warning("TelemetryBridge is disabled, skipping start")
            return

        self.running = True
        logger.info("TelemetryBridge starting observation loop...")

        while self.running:
            try:
                await self._observe_metrics()
                await self._analyze_entropy()
                await self._route_if_needed()
            except Exception as e:
                logger.error(f"TelemetryBridge loop error: {e}")

            await asyncio.sleep(self.scrape_interval)

    async def stop(self) -> None:
        """Stop the telemetry bridge."""
        self.running = False
        logger.info("TelemetryBridge stopped")

    async def _observe_metrics(self) -> None:
        """Scrape metrics from Prometheus."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Error rate
                self.current_metrics.error_rate = await self._query_prometheus(
                    client, "sum(rate(afo_errors_total[5m])) or vector(0)"
                )

                # Request latency P99
                self.current_metrics.request_latency_p99 = await self._query_prometheus(
                    client,
                    "histogram_quantile(0.99, rate(afo_request_duration_seconds_bucket[5m])) "
                    "or vector(0)",
                )

                # Memory usage
                self.current_metrics.memory_usage_percent = await self._query_prometheus(
                    client, "afo_memory_usage_percent or vector(0)"
                )

                # CPU usage
                self.current_metrics.cpu_usage_percent = await self._query_prometheus(
                    client, "afo_cpu_usage_percent or vector(0)"
                )

                # IRS API latency
                self.current_metrics.irs_api_latency_ms = await self._query_prometheus(
                    client,
                    "avg(afo_irs_api_latency_seconds) * 1000 or vector(0)",
                )

                # Active connections
                self.current_metrics.active_connections = int(
                    await self._query_prometheus(client, "afo_active_connections or vector(0)")
                )

                self.current_metrics.timestamp = datetime.now(UTC)
                logger.debug(f"Metrics observed: error_rate={self.current_metrics.error_rate:.4f}")

        except httpx.ConnectError:
            logger.debug("Prometheus unavailable, using cached metrics")
        except Exception as e:
            logger.warning(f"Metrics observation failed: {e}")

    async def _query_prometheus(self, client: httpx.AsyncClient, query: str) -> float:
        """Execute a Prometheus query and return the value."""
        try:
            response = await client.get(
                f"{self.prometheus_url}/api/v1/query",
                params={"query": query},
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    results = data.get("data", {}).get("result", [])
                    if results:
                        return float(results[0].get("value", [0, 0])[1])
            return 0.0
        except Exception:
            return 0.0

    async def _analyze_entropy(self) -> None:
        """Calculate system entropy based on observed metrics.

        Entropy represents "surprise" or deviation from expected state.
        Higher entropy = more anomalous behavior = more likely to need intervention.
        """
        # Weighted entropy calculation
        weights = {
            "error_rate": 0.35,  # 眞 - Truth (most critical)
            "latency": 0.25,  # 善 - Goodness (user experience)
            "memory": 0.20,  # 美 - Beauty (system elegance)
            "cpu": 0.10,  # 孝 - Serenity (resource harmony)
            "irs": 0.10,  # 永 - Eternity (external integration)
        }

        # Normalize metrics to 0-1 scale
        error_entropy = min(self.current_metrics.error_rate * 100, 1.0)
        latency_entropy = min(self.current_metrics.request_latency_p99 / 5.0, 1.0)  # 5s = max
        memory_entropy = self.current_metrics.memory_usage_percent / 100.0
        cpu_entropy = self.current_metrics.cpu_usage_percent / 100.0
        irs_entropy = min(self.current_metrics.irs_api_latency_ms / 5000, 1.0)  # 5s = max

        # Weighted sum
        self.current_entropy = (
            weights["error_rate"] * error_entropy
            + weights["latency"] * latency_entropy
            + weights["memory"] * memory_entropy
            + weights["cpu"] * cpu_entropy
            + weights["irs"] * irs_entropy
        )

        # Update Trinity Score (inverse of entropy)
        self.current_metrics.trinity_score = max(0, (1 - self.current_entropy) * 100)

        logger.debug(
            f"Entropy calculated: {self.current_entropy:.4f}, "
            f"Trinity Score: {self.current_metrics.trinity_score:.1f}"
        )

    async def _route_if_needed(self) -> None:
        """Trigger Chancellor routing if entropy exceeds threshold."""
        if self.current_entropy <= self.entropy_threshold:
            return

        # Determine severity based on entropy level
        if self.current_entropy > 0.8:
            severity = AlertSeverity.EMERGENCY
        elif self.current_entropy > 0.65:
            severity = AlertSeverity.CRITICAL
        elif self.current_entropy > 0.5:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.INFO

        # Create alert
        alert = TelemetryAlert(
            alert_id=f"TELEM-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            severity=severity,
            source="TelemetryBridge",
            message=self._generate_alert_message(),
            metrics={
                "error_rate": self.current_metrics.error_rate,
                "latency_p99": self.current_metrics.request_latency_p99,
                "memory_percent": self.current_metrics.memory_usage_percent,
                "entropy": self.current_entropy,
                "trinity_score": self.current_metrics.trinity_score,
            },
        )

        self.alerts.append(alert)
        logger.warning(
            f"Alert generated: {alert.alert_id} [{severity.value}] - "
            f"Entropy: {self.current_entropy:.4f}"
        )

        # Notify handlers
        for handler in self._alert_handlers:
            try:
                if inspect.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Alert handler error: {e}")

    def _generate_alert_message(self) -> str:
        """Generate a human-readable alert message."""
        issues = []

        if self.current_metrics.error_rate > 0.01:
            issues.append(f"High error rate: {self.current_metrics.error_rate:.4f}")
        if self.current_metrics.request_latency_p99 > 2.0:
            issues.append(f"High latency: {self.current_metrics.request_latency_p99:.2f}s")
        if self.current_metrics.memory_usage_percent > 85:
            issues.append(f"Memory pressure: {self.current_metrics.memory_usage_percent:.1f}%")
        if self.current_metrics.irs_api_latency_ms > 2000:
            issues.append(f"IRS API slow: {self.current_metrics.irs_api_latency_ms:.0f}ms")

        if issues:
            return "System anomaly detected: " + "; ".join(issues)
        return f"Elevated entropy: {self.current_entropy:.4f}"

    def get_current_state(self) -> dict[str, Any]:
        """Get current telemetry state for external consumers."""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "entropy": self.current_entropy,
            "trinity_score": self.current_metrics.trinity_score,
            "metrics": {
                "error_rate": self.current_metrics.error_rate,
                "latency_p99_seconds": self.current_metrics.request_latency_p99,
                "memory_percent": self.current_metrics.memory_usage_percent,
                "cpu_percent": self.current_metrics.cpu_usage_percent,
                "active_connections": self.current_metrics.active_connections,
                "irs_latency_ms": self.current_metrics.irs_api_latency_ms,
            },
            "last_update": self.current_metrics.timestamp.isoformat(),
            "active_alerts": len([a for a in self.alerts if not a.acknowledged]),
        }

    def get_recent_alerts(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent alerts for display."""
        return [
            {
                "alert_id": a.alert_id,
                "severity": a.severity.value,
                "source": a.source,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "acknowledged": a.acknowledged,
            }
            for a in sorted(self.alerts, key=lambda x: x.timestamp, reverse=True)[:limit]
        ]


# Singleton instance for global access
_telemetry_bridge: TelemetryBridge | None = None


def get_telemetry_bridge() -> TelemetryBridge:
    """Get or create the global TelemetryBridge instance."""
    global _telemetry_bridge
    if _telemetry_bridge is None:
        _telemetry_bridge = TelemetryBridge()
    return _telemetry_bridge


async def start_telemetry_bridge() -> None:
    """Start the global telemetry bridge."""
    bridge = get_telemetry_bridge()
    await bridge.start()
