"""
Discord Webhook Module
공통 Discord 웹훅 알림 유틸리티

Usage:
    from scripts.common import send_discord_alert, send_simple_alert

    # Simple alert
    send_simple_alert("Build completed!", level="success")

    # Rich embed alert
    send_discord_alert(
        title="CI Status",
        description="All tests passed",
        color=0x00FF00,
        fields=[{"name": "Tests", "value": "1551 passed"}]
    )
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Color presets
COLORS = {
    "success": 0x00FF00,  # Green
    "warning": 0xFFFF00,  # Yellow
    "error": 0xFF0000,  # Red
    "info": 0x0099FF,  # Blue
    "critical": 0x990000,  # Dark Red
}


def get_webhook_url() -> str | None:
    """환경변수에서 Discord webhook URL 가져오기"""
    return os.environ.get("DISCORD_WEBHOOK_URL")


def send_simple_alert(
    message: str,
    level: str = "info",
    webhook_url: str | None = None,
) -> bool:
    """간단한 Discord 알림 전송

    Args:
        message: 알림 메시지
        level: 알림 레벨 (success, warning, error, info, critical)
        webhook_url: Discord webhook URL (없으면 환경변수 사용)

    Returns:
        bool: 전송 성공 여부
    """
    webhook_url = webhook_url or get_webhook_url()
    if not webhook_url:
        logger.warning("Discord webhook URL not configured")
        return False

    icon_map = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "critical": "🚨",
    }
    icon = icon_map.get(level, "📢")

    payload = {"content": f"{icon} {message}"}

    return _send_webhook(webhook_url, payload)


def send_discord_alert(
    title: str,
    description: str | None = None,
    color: int | str = "info",
    fields: list[dict[str, Any]] | None = None,
    footer: str | None = None,
    webhook_url: str | None = None,
) -> bool:
    """Rich embed Discord 알림 전송

    Args:
        title: 알림 제목
        description: 알림 설명
        color: 색상 (hex int 또는 preset 이름)
        fields: 추가 필드 리스트 [{"name": "...", "value": "...", "inline": bool}]
        footer: 푸터 텍스트
        webhook_url: Discord webhook URL (없으면 환경변수 사용)

    Returns:
        bool: 전송 성공 여부
    """
    webhook_url = webhook_url or get_webhook_url()
    if not webhook_url:
        logger.warning("Discord webhook URL not configured")
        return False

    # Color resolution
    if isinstance(color, str):
        color = COLORS.get(color, COLORS["info"])

    embed: dict[str, Any] = {
        "title": title,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if description:
        embed["description"] = description

    if fields:
        embed["fields"] = fields

    if footer:
        embed["footer"] = {"text": footer}

    payload = {"embeds": [embed]}

    return _send_webhook(webhook_url, payload)


def _send_webhook(webhook_url: str, payload: dict[str, Any]) -> bool:
    """Discord webhook 전송 (내부 함수)"""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = Request(
            webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=10) as resp:
            return resp.status == 204
    except URLError as e:
        logger.error(f"Discord webhook failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Discord webhook: {e}")
        return False
