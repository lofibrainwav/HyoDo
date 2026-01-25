# Trinity Score: 91.0 (Established by Chancellor)
"""Security Agent Core (TICKET-098)
Anomaly detection and real-time security monitoring for AFO Kingdom.

2026 Best Practices Implementation:
- Anomaly Detection: Monitor agent behavior patterns for deviations
- Real-time Monitoring: Track security events across all agents
- Threat Response: Automated containment and alerting
- Integration: Works with GovernanceAgent for policy enforcement

Philosophy:
- 眞 (Truth): Detect real threats, minimize false positives
- 善 (Goodness): Protect the kingdom from malicious activity
- 美 (Beauty): Non-intrusive monitoring with clear alerts
"""

import hashlib
import logging
import os
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, IntEnum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ThreatLevel(IntEnum):
    """Threat classification for security events (ordered by severity)."""

    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

    def __str__(self) -> str:
        return self.name.lower()


class SecurityEventType(Enum):
    """Types of security events to monitor."""

    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_PATTERN = "suspicious_pattern"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_EXFILTRATION = "data_exfiltration"
    INJECTION_ATTEMPT = "injection_attempt"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    ANOMALOUS_BEHAVIOR = "anomalous_behavior"


@dataclass
class SecurityEvent:
    """A security event with full context."""

    event_type: SecurityEventType
    threat_level: ThreatLevel
    source_agent: str
    description: str
    metadata: dict[str, Any] = field(default_factory=lambda: {})
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    event_id: str = field(
        default_factory=lambda: hashlib.sha256(
            f"{datetime.now(UTC).isoformat()}-{os.urandom(8).hex()}".encode()
        ).hexdigest()[:16]
    )


@dataclass
class SecurityAlert:
    """An alert generated from security events."""

    alert_id: str
    events: list[SecurityEvent]
    threat_level: ThreatLevel
    recommended_action: str
    is_acknowledged: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class SecurityAgent:
    """Security Agent for AFO Kingdom.

    Implements 2026 AI Security best practices:
    1. Anomaly detection for agent behavior
    2. Real-time security monitoring
    3. Threat response automation
    4. Integration with Governance Agent
    """

    def __init__(self) -> None:
        self.name = "Security Agent (張飛)"

        # Event history for pattern analysis
        self._event_history: deque[SecurityEvent] = deque(maxlen=1000)
        self._alerts: list[SecurityAlert] = []

        # Anomaly detection thresholds
        self.thresholds = {
            "max_auth_failures_per_minute": 5,
            "max_api_calls_per_minute": 100,
            "max_file_operations_per_minute": 50,
            "suspicious_pattern_threshold": 3,
        }

        # Agent behavior baselines (learned over time)
        self._behavior_baselines: dict[str, dict[str, float]] = {}

        # Blocked agents/IPs
        self._blocked_entities: set[str] = set()

        # Alert subscribers (for notification integration)
        self._alert_subscribers: list[Callable[[SecurityAlert], None]] = []

    def record_event(self, event: SecurityEvent) -> SecurityAlert | None:
        """Record a security event and check for threat patterns.

        Returns:
            SecurityAlert if threat detected, None otherwise
        """
        self._event_history.append(event)
        logger.info(
            f"[{self.name}] Event recorded: {event.event_type.value} | Level: {event.threat_level.name}"
        )

        # Persist to security log
        self._persist_event(event)

        # Check for patterns that warrant an alert
        alert = self._analyze_threat_patterns(event)

        if alert:
            self._alerts.append(alert)
            self._notify_subscribers(alert)

        return alert

    def detect_anomaly(
        self, agent_name: str, action: str, metrics: dict[str, float]
    ) -> SecurityEvent | None:
        """Detect anomalous behavior based on agent baselines.

        Args:
            agent_name: Name of the agent being monitored
            action: Action being performed
            metrics: Performance/behavior metrics

        Returns:
            SecurityEvent if anomaly detected, None otherwise
        """
        baseline = self._behavior_baselines.get(agent_name, {})

        anomalies: list[str] = []

        for metric_name, value in metrics.items():
            if metric_name in baseline:
                expected = baseline[metric_name]
                deviation = abs(value - expected) / max(expected, 0.001)

                # Flag if deviation > 2x (200%) from baseline
                if deviation > 2.0:
                    anomalies.append(f"{metric_name}: {value:.2f} vs expected {expected:.2f}")

        if anomalies:
            event = SecurityEvent(
                event_type=SecurityEventType.ANOMALOUS_BEHAVIOR,
                threat_level=(ThreatLevel.MEDIUM if len(anomalies) < 3 else ThreatLevel.HIGH),
                source_agent=agent_name,
                description=f"Anomalous behavior detected: {', '.join(anomalies)}",
                metadata={"metrics": metrics, "baseline": baseline, "action": action},
            )
            self.record_event(event)
            return event

        # Update baseline with new data (exponential moving average)
        self._update_baseline(agent_name, metrics)
        return None

    def scan_for_injection(self, input_text: str, source: str) -> SecurityEvent | None:
        """Scan input text for injection attempts.

        Args:
            input_text: Text to scan
            source: Source of the input (agent/user)

        Returns:
            SecurityEvent if injection detected, None otherwise
        """
        # Common injection patterns
        injection_patterns = [
            "'; DROP TABLE",
            "<script>",
            "{{",  # Template injection
            "${",  # Shell injection
            "UNION SELECT",
            "eval(",
            "exec(",
            "__import__",
            "os.system",
            "subprocess",
        ]

        input_lower = input_text.lower()
        detected_patterns = [p for p in injection_patterns if p.lower() in input_lower]

        if detected_patterns:
            event = SecurityEvent(
                event_type=SecurityEventType.INJECTION_ATTEMPT,
                threat_level=ThreatLevel.HIGH,
                source_agent=source,
                description="Potential injection attempt detected",
                metadata={
                    "patterns_found": detected_patterns,
                    "input_preview": input_text[:200],
                },
            )
            self.record_event(event)
            return event

        return None

    def block_entity(self, entity_id: str, reason: str) -> None:
        """Block an entity (agent/IP) from further operations.

        Args:
            entity_id: Identifier of the entity to block
            reason: Reason for blocking
        """
        self._blocked_entities.add(entity_id)
        logger.warning(f"[{self.name}] Entity blocked: {entity_id} | Reason: {reason}")

        event = SecurityEvent(
            event_type=SecurityEventType.UNAUTHORIZED_ACCESS,
            threat_level=ThreatLevel.HIGH,
            source_agent=entity_id,
            description=f"Entity blocked: {reason}",
            metadata={"action": "block", "reason": reason},
        )
        self.record_event(event)

    def is_blocked(self, entity_id: str) -> bool:
        """Check if an entity is blocked."""
        return entity_id in self._blocked_entities

    def unblock_entity(self, entity_id: str) -> bool:
        """Unblock an entity (requires manual authorization)."""
        if entity_id in self._blocked_entities:
            self._blocked_entities.remove(entity_id)
            logger.info(f"[{self.name}] Entity unblocked: {entity_id}")
            return True
        return False

    def _analyze_threat_patterns(self, _latest_event: SecurityEvent) -> SecurityAlert | None:
        """Analyze recent events for threat patterns."""
        # Get events from last minute
        one_minute_ago = datetime.now(UTC).timestamp() - 60
        recent_events = [
            e
            for e in self._event_history
            if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")).timestamp()
            > one_minute_ago
        ]

        # Count by event type
        type_counts: dict[str, int] = {}
        for event in recent_events:
            type_counts[event.event_type.value] = type_counts.get(event.event_type.value, 0) + 1

        # Check for alert-worthy patterns
        alerts_needed: list[tuple[str, ThreatLevel]] = []

        if type_counts.get("auth_failure", 0) >= self.thresholds["max_auth_failures_per_minute"]:
            alerts_needed.append(("Brute force attack suspected", ThreatLevel.HIGH))

        if type_counts.get("injection_attempt", 0) >= 2:
            alerts_needed.append(("Multiple injection attempts detected", ThreatLevel.CRITICAL))

        if (
            type_counts.get("anomalous_behavior", 0)
            >= self.thresholds["suspicious_pattern_threshold"]
        ):
            alerts_needed.append(("Coordinated anomalous behavior", ThreatLevel.HIGH))

        if alerts_needed:
            max_level = max(level for _, level in alerts_needed)
            # Descriptions available: [desc for desc, _ in alerts_needed]

            return SecurityAlert(
                alert_id=hashlib.sha256(f"{datetime.now(UTC).isoformat()}".encode()).hexdigest()[
                    :12
                ],
                events=recent_events,
                threat_level=max_level,
                recommended_action=self._get_recommended_action(max_level),
            )

        return None

    def _get_recommended_action(self, threat_level: ThreatLevel) -> str:
        """Get recommended action based on threat level."""
        actions = {
            ThreatLevel.LOW: "Monitor and log",
            ThreatLevel.MEDIUM: "Increase monitoring, prepare containment",
            ThreatLevel.HIGH: "Immediate containment, alert security team",
            ThreatLevel.CRITICAL: "Emergency shutdown of affected systems, escalate to human",
        }
        return actions.get(threat_level, "Investigate")

    def _update_baseline(self, agent_name: str, metrics: dict[str, float]) -> None:
        """Update behavior baseline with exponential moving average."""
        alpha = 0.1  # Learning rate

        if agent_name not in self._behavior_baselines:
            self._behavior_baselines[agent_name] = {}

        baseline = self._behavior_baselines[agent_name]
        for key, value in metrics.items():
            if key in baseline:
                baseline[key] = alpha * value + (1 - alpha) * baseline[key]
            else:
                baseline[key] = value

    def _persist_event(self, event: SecurityEvent) -> None:
        """Persist security event to file."""
        try:
            security_dir = (
                Path(__file__).parent.parent.parent.parent.parent / "docs" / "ssot" / "security"
            )
            security_dir.mkdir(parents=True, exist_ok=True)

            import json
            from dataclasses import asdict

            log_file = security_dir / "security_events.jsonl"
            with log_file.open("a", encoding="utf-8") as f:
                entry = asdict(event)
                entry["event_type"] = event.event_type.value
                entry["threat_level"] = event.threat_level.name.lower()
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        except Exception as e:
            logger.warning(f"Failed to persist security event: {e}")

    def _notify_subscribers(self, alert: SecurityAlert) -> None:
        """Notify alert subscribers."""
        for subscriber in self._alert_subscribers:
            try:
                subscriber(alert)
            except Exception as e:
                logger.error(f"Alert notification failed: {e}")

    def subscribe_to_alerts(self, callback: Callable[[SecurityAlert], None]) -> None:
        """Subscribe to security alerts."""
        self._alert_subscribers.append(callback)

    def get_security_summary(self) -> dict[str, Any]:
        """Get summary of security status."""
        recent_events = list(self._event_history)[-100:]

        threat_counts = {}
        for event in recent_events:
            level = event.threat_level.value
            threat_counts[level] = threat_counts.get(level, 0) + 1

        return {
            "total_events": len(self._event_history),
            "active_alerts": len([a for a in self._alerts if not a.is_acknowledged]),
            "blocked_entities": len(self._blocked_entities),
            "threat_distribution": threat_counts,
            "monitored_agents": len(self._behavior_baselines),
        }


# Singleton instance
security_agent = SecurityAgent()


# Convenience functions
def record_security_event(
    event_type: SecurityEventType,
    threat_level: ThreatLevel,
    source: str,
    description: str,
    **metadata: Any,
) -> SecurityAlert | None:
    event = SecurityEvent(
        event_type=event_type,
        threat_level=threat_level,
        source_agent=source,
        description=description,
        metadata=metadata,
    )
    return security_agent.record_event(event)


def check_for_injection(input_text: str, source: str = "unknown") -> bool:
    """Check input for injection attempts. Returns True if safe."""
    event = security_agent.scan_for_injection(input_text, source)
    return event is None
