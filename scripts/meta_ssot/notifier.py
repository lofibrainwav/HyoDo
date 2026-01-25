"""
Meta-SSOT Notifier - Discord webhook notifications

Handles alert notifications via Discord webhook.
"""

import json
import os
from datetime import datetime
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen


def send_discord_alert(results: dict, webhook_url: Optional[str] = None) -> bool:
    """Discord 웹훅으로 건강 상태 알림 전송"""
    webhook_url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return False

    overall = results.get("overall_status", "UNKNOWN")
    meta = results.get("meta", {})
    metacog = results.get("metacognitive", {})

    # 색상 결정
    color_map = {
        "HEALTHY": 0x00FF00,  # Green
        "WARNING": 0xFFFF00,  # Yellow
        "STALE": 0xFFA500,  # Orange
        "ERROR": 0xFF0000,  # Red
        "INCOMPLETE": 0xFF6600,  # Dark Orange
    }
    color = color_map.get(overall, 0x808080)

    # 시스템 상태 요약
    system_summary = []
    for sys_info in results.get("systems", []):
        icon = (
            "✅"
            if sys_info["status"] == "HEALTHY"
            else "⏭️"
            if sys_info["status"] == "SKIP"
            else "❌"
        )
        system_summary.append(f"{icon} {sys_info['name']}")

    # launchd 상태
    launchd = metacog.get("launchd_runtime", {})
    launchd_status = f"{launchd.get('loaded', 0)}/{launchd.get('total', 0)} loaded"

    # Cross-validation 상태
    xval = metacog.get("cross_validation", {})
    xval_status = f"{xval.get('passed', 0)}/{xval.get('total_checks', 0)} passed"

    message = {
        "embeds": [
            {
                "title": f"🏰 Meta-SSOT Health: {overall}",
                "color": color,
                "fields": [
                    {"name": "Healthy", "value": str(meta.get("healthy", 0)), "inline": True},
                    {"name": "Warning", "value": str(meta.get("warning", 0)), "inline": True},
                    {"name": "Error", "value": str(meta.get("error", 0)), "inline": True},
                    {"name": "launchd", "value": launchd_status, "inline": True},
                    {"name": "Cross-Validation", "value": xval_status, "inline": True},
                ],
                "description": "```\n" + "\n".join(system_summary[:6]) + "\n```",
                "timestamp": results.get("timestamp", datetime.now().isoformat()),
                "footer": {"text": "Meta-SSOT Health v2.0"},
            }
        ]
    }

    try:
        req = Request(
            webhook_url,
            data=json.dumps(message).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        urlopen(req, timeout=10)
        return True
    except URLError as e:
        print(f"⚠️  Discord alert failed: {e}")
        return False


def should_alert(results: dict) -> bool:
    """알림이 필요한 상태인지 판단"""
    overall = results.get("overall_status", "HEALTHY")
    metacog = results.get("metacognitive", {})
    xval = metacog.get("cross_validation", {})

    # 알림 조건:
    # 1. overall_status가 HEALTHY가 아닌 경우
    # 2. cross_validation이 실패한 경우
    # 3. launchd 서비스가 로드되지 않은 경우
    if overall != "HEALTHY":
        return True
    if not xval.get("all_valid", True):
        return True

    launchd = metacog.get("launchd_runtime", {})
    if launchd.get("loaded", 0) < launchd.get("total", 0):
        return True

    return False
