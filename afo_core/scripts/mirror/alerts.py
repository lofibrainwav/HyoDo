# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Alerts - Alert management for Chancellor Mirror

Handles:
- Alert creation and deduplication
- Alert lifecycle management
- Multi-channel notification dispatch
"""

import datetime
import logging
from typing import TYPE_CHECKING

from scripts.mirror.models import TrinityScoreAlert
from scripts.mirror.notifiers import DiscordNotifier, LocalLogNotifier, SlackNotifier

if TYPE_CHECKING:
    from scripts.mirror.recovery import RecoveryEngine

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages Trinity Score alerts and notifications"""

    def __init__(self, publish_thought_callback=None) -> None:
        self.active_alerts: list[TrinityScoreAlert] = []
        self.discord = DiscordNotifier()
        self.slack = SlackNotifier()
        self.local_log = LocalLogNotifier()
        self._publish_thought = publish_thought_callback
        self._recovery_engine: RecoveryEngine | None = None

    def set_recovery_engine(self, engine: "RecoveryEngine") -> None:
        """Set recovery engine for emergency responses"""
        self._recovery_engine = engine

    async def raise_alert(self, pillar: str, score: float, threshold: float, message: str) -> None:
        """
        Raise a new alert

        Args:
            pillar: Problem pillar name
            score: Current score
            threshold: Threshold value
            message: Alert message
        """
        alert = TrinityScoreAlert(
            pillar=pillar,
            score=score,
            threshold=threshold,
            timestamp=datetime.datetime.now().isoformat(),
            message=message,
        )

        if self._publish_thought:
            level = "warning" if "⚠️" in message else "critical"
            await self._publish_thought(message, level=level)

        # Prevent duplicate alerts
        if not self._is_duplicate_alert(alert):
            self.active_alerts.append(alert)
            logger.warning(f"🚨 TRINITY ALERT: {message}")

            # Send notification
            await self.send_alert_notification(alert)

            # Emergency response for severe cases
            if pillar == "total" and score < 85.0:
                await self.emergency_response(alert)

    def _is_duplicate_alert(self, new_alert: TrinityScoreAlert) -> bool:
        """
        Check for duplicate alerts

        Args:
            new_alert: New alert to check

        Returns:
            True if duplicate within 5 minutes
        """
        cutoff_time = datetime.datetime.now() - datetime.timedelta(minutes=5)

        for alert in self.active_alerts:
            if alert.pillar == new_alert.pillar and alert.timestamp > cutoff_time.isoformat():
                return True

        return False

    async def send_alert_notification(self, alert: TrinityScoreAlert) -> None:
        """Send alert via configured notification channels"""
        logger.warning(f"📢 알람 전송: {alert.message}")
        await self.discord.send(alert)

    async def emergency_response(self, alert: TrinityScoreAlert) -> None:
        """Handle emergency situations"""
        logger.critical(f"🚨 EMERGENCY RESPONSE ACTIVATED | {alert.message}")

        if self._recovery_engine:
            await self._recovery_engine.collect_system_diagnostics()
            await self._recovery_engine.attempt_auto_recovery()

        await self.notify_administrators(alert)

    async def notify_administrators(self, alert: TrinityScoreAlert) -> None:
        """Notify administrators through all channels"""
        logger.critical("📢 관리자 긴급 통보 발송")
        notification_results: list[dict[str, str | bool]] = []

        # Discord (critical level)
        if await self.discord.send(alert, is_critical=True):
            notification_results.append({"channel": "discord", "success": True})
        else:
            notification_results.append({"channel": "discord", "success": False})

        # Slack (backup channel)
        if await self.slack.send(alert, is_critical=True):
            notification_results.append({"channel": "slack", "success": True})
        else:
            notification_results.append({"channel": "slack", "success": False})

        # Local log (always)
        if await self.local_log.send(alert, is_critical=True):
            notification_results.append({"channel": "local_log", "success": True})
        else:
            notification_results.append({"channel": "local_log", "success": False})

        # Publish to Matrix Stream
        if self._publish_thought:
            await self._publish_thought(
                f"CRITICAL ALERT: {alert.message} (Admin notified via {len(notification_results)} channels)",
                level="critical",
            )

        successful = sum(1 for r in notification_results if r.get("success"))
        logger.critical(f"📢 관리자 통보 완료: {successful}/{len(notification_results)} 채널 성공")

    def get_active_alerts(self) -> list[TrinityScoreAlert]:
        """Get list of active alerts"""
        return self.active_alerts.copy()

    def clear_resolved_alerts(self) -> None:
        """Clear alerts older than 1 hour"""
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=1)

        self.active_alerts = [
            alert for alert in self.active_alerts if alert.timestamp > cutoff_time.isoformat()
        ]

        logger.info(f"🧹 해결된 알람 정리 완료, 남은 알람: {len(self.active_alerts)}개")
