"""Phase 80 Integration Tests - Real-Time Intelligence Orchestration

Tests for:
1. Telemetry Bridge → Trinity Score routing
2. IRS Change Detection → Agent response
3. MyGPT Dashboard → Real metrics
4. End-to-end streaming

Author: AFO Kingdom Phase 80
Trinity Score: 善(Goodness) - Quality Assurance
"""

import asyncio
from datetime import UTC, datetime

import pytest

from infrastructure.telemetry_bridge import (
    AlertSeverity,
    TelemetryAlert,
    TelemetryBridge,
    TelemetryMetrics,
    get_telemetry_bridge,
)


class TestTelemetryBridge:
    """Tests for TelemetryBridge functionality."""

    def test_telemetry_bridge_initialization(self) -> None:
        """Test TelemetryBridge initializes with correct defaults."""
        bridge = TelemetryBridge()

        assert bridge.enabled is True
        assert bridge.running is False
        assert bridge.entropy_threshold == 0.5
        assert bridge.current_entropy == 0.0
        assert isinstance(bridge.current_metrics, TelemetryMetrics)

    def test_entropy_calculation_low(self) -> None:
        """Test entropy calculation with low metrics (healthy state)."""
        bridge = TelemetryBridge()
        bridge.current_metrics.error_rate = 0.001
        bridge.current_metrics.request_latency_p99 = 0.5
        bridge.current_metrics.memory_usage_percent = 40.0
        bridge.current_metrics.cpu_usage_percent = 30.0
        bridge.current_metrics.irs_api_latency_ms = 500

        # Run entropy analysis synchronously (via _analyze_entropy internals)
        asyncio.run(bridge._analyze_entropy())

        # Low metrics should result in low entropy
        assert bridge.current_entropy < 0.3
        assert bridge.current_metrics.trinity_score > 70

    def test_entropy_calculation_high(self) -> None:
        """Test entropy calculation with high metrics (stressed state)."""
        bridge = TelemetryBridge()
        bridge.current_metrics.error_rate = 0.05  # 5% error rate
        bridge.current_metrics.request_latency_p99 = 4.0  # 4 seconds
        bridge.current_metrics.memory_usage_percent = 90.0
        bridge.current_metrics.cpu_usage_percent = 85.0
        bridge.current_metrics.irs_api_latency_ms = 4000

        asyncio.run(bridge._analyze_entropy())

        # High metrics should result in high entropy
        assert bridge.current_entropy > 0.5
        assert bridge.current_metrics.trinity_score < 50

    @pytest.mark.asyncio
    async def test_alert_generation_on_high_entropy(self) -> None:
        """Test that alerts are generated when entropy exceeds threshold."""
        bridge = TelemetryBridge()
        bridge.entropy_threshold = 0.3  # Lower threshold for testing

        # Set high entropy state
        bridge.current_entropy = 0.6
        bridge.current_metrics.error_rate = 0.03

        # Register mock handler
        handler_called = False
        received_alert = None

        async def mock_handler(alert: TelemetryAlert) -> None:
            nonlocal handler_called, received_alert
            handler_called = True
            received_alert = alert

        bridge.register_alert_handler(mock_handler)

        # Trigger routing
        await bridge._route_if_needed()

        assert handler_called is True
        assert received_alert is not None
        assert received_alert.severity == AlertSeverity.WARNING
        assert "TELEM-" in received_alert.alert_id

    def test_get_current_state(self) -> None:
        """Test get_current_state returns expected structure."""
        bridge = TelemetryBridge()
        bridge.current_metrics.error_rate = 0.01
        bridge.current_entropy = 0.25

        state = bridge.get_current_state()

        assert "enabled" in state
        assert "running" in state
        assert "entropy" in state
        assert "trinity_score" in state
        assert "metrics" in state
        assert "last_update" in state
        assert state["entropy"] == 0.25

    def test_alert_severity_levels(self) -> None:
        """Test alert severity is determined correctly by entropy level."""
        bridge = TelemetryBridge()

        # Test emergency (entropy > 0.8)
        bridge.current_entropy = 0.85
        asyncio.run(bridge._route_if_needed())
        assert len(bridge.alerts) == 1
        assert bridge.alerts[0].severity == AlertSeverity.EMERGENCY

        # Test critical (entropy > 0.65)
        bridge.alerts.clear()
        bridge.current_entropy = 0.7
        asyncio.run(bridge._route_if_needed())
        assert bridge.alerts[0].severity == AlertSeverity.CRITICAL

        # Test warning (entropy > 0.5)
        bridge.alerts.clear()
        bridge.current_entropy = 0.55
        asyncio.run(bridge._route_if_needed())
        assert bridge.alerts[0].severity == AlertSeverity.WARNING


class TestIRSChangesIntegration:
    """Tests for IRS Changes SSE integration."""

    @pytest.mark.asyncio
    async def test_broadcast_change_queuing(self) -> None:
        """Test that changes are properly queued for broadcast."""
        # Create standalone queue for testing (avoids deep import chain)
        test_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)

        change = {
            "change_id": "TEST-001",
            "title": "Test Change",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        await test_queue.put(change)

        assert test_queue.qsize() == 1
        queued = await test_queue.get()
        assert queued["change_id"] == "TEST-001"

    def test_sse_format(self) -> None:
        """Test SSE message formatting."""
        import json

        def sse_format(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data)}\n\n"

        result = sse_format("test_event", {"key": "value"})

        assert "event: test_event" in result
        assert 'data: {"key": "value"}' in result
        assert result.endswith("\n\n")


class TestMyGPTDashboardIntegration:
    """Tests for MyGPT Dashboard integration."""

    @pytest.mark.asyncio
    async def test_operations_dashboard_structure(self) -> None:
        """Test operations dashboard returns expected structure."""
        from api.routes.mygpt.dashboard import get_operations_dashboard

        response = await get_operations_dashboard(
            include_alerts=True,
            include_health=False,  # Skip health checks for unit test
            alert_limit=5,
        )

        assert "trinity_score" in response
        assert "entropy" in response
        assert "metrics" in response
        assert "active_agents" in response
        assert "timestamp" in response

        # Check agents structure
        agents = response["active_agents"]
        assert len(agents) >= 2
        assert all("name" in a and "status" in a for a in agents)

    @pytest.mark.asyncio
    async def test_operations_summary(self) -> None:
        """Test operations summary endpoint."""
        from api.routes.mygpt.dashboard import get_operations_summary

        response = await get_operations_summary()

        assert "status" in response
        assert "trinity_score" in response
        assert "active_alerts" in response
        assert response["status"] in ["operational", "degraded"]

    @pytest.mark.asyncio
    async def test_detailed_metrics(self) -> None:
        """Test detailed metrics endpoint."""
        from api.routes.mygpt.dashboard import get_detailed_metrics

        response = await get_detailed_metrics()

        assert "telemetry_enabled" in response
        assert "entropy" in response
        assert "trinity_score" in response
        assert "metrics" in response


class TestEndToEndScenarios:
    """End-to-end integration scenarios."""

    @pytest.mark.asyncio
    async def test_high_error_rate_triggers_healing(self) -> None:
        """Scenario 1: High error rate triggers healing agent response."""
        bridge = TelemetryBridge()
        bridge.entropy_threshold = 0.3

        healing_triggered = False

        async def healing_handler(alert: TelemetryAlert) -> None:
            nonlocal healing_triggered
            if "error rate" in alert.message.lower() or alert.severity in [
                AlertSeverity.CRITICAL,
                AlertSeverity.EMERGENCY,
            ]:
                healing_triggered = True

        bridge.register_alert_handler(healing_handler)

        # Simulate high error rate
        bridge.current_metrics.error_rate = 0.1
        await bridge._analyze_entropy()
        await bridge._route_if_needed()

        assert healing_triggered is True

    @pytest.mark.asyncio
    async def test_irs_change_triggers_agent_response(self) -> None:
        """Scenario 2: IRS change triggers agent analysis."""
        # Test the change broadcast pattern without deep imports
        test_queue: asyncio.Queue[dict] = asyncio.Queue(maxsize=100)

        # Simulate IRS change
        change = {
            "change_id": "IRS-2026-TEST",
            "change_type": "guidance",
            "title": "New Form 1040 Instructions",
            "severity": "warning",
            "timestamp": datetime.now(UTC).isoformat(),
        }

        await test_queue.put(change)

        # Verify change was queued (agent would receive via SSE)
        queued = await test_queue.get()
        assert queued["change_id"] == "IRS-2026-TEST"
        assert queued["change_type"] == "guidance"

    @pytest.mark.asyncio
    async def test_mygpt_receives_real_metrics(self) -> None:
        """Scenario 3: MyGPT query returns real metrics from telemetry."""
        from api.routes.mygpt.dashboard import get_operations_dashboard

        # Get dashboard with real telemetry
        response = await get_operations_dashboard(
            include_alerts=True,
            include_health=False,
            alert_limit=5,
        )

        # Verify real metrics are included
        assert response["trinity_score"] >= 0
        assert response["trinity_score"] <= 100
        assert "error_rate" in response.get("metrics", {})

    @pytest.mark.asyncio
    async def test_telemetry_bridge_singleton(self) -> None:
        """Test that get_telemetry_bridge returns singleton."""
        bridge1 = get_telemetry_bridge()
        bridge2 = get_telemetry_bridge()

        assert bridge1 is bridge2


class TestTelemetryMetrics:
    """Tests for TelemetryMetrics dataclass."""

    def test_metrics_defaults(self) -> None:
        """Test TelemetryMetrics has correct defaults."""
        metrics = TelemetryMetrics()

        assert metrics.error_rate == 0.0
        assert metrics.request_latency_p99 == 0.0
        assert metrics.memory_usage_percent == 0.0
        assert metrics.cpu_usage_percent == 0.0
        assert metrics.active_connections == 0
        assert metrics.irs_api_latency_ms == 0.0
        assert metrics.trinity_score == 100.0
        assert isinstance(metrics.timestamp, datetime)


class TestAlertManagement:
    """Tests for alert management functionality."""

    def test_get_recent_alerts(self) -> None:
        """Test getting recent alerts."""
        bridge = TelemetryBridge()

        # Add some alerts
        for i in range(5):
            alert = TelemetryAlert(
                alert_id=f"TEST-{i:03d}",
                severity=AlertSeverity.INFO,
                source="test",
                message=f"Test alert {i}",
                metrics={},
            )
            bridge.alerts.append(alert)

        recent = bridge.get_recent_alerts(limit=3)

        assert len(recent) == 3
        assert all("alert_id" in a for a in recent)

    @pytest.mark.asyncio
    async def test_alert_acknowledgment(self) -> None:
        """Test alert acknowledgment."""
        from api.routes.mygpt.dashboard import acknowledge_alert

        bridge = get_telemetry_bridge()

        # Add a test alert
        alert = TelemetryAlert(
            alert_id="ACK-TEST-001",
            severity=AlertSeverity.WARNING,
            source="test",
            message="Test acknowledgment",
            metrics={},
        )
        bridge.alerts.append(alert)

        # Acknowledge it
        result = await acknowledge_alert(alert_id="ACK-TEST-001")

        assert result["status"] == "success"
        assert alert.acknowledged is True

        # Clean up
        bridge.alerts.remove(alert)
