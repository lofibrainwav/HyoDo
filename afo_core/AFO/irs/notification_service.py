"""Notification Service Module.

Provides notification channels for IRS document changes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .change_detector import ChangeSummary

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Available notification channels."""

    LOG = "log"
    EMAIL = "email"
    SLACK = "slack"


@dataclass
class Notification:
    """Notification message."""

    title: str
    message: str
    severity: str
    document_id: str
    channel: NotificationChannel

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "document_id": self.document_id,
            "channel": self.channel.value,
        }


class NotificationService:
    """Service for sending notifications about IRS document changes."""

    def __init__(self, channels: list[NotificationChannel] | None = None) -> None:
        self.channels = channels or [NotificationChannel.LOG]
        self._notification_count = 0

    async def notify_change(self, change_summary: ChangeSummary) -> None:
        """Send notification for a change summary."""
        notification = self._create_notification(change_summary)

        for channel in self.channels:
            await self._send_to_channel(notification, channel)

        self._notification_count += 1

    def _create_notification(self, change_summary: ChangeSummary) -> Notification:
        """Create notification from change summary."""
        title = f"IRS Document Change: {change_summary.document_id}"
        severity = change_summary.impact.category

        change_details = []
        if change_summary.changes:
            for key, value in change_summary.changes.items():
                change_details.append(f"- {key}: {value}")

        message = f"""
Severity: {severity.upper()}
Document: {change_summary.document_id}
Impact Score: {change_summary.impact.score:.2f}

Details:
{chr(10).join(change_details) if change_details else 'No detailed changes available'}

Description: {change_summary.impact.description or 'N/A'}
Detected At: {change_summary.detected_at}
"""

        return Notification(
            title=title,
            message=message.strip(),
            severity=severity,
            document_id=change_summary.document_id,
            channel=NotificationChannel.LOG,
        )

    async def _send_to_channel(self, notification: Notification, channel: NotificationChannel) -> None:
        """Send notification to specific channel."""
        if channel == NotificationChannel.LOG:
            await self._send_to_log(notification)
        elif channel == NotificationChannel.EMAIL:
            await self._send_to_email(notification)
        elif channel == NotificationChannel.SLACK:
            await self._send_to_slack(notification)

    async def _send_to_log(self, notification: Notification) -> None:
        """Send notification via structured logging."""
        log_message = (
            f"[IRS CHANGE] {notification.title} | "
            f"Severity: {notification.severity} | "
            f"Document: {notification.document_id}"
        )

        if notification.severity == "critical":
            logger.error(log_message)
        elif notification.severity == "high":
            logger.warning(log_message)
        else:
            logger.info(log_message)

        logger.debug(f"Notification details:\n{notification.message}")

    async def _send_to_email(self, notification: Notification) -> None:
        """Send notification via email (placeholder)."""
        logger.info(f"[EMAIL PLACEHOLDER] Would send: {notification.title}")

    async def _send_to_slack(self, notification: Notification) -> None:
        """Send notification via Slack (placeholder)."""
        logger.info(f"[SLACK PLACEHOLDER] Would send: {notification.title}")

    def get_stats(self) -> dict[str, Any]:
        """Get notification statistics."""
        return {
            "notification_count": self._notification_count,
            "channels": [c.value for c in self.channels],
        }


__all__ = [
    "NotificationChannel",
    "Notification",
    "NotificationService",
]
