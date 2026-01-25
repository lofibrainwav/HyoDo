"""
System Health Monitoring Service (Phase 62)
Provides real-time health metrics, alerts, and performance data.
"""

from collections import deque
from datetime import datetime
from typing import Any

import psutil


class SystemHealthService:
    """Monitors system health and generates alerts."""

    def __init__(self) -> None:
        self.alerts: deque[dict[str, Any]] = deque(maxlen=50)
        self.metrics_history: deque[dict[str, Any]] = deque(maxlen=100)
        self._thresholds = {
            "cpu_critical": 90,
            "cpu_warning": 70,
            "memory_critical": 90,
            "memory_warning": 80,
            "disk_critical": 95,
            "disk_warning": 85,
        }

    def get_current_metrics(self) -> dict[str, Any]:
        """Get current system metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        # Network I/O
        try:
            net_io = psutil.net_io_counters()
            network = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
            }
        except Exception:
            network = {"bytes_sent": 0, "bytes_recv": 0}

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "count": psutil.cpu_count(),
                "status": self._get_status("cpu", cpu_percent),
            },
            "memory": {
                "used_percent": memory.percent,
                "used_gb": round(memory.used / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "status": self._get_status("memory", memory.percent),
            },
            "disk": {
                "used_percent": disk.percent,
                "used_gb": round(disk.used / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "status": self._get_status("disk", disk.percent),
            },
            "network": network,
        }

        # Check for alerts
        self._check_alerts(metrics)

        # Store in history
        self.metrics_history.append(metrics)

        return metrics

    def _get_status(self, metric_type: str, value: float) -> str:
        """Determine status based on thresholds."""
        critical = self._thresholds.get(f"{metric_type}_critical", 90)
        warning = self._thresholds.get(f"{metric_type}_warning", 70)

        if value >= critical:
            return "critical"
        elif value >= warning:
            return "warning"
        return "healthy"

    def _check_alerts(self, metrics: dict[str, Any]) -> None:
        """Check metrics and generate alerts if needed."""
        timestamp = metrics["timestamp"]

        # CPU Alert
        if metrics["cpu"]["status"] == "critical":
            self._add_alert(
                "critical", "CPU", f"CPU usage at {metrics['cpu']['percent']}%", timestamp
            )
        elif metrics["cpu"]["status"] == "warning":
            self._add_alert(
                "warning", "CPU", f"High CPU usage: {metrics['cpu']['percent']}%", timestamp
            )

        # Memory Alert
        if metrics["memory"]["status"] == "critical":
            self._add_alert(
                "critical",
                "Memory",
                f"Memory usage at {metrics['memory']['used_percent']}%",
                timestamp,
            )
        elif metrics["memory"]["status"] == "warning":
            self._add_alert(
                "warning",
                "Memory",
                f"High memory usage: {metrics['memory']['used_percent']}%",
                timestamp,
            )

        # Disk Alert
        if metrics["disk"]["status"] == "critical":
            self._add_alert(
                "critical", "Disk", f"Disk usage at {metrics['disk']['used_percent']}%", timestamp
            )
        elif metrics["disk"]["status"] == "warning":
            self._add_alert(
                "warning", "Disk", f"High disk usage: {metrics['disk']['used_percent']}%", timestamp
            )

    def _add_alert(self, severity: str, source: str, message: str, timestamp: str) -> None:
        """Add an alert to the alerts queue."""
        alert = {
            "id": f"ALERT-{len(self.alerts) + 1:04d}",
            "severity": severity,
            "source": source,
            "message": message,
            "timestamp": timestamp,
            "acknowledged": False,
        }
        self.alerts.appendleft(alert)

    def get_alerts(
        self, limit: int = 20, unacknowledged_only: bool = False
    ) -> list[dict[str, Any]]:
        """Get recent alerts."""
        alerts_list = list(self.alerts)
        if unacknowledged_only:
            alerts_list = [a for a in alerts_list if not a["acknowledged"]]
        return alerts_list[:limit]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                return True
        return False

    def get_health_summary(self) -> dict[str, Any]:
        """Get overall health summary."""
        metrics = self.get_current_metrics()

        statuses = [
            metrics["cpu"]["status"],
            metrics["memory"]["status"],
            metrics["disk"]["status"],
        ]

        if "critical" in statuses:
            overall = "critical"
        elif "warning" in statuses:
            overall = "warning"
        else:
            overall = "healthy"

        unack_alerts = len([a for a in self.alerts if not a["acknowledged"]])

        return {
            "overall_status": overall,
            "unacknowledged_alerts": unack_alerts,
            "components": {
                "cpu": metrics["cpu"]["status"],
                "memory": metrics["memory"]["status"],
                "disk": metrics["disk"]["status"],
            },
            "metrics": metrics,
            "last_check": metrics["timestamp"],
        }

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get aggregated performance metrics."""
        if not self.metrics_history:
            return {"error": "No history available"}

        cpu_avg = sum(m["cpu"]["percent"] for m in self.metrics_history) / len(self.metrics_history)
        mem_avg = sum(m["memory"]["used_percent"] for m in self.metrics_history) / len(
            self.metrics_history
        )

        cpu_max = max(m["cpu"]["percent"] for m in self.metrics_history)
        mem_max = max(m["memory"]["used_percent"] for m in self.metrics_history)

        return {
            "sample_count": len(self.metrics_history),
            "cpu": {
                "average": round(cpu_avg, 1),
                "max": round(cpu_max, 1),
                "current": self.metrics_history[-1]["cpu"]["percent"],
            },
            "memory": {
                "average": round(mem_avg, 1),
                "max": round(mem_max, 1),
                "current": self.metrics_history[-1]["memory"]["used_percent"],
            },
            "uptime_estimate": "unknown",  # Would need system uptime tracking
            "timestamp": datetime.now().isoformat(),
        }


# Singleton instance
_health_service: SystemHealthService | None = None


def get_health_service() -> SystemHealthService:
    """Get or create the health service singleton."""
    global _health_service
    if _health_service is None:
        _health_service = SystemHealthService()
    return _health_service
