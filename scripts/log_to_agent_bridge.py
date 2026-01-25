#!/usr/bin/env python3
"""
Log to Agent Bridge System (Phase 48)
터미널 로그를 모니터링하여 LLM Agent에게 자동으로 보고

기능:
1. 로그 파일 감시 (tail -f 방식)
2. 패턴 매칭 (에러, 경고, 중요 이벤트)
3. Discord/Webhook으로 보고
4. Context7에 이력 저장
"""

import argparse
import asyncio
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

# Configuration
LOG_FILES = [
    Path("artifacts/run/unified_ticket_sync.err"),
    Path("artifacts/run/ssot_document_drift.err"),
    Path("artifacts/run/uvicorn_8010.log"),
    Path("logs/system_monitor_*.log"),
    Path("logs/trinity_evidence.log"),
]

PATTERNS = {
    "error": re.compile(r"error|exception|fail|crash", re.IGNORECASE),
    "warning": re.compile(r"warning|warn|degraded", re.IGNORECASE),
    "drift": re.compile(r"drift|drifted", re.IGNORECASE),
    "critical": re.compile(r"critical|emergency|fatal", re.IGNORECASE),
}

HISTORY_FILE = Path("artifacts/log_agent_history.json")


@dataclass
class LogEvent:
    """로그 이벤트"""

    timestamp: str
    log_file: str
    level: str  # "error", "warning", "drift", "critical"
    message: str
    line_number: int


@dataclass
class AlertConfig:
    """알림 설정"""

    webhook_url: Optional[str] = None
    min_level: str = "warning"  # "error", "warning", "drift", "critical"
    cooldown_seconds: int = 300  # 5분 동안 동일 이벤트 무시


class LogMonitor:
    """로그 모니터"""

    def __init__(self, config: AlertConfig) -> None:
        self.config = config
        self.log_files: List[Path] = []
        self.last_positions: Dict[str, int] = {}
        self.event_history: Dict[str, float] = {}

    def resolve_log_files(self) -> None:
        """실제 로그 파일 경로 해결 (와일드카드 확장)"""
        resolved = []

        for pattern in LOG_FILES:
            if "*" in str(pattern):
                # 와일드카드 패턴 확장
                parent = pattern.parent
                glob_pattern = pattern.name
                for file in sorted(parent.glob(glob_pattern), reverse=True):
                    if file.is_file():
                        resolved.append(file)
                        break
            elif pattern.exists() and pattern.is_file():
                resolved.append(pattern)

        self.log_files = resolved

    def detect_events(self) -> List[LogEvent]:
        """새로운 이벤트 감지"""
        events = []

        for log_file in self.log_files:
            if not log_file.exists():
                continue

            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    # 마지막 위치로 이동
                    last_pos = self.last_positions.get(str(log_file), 0)
                    f.seek(last_pos)

                    # 새로운 라인 읽기
                    new_lines = f.readlines()

                    # 위치 업데이트
                    self.last_positions[str(log_file)] = f.tell()

                    # 패턴 매칭
                    for i, line in enumerate(new_lines, start=1):
                        line_number = last_pos + i

                        for level, pattern in PATTERNS.items():
                            if pattern.search(line):
                                # 쿨다운 체크
                                event_key = f"{log_file}:{level}:{line.strip()[:50]}"
                                now = time.time()

                                if (
                                    event_key not in self.event_history
                                    or now - self.event_history[event_key]
                                    > self.config.cooldown_seconds
                                ):
                                    events.append(
                                        LogEvent(
                                            timestamp=datetime.now(UTC).isoformat(),
                                            log_file=str(log_file),
                                            level=level,
                                            message=line.strip(),
                                            line_number=line_number,
                                        )
                                    )

                                    self.event_history[event_key] = now

            except Exception as e:
                logger.error(f"Failed to read {log_file}: {e}")

        # 레벨 필터링
        level_priority = {"error": 3, "warning": 2, "drift": 1, "critical": 4}
        min_priority = level_priority.get(self.config.min_level, 0)

        events = [e for e in events if level_priority.get(e.level, 0) >= min_priority]

        return events

    def save_history(self, events: List[LogEvent]) -> None:
        """이력 저장"""
        history = []

        if HISTORY_FILE.exists():
            try:
                history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except Exception:
                history = []

        # 최근 100개만 유지
        history.extend([e.__dict__ for e in events])
        history = history[-100:]

        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to save history: {e}")


class AlertSender:
    """알림 전송기"""

    @staticmethod
    def send_discord_alert(events: List[LogEvent], webhook_url: str) -> bool:
        """Discord로 알림 전송"""
        if not events or not webhook_url:
            return False

        # 이벤트 그룹화
        by_level = {}
        for event in events:
            if event.level not in by_level:
                by_level[event.level] = []
            by_level[event.level].append(event)

        color = {
            "error": 16711680,  # Red
            "warning": 16776960,  # Yellow
            "drift": 16711782,  # Orange
            "critical": 16729344,  # Dark Red
        }

        # Embed 생성
        embed = {
            "title": "🚨 Log Alert Detected",
            "color": color.get(events[0].level, 5814783),
            "fields": [
                {"name": "Total Events", "value": str(len(events)), "inline": True},
                {"name": "Timestamp", "value": events[0].timestamp, "inline": True},
            ],
            "timestamp": events[0].timestamp,
        }

        # 각 레벨의 요약 추가
        for level, level_events in by_level.items():
            emoji = {"error": "❌", "warning": "⚠️", "drift": "🔄", "critical": "🔴"}.get(
                level, "📝"
            )
            embed["fields"].append(
                {
                    "name": f"{emoji} {level.upper()}",
                    "value": str(len(level_events)),
                    "inline": True,
                }
            )

        # 최근 5개 이벤트 추가
        recent_events = events[:5]
        event_list = "\n".join(
            [
                f"- `{event.log_file}`: {event.level.upper()} - {event.message[:100]}"
                for event in recent_events
            ]
        )

        embed["description"] = f"```\n{event_list}\n```"

        message = {"embeds": [embed]}

        try:
            req = Request(
                webhook_url,
                data=json.dumps(message).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            urlopen(req, timeout=10)
            return True
        except URLError as e:
            logger.error(f"Discord alert failed: {e}")
            return False

    @staticmethod
    def send_to_context7(events: List[LogEvent]) -> bool:
        """Context7에 이력 저장 (API 호출)"""
        if not events:
            return False

        # API endpoint가 있다면 호출
        try:
            import httpx

            payload = {
                "events": [e.__dict__ for e in events],
                "timestamp": datetime.now(UTC).isoformat(),
            }

            response = httpx.post(
                "http://localhost:8010/api/logs/ingest",
                json=payload,
                timeout=5.0,
            )

            return response.status_code == 200

        except Exception as e:
            logger.warning(f"Context7 API call failed (expected if API not available): {e}")
            return False


async def monitor_once(monitor: LogMonitor, sender: AlertSender) -> int:
    """단일 모니터링 사이클"""
    # 로그 파일 해결
    monitor.resolve_log_files()

    if not monitor.log_files:
        logger.warning("No log files found to monitor")
        return 0

    # 이벤트 감지
    events = monitor.detect_events()

    if not events:
        logger.debug("No new events detected")
        return 0

    logger.info(f"Detected {len(events)} new events")

    # 이력 저장
    monitor.save_history(events)

    # Discord 알림
    if monitor.config.webhook_url:
        AlertSender.send_discord_alert(events, monitor.config.webhook_url)

    # Context7 전송
    AlertSender.send_to_context7(events)

    return len(events)


async def continuous_monitor(monitor: LogMonitor, sender: AlertSender, interval: int = 60):
    """지속적 모니터링"""
    logger.info("🚀 Log Monitor started")
    logger.info(f"📋 Monitoring {len(monitor.log_files)} log files")
    logger.info(f"🔔 Min level: {monitor.config.min_level}")
    logger.info(f"⏰ Check interval: {interval}s")

    while True:
        try:
            event_count = await monitor_once(monitor, sender)

            if event_count > 0:
                logger.info(f"✅ Processed {event_count} events")

        except Exception as e:
            logger.error(f"❌ Monitor cycle failed: {e}", exc_info=True)

        # 다음 사이클까지 대기
        await asyncio.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(description="Log to Agent Bridge System")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run single monitoring cycle",
    )
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Run continuous monitoring",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Monitoring interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--discord-webhook",
        help="Discord webhook URL for alerts",
    )
    parser.add_argument(
        "--min-level",
        default="warning",
        choices=["error", "warning", "drift", "critical"],
        help="Minimum level to trigger alerts",
    )
    parser.add_argument(
        "--cooldown",
        type=int,
        default=300,
        help="Cooldown time in seconds (default: 300)",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # 환경변수에서 webhook URL 가져오기
    webhook_url = args.discord_webhook or os.environ.get("DISCORD_WEBHOOK_URL")

    # 설정 생성
    config = AlertConfig(
        webhook_url=webhook_url,
        min_level=args.min_level,
        cooldown_seconds=args.cooldown,
    )

    # 모니터 및 전송기 초기화
    monitor = LogMonitor(config)
    sender = AlertSender()

    # 실행 모드 선택
    if args.once:
        event_count = asyncio.run(monitor_once(monitor, sender))

        print("\n🔍 Log Monitor Results")
        print(f"- Events detected: {event_count}")
        print(f"- Min level: {config.min_level}")
        print(f"- Webhook configured: {'Yes' if webhook_url else 'No'}")

    elif args.continuous:
        try:
            asyncio.run(continuous_monitor(monitor, sender, args.interval))
        except KeyboardInterrupt:
            logger.info("🛑 Monitor stopped by user")

    else:
        parser.print_help()


if __name__ == "__main__":
    import sys

    sys.exit(main())
