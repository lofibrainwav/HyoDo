# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Notifiers - Multi-channel notification system

Supports:
- Discord webhooks
- Slack webhooks
- Local file logging
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import aiohttp
from scripts.mirror.models import TrinityScoreAlert

logger = logging.getLogger(__name__)


class NotifierBase(ABC):
    """Base class for notification channels"""

    @abstractmethod
    async def send(self, alert: TrinityScoreAlert, is_critical: bool = False) -> bool:
        """Send notification. Returns True if successful."""
        pass


class DiscordNotifier(NotifierBase):
    """Discord webhook notifier"""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")

    async def send(self, alert: TrinityScoreAlert, is_critical: bool = False) -> bool:
        if not self.webhook_url:
            logger.debug("DISCORD_WEBHOOK_URL not configured, skipping Discord notification")
            return False

        # Color based on severity
        if is_critical:
            color = 0xB71C1C  # Dark red (critical)
            title = "🚨 CRITICAL: AFO Kingdom Emergency Alert"
            content = "@here Emergency alert from Chancellor Mirror!"
        else:
            color = 0xFF0000 if alert.score < 85.0 else 0xFFA500  # Red / Orange
            title = f"🏰 AFO Kingdom Trinity Alert - {alert.pillar.upper()}"
            content = None

        embed = {
            "title": title,
            "description": alert.message
            if not is_critical
            else f"**{alert.message}**\n\nImmediate administrator attention required!",
            "color": color,
            "fields": [
                {"name": "Pillar", "value": alert.pillar.upper(), "inline": True},
                {"name": "Score", "value": f"{alert.score:.1f}", "inline": True},
                {"name": "Threshold", "value": f"{alert.threshold:.1f}", "inline": True},
            ],
            "timestamp": alert.timestamp,
            "footer": {"text": "Chancellor Mirror (승상의 거울)"},
        }

        if is_critical:
            embed["fields"].append(
                {
                    "name": "Severity",
                    "value": "CRITICAL - Immediate Action Required",
                    "inline": False,
                }
            )

        payload = {
            "username": "AFO Kingdom EMERGENCY" if is_critical else "AFO Kingdom Guardian",
            "embeds": [embed],
        }
        if content:
            payload["content"] = content

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 204:
                        logger.info("✅ Discord 알림 전송 성공")
                        return True
                    else:
                        logger.warning(f"⚠️ Discord 알림 전송 실패: HTTP {response.status}")
                        return False
        except TimeoutError:
            logger.error("❌ Discord 알림 전송 타임아웃")
            return False
        except Exception as e:
            logger.error(f"❌ Discord 알림 전송 실패: {e}")
            return False


class SlackNotifier(NotifierBase):
    """Slack webhook notifier"""

    def __init__(self, webhook_url: str | None = None) -> None:
        self.webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL")

    async def send(self, alert: TrinityScoreAlert, is_critical: bool = False) -> bool:
        if not self.webhook_url:
            logger.debug("SLACK_WEBHOOK_URL not configured, skipping Slack notification")
            return False

        color = "#B71C1C" if is_critical else ("#FF0000" if alert.score < 85.0 else "#FFA500")
        title = (
            f"🚨 CRITICAL: {alert.pillar.upper()} Alert"
            if is_critical
            else f"⚠️ {alert.pillar.upper()} Alert"
        )

        slack_payload = {
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": f"{alert.message}\n*Score:* {alert.score:.1f} / *Threshold:* {alert.threshold:.1f}",
                    "footer": "AFO Kingdom Chancellor Mirror",
                    "ts": datetime.now().timestamp(),
                }
            ]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=slack_payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        logger.info("✅ Slack 알림 전송 성공")
                        return True
                    else:
                        logger.warning(f"⚠️ Slack 알림 전송 실패: HTTP {response.status}")
                        return False
        except Exception as e:
            logger.error(f"❌ Slack 알림 전송 실패: {e}")
            return False


class LocalLogNotifier(NotifierBase):
    """Local file log notifier"""

    def __init__(self, log_dir: Path | None = None) -> None:
        self.log_dir = (
            log_dir or Path(__file__).parent.parent.parent.parent / "artifacts" / "alerts"
        )

    async def send(self, alert: TrinityScoreAlert, is_critical: bool = False) -> bool:
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            alert_log_file = self.log_dir / "critical_alerts.log"

            severity = "CRITICAL" if is_critical else "WARNING"
            log_entry = (
                f"[{alert.timestamp}] {severity} | "
                f"Pillar: {alert.pillar} | Score: {alert.score:.1f} | "
                f"Threshold: {alert.threshold:.1f} | {alert.message}\n"
            )

            with alert_log_file.open("a", encoding="utf-8") as f:
                f.write(log_entry)

            logger.info(f"✅ 로컬 알람 로그 기록 완료: {alert_log_file}")
            return True
        except Exception as e:
            logger.error(f"❌ 로컬 알람 로그 기록 실패: {e}")
            return False
