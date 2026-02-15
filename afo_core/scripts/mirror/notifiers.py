# Trinity Score: 90.0 (Established by Chancellor)
"""
Mirror Notifiers - Multi-channel notification system

Supports:
- Discord webhooks
- Slack webhooks
- Email (SMTP with TLS)
- Local file logging
"""

import asyncio
import logging
import os
import smtplib
from abc import ABC, abstractmethod
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import aiohttp

from scripts.mirror.models import TrinityScoreAlert

logger = logging.getLogger(__name__)

# Try to import aiosmtplib for async email support
try:
    import aiosmtplib

    AIOSMTPLIB_AVAILABLE = True
except ImportError:
    AIOSMTPLIB_AVAILABLE = False
    logger.debug("aiosmtplib not installed. Email will use sync smtplib in executor.")


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


class EmailNotifier(NotifierBase):
    """Email SMTP notifier with TLS/SSL support"""

    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        from_addr: str | None = None,
        to_addrs: str | list[str] | None = None,
        use_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host or os.environ.get("IRS_EMAIL_SMTP_HOST", "")
        self.smtp_port = smtp_port or int(os.environ.get("IRS_EMAIL_SMTP_PORT", "587"))
        self.smtp_user = smtp_user or os.environ.get("IRS_EMAIL_SMTP_USER", "")
        self.smtp_password = smtp_password or os.environ.get("IRS_EMAIL_SMTP_PASSWORD", "")
        self.from_addr = from_addr or os.environ.get("IRS_EMAIL_FROM", "")

        # Handle single email or comma-separated list
        to_env = os.environ.get("IRS_EMAIL_TO", "")
        if to_addrs:
            if isinstance(to_addrs, str):
                self.to_addrs = [addr.strip() for addr in to_addrs.split(",")]
            else:
                self.to_addrs = to_addrs
        elif to_env:
            self.to_addrs = [addr.strip() for addr in to_env.split(",")]
        else:
            self.to_addrs = []

        self.use_tls = use_tls
        self.sender_name = "AFO Kingdom Guardian"

    def _format_email_content(self, alert: TrinityScoreAlert, is_critical: bool) -> dict[str, Any]:
        """Format email content with HTML and text versions"""
        severity = "CRITICAL" if is_critical else "WARNING"
        color = "#B71C1C" if is_critical else ("#FF0000" if alert.score < 85.0 else "#FFA500")

        subject = f"{'🚨' if is_critical else '⚠️'} [{severity}] AFO Kingdom Trinity Alert - {alert.pillar.upper()}"

        # Text version
        text_body = f"""
AFO Kingdom Guardian Alert
{"=" * 50}

Severity: {severity}
Pillar: {alert.pillar.upper()}
Current Score: {alert.score:.1f}
Threshold: {alert.threshold:.1f}

Message:
{alert.message}

Timestamp: {alert.timestamp}

{"=" * 50}
This is an automated alert from AFO Kingdom Guardian.
"""

        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ border-left: 5px solid {color}; padding-left: 20px; margin-bottom: 20px; }}
        .severity {{ color: {color}; font-size: 24px; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .metric-label {{ font-size: 12px; color: #666; }}
        .metric-value {{ font-size: 18px; font-weight: bold; }}
        .message {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 11px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="severity">{severity}</div>
            <h1>AFO Kingdom Guardian Alert</h1>
        </div>

        <div>
            <div class="metric">
                <div class="metric-label">Pillar</div>
                <div class="metric-value">{alert.pillar.upper()}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Current Score</div>
                <div class="metric-value">{alert.score:.1f}</div>
            </div>
            <div class="metric">
                <div class="metric-label">Threshold</div>
                <div class="metric-value">{alert.threshold:.1f}</div>
            </div>
        </div>

        <div class="message">
            <strong>Message:</strong><br>
            {alert.message}
        </div>

        <div class="footer">
            Timestamp: {alert.timestamp}<br>
            This is an automated alert from AFO Kingdom Guardian.<br>
            <em>眞善美孝永 — 왕국의 영원한 빛</em>
        </div>
    </div>
</body>
</html>
"""

        return {"subject": subject, "text": text_body, "html": html_body}

    async def send(self, alert: TrinityScoreAlert, is_critical: bool = False) -> bool:
        """Send email notification via SMTP with TLS"""
        # Validate configuration
        if not all(
            [self.smtp_host, self.smtp_user, self.smtp_password, self.from_addr, self.to_addrs]
        ):
            logger.debug(
                "Email not configured (missing SMTP settings), skipping email notification"
            )
            return False

        content = self._format_email_content(alert, is_critical)

        # Build message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = content["subject"]
        msg["From"] = f"{self.sender_name} <{self.from_addr}>"
        msg["To"] = ", ".join(self.to_addrs)

        # Attach text and HTML parts
        msg.attach(MIMEText(content["text"], "plain", "utf-8"))
        msg.attach(MIMEText(content["html"], "html", "utf-8"))

        try:
            if AIOSMTPLIB_AVAILABLE:
                # Use async aiosmtplib
                await self._send_async(msg)
            else:
                # Fallback to sync smtplib in executor
                await asyncio.get_event_loop().run_in_executor(None, self._send_sync, msg)

            logger.info(f"✅ Email 알림 전송 성공: {', '.join(self.to_addrs)}")
            return True

        except TimeoutError:
            logger.error("❌ Email 알림 전송 타임아웨")
            return False
        except Exception as e:
            logger.error(f"❌ Email 알림 전송 실패: {e}")
            return False

    async def _send_async(self, msg: MIMEMultipart) -> None:
        """Send email using aiosmtplib (async)"""
        await aiosmtplib.send(
            msg,
            hostname=self.smtp_host,
            port=self.smtp_port,
            username=self.smtp_user,
            password=self.smtp_password,
            start_tls=self.use_tls,
            timeout=10,
        )

    def _send_sync(self, msg: MIMEMultipart) -> None:
        """Send email using smtplib (sync, for fallback)"""
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.from_addr, self.to_addrs, msg.as_string())


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
