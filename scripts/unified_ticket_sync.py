#!/usr/bin/env python3
"""
Unified Ticket Sync System (통합 티켓 동기화 시스템)

모든 Phase의 Issue Sync Map을 자동 동기화하고 알림을 전송합니다.

기능:
1. 모든 마크다운 파일에서 Issue Sync Map 섹션 검색
2. GitHub CLI로 이슈 상태 동기화
3. Slack/Discord 웹훅 알림
4. Dashboard용 JSON 출력
5. 변경 이력 추적
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

# ═══════════════════════════════════════════════════════════════
# 설정
# ═══════════════════════════════════════════════════════════════

ISSUE_SYNC_PATTERN = re.compile(r"##\s+🔗\s+(.+?)\s+Issue\s+Sync\s+Map", re.IGNORECASE)
TABLE_ROW_PATTERN = re.compile(
    r"\|\s*(\w+)\s*\|\s*(.+?)\s*\|\s*(#\d+)\s*\|\s*(OPEN|CLOSED)\s*\|\s*(.+?)\s*\|"
)
STATUS_LINE_PATTERN = re.compile(r">\s*상태 기준:.*마지막 동기화:\s*(\d{4}-\d{2}-\d{2})")

TRACKED_FILES = [
    "TICKETS.md",
    "docs/TICKETS_PHASE1.md",
    "docs/TICKETS_PHASE2.md",
]

OUTPUT_DIR = Path("artifacts/ticket_sync")
HISTORY_FILE = OUTPUT_DIR / "sync_history.json"


# ═══════════════════════════════════════════════════════════════
# 데이터 모델
# ═══════════════════════════════════════════════════════════════


@dataclass
class IssueInfo:
    """이슈 정보"""

    layer: str
    ticket: str
    issue_number: str
    status: str
    notes: str
    new_status: Optional[str] = None

    @property
    def changed(self) -> bool:
        return self.new_status is not None and self.new_status != self.status


@dataclass
class SyncMapSection:
    """Issue Sync Map 섹션 정보"""

    name: str
    file_path: str
    line_start: int
    line_end: int
    issues: List[IssueInfo] = field(default_factory=list)
    last_sync: Optional[str] = None


@dataclass
class SyncResult:
    """동기화 결과"""

    timestamp: str
    sections: List[SyncMapSection]
    total_issues: int = 0
    changed_issues: int = 0
    open_count: int = 0
    closed_count: int = 0


# ═══════════════════════════════════════════════════════════════
# GitHub CLI 연동
# ═══════════════════════════════════════════════════════════════


def find_gh_cli() -> Optional[str]:
    """GitHub CLI 경로 찾기"""
    env_path = os.environ.get("GH_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    gh_path = shutil.which("gh")
    if gh_path:
        return gh_path

    for candidate in ("/opt/homebrew/bin/gh", "/usr/local/bin/gh", "/usr/bin/gh"):
        if Path(candidate).exists():
            return candidate

    return None


def fetch_github_issues() -> dict[str, str]:
    """GitHub에서 이슈 상태 가져오기"""
    gh_path = find_gh_cli()
    if not gh_path:
        print("⚠️  GitHub CLI (gh) not found - using cached data if available")
        return {}

    try:
        result = subprocess.run(
            [gh_path, "issue", "list", "-L", "500", "--state", "all", "--json", "number,state"],
            check=True,
            capture_output=True,
            text=True,
        )
        data = json.loads(result.stdout)
        return {f"#{item['number']}": item["state"].upper() for item in data}
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"⚠️  Failed to fetch issues: {e}")
        return {}


# ═══════════════════════════════════════════════════════════════
# 마크다운 파싱
# ═══════════════════════════════════════════════════════════════


def find_sync_map_sections(repo: Path) -> List[SyncMapSection]:
    """모든 마크다운 파일에서 Issue Sync Map 섹션 찾기"""
    sections: List[SyncMapSection] = []

    # 먼저 TRACKED_FILES 확인
    for file_path in TRACKED_FILES:
        full_path = repo / file_path
        if full_path.exists():
            found = parse_sync_sections(full_path)
            sections.extend(found)

    # 추가로 docs/ 디렉토리 스캔
    for md_file in (repo / "docs").glob("*.md"):
        if md_file.name not in [Path(f).name for f in TRACKED_FILES]:
            found = parse_sync_sections(md_file)
            sections.extend(found)

    return sections


def parse_sync_sections(file_path: Path) -> List[SyncMapSection]:
    """파일에서 Issue Sync Map 섹션 파싱"""
    sections: List[SyncMapSection] = []
    content = file_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    current_section: Optional[SyncMapSection] = None
    in_table = False

    for i, line in enumerate(lines, 1):
        # Issue Sync Map 헤더 찾기
        header_match = ISSUE_SYNC_PATTERN.search(line)
        if header_match:
            if current_section:
                current_section.line_end = i - 1
                sections.append(current_section)

            current_section = SyncMapSection(
                name=header_match.group(1).strip(),
                file_path=str(file_path),
                line_start=i,
                line_end=i,
            )
            in_table = False
            continue

        if current_section:
            # 상태 라인 찾기
            status_match = STATUS_LINE_PATTERN.search(line)
            if status_match:
                current_section.last_sync = status_match.group(1)
                continue

            # 테이블 행 찾기
            row_match = TABLE_ROW_PATTERN.search(line)
            if row_match:
                in_table = True
                issue = IssueInfo(
                    layer=row_match.group(1),
                    ticket=row_match.group(2).strip(),
                    issue_number=row_match.group(3),
                    status=row_match.group(4),
                    notes=row_match.group(5).strip(),
                )
                current_section.issues.append(issue)
                current_section.line_end = i
            elif in_table and not line.strip().startswith("|"):
                # 테이블 끝
                in_table = False

    if current_section:
        sections.append(current_section)

    return sections


# ═══════════════════════════════════════════════════════════════
# 동기화 로직
# ═══════════════════════════════════════════════════════════════


def sync_issues(sections: List[SyncMapSection], github_states: dict[str, str]) -> SyncResult:
    """이슈 상태 동기화"""
    result = SyncResult(
        timestamp=datetime.now().isoformat(),
        sections=sections,
    )

    for section in sections:
        for issue in section.issues:
            result.total_issues += 1

            github_status = github_states.get(issue.issue_number)
            if github_status:
                if github_status != issue.status:
                    issue.new_status = github_status
                    result.changed_issues += 1

            final_status = issue.new_status or issue.status
            if final_status == "OPEN":
                result.open_count += 1
            else:
                result.closed_count += 1

    return result


def update_markdown_files(sections: List[SyncMapSection]) -> int:
    """마크다운 파일 업데이트"""
    updated_count = 0
    files_to_update: dict[str, List[SyncMapSection]] = {}

    for section in sections:
        if any(issue.changed for issue in section.issues):
            if section.file_path not in files_to_update:
                files_to_update[section.file_path] = []
            files_to_update[section.file_path].append(section)

    for file_path, file_sections in files_to_update.items():
        path = Path(file_path)
        content = path.read_text(encoding="utf-8")
        lines = content.splitlines()
        today = datetime.now().strftime("%Y-%m-%d")

        for section in file_sections:
            for issue in section.issues:
                if issue.changed:
                    # 테이블에서 해당 이슈 행 찾아서 업데이트
                    for i, line in enumerate(lines):
                        if issue.issue_number in line and TABLE_ROW_PATTERN.search(line):
                            lines[i] = line.replace(
                                f"| {issue.status} |", f"| {issue.new_status} |"
                            )
                            updated_count += 1
                            break

        # 마지막 동기화 날짜 업데이트
        for i, line in enumerate(lines):
            if STATUS_LINE_PATTERN.search(line):
                lines[i] = re.sub(
                    r"마지막 동기화:\s*\d{4}-\d{2}-\d{2}", f"마지막 동기화: {today}", line
                )
                break

        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return updated_count


# ═══════════════════════════════════════════════════════════════
# 알림 시스템
# ═══════════════════════════════════════════════════════════════


def send_slack_notification(webhook_url: str, result: SyncResult) -> bool:
    """Slack 웹훅으로 알림 전송"""
    if not webhook_url:
        return False

    # 변경된 이슈 목록
    changes = []
    for section in result.sections:
        for issue in section.issues:
            if issue.changed:
                emoji = "✅" if issue.new_status == "CLOSED" else "🔄"
                changes.append(f"{emoji} {issue.issue_number}: {issue.status} → {issue.new_status}")

    if not changes:
        return True  # 변경 없으면 알림 안 보냄

    message = {
        "text": "🎫 Ticket Sync Update",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": "🎫 Ticket Sync Update"}},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Total Issues:* {result.total_issues}"},
                    {"type": "mrkdwn", "text": f"*Changed:* {result.changed_issues}"},
                    {"type": "mrkdwn", "text": f"*Open:* {result.open_count}"},
                    {"type": "mrkdwn", "text": f"*Closed:* {result.closed_count}"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "```\n" + "\n".join(changes) + "\n```"},
            },
        ],
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
        print(f"⚠️  Slack notification failed: {e}")
        return False


def send_discord_notification(webhook_url: str, result: SyncResult) -> bool:
    """Discord 웹훅으로 알림 전송"""
    if not webhook_url:
        return False

    changes = []
    for section in result.sections:
        for issue in section.issues:
            if issue.changed:
                emoji = "✅" if issue.new_status == "CLOSED" else "🔄"
                changes.append(f"{emoji} {issue.issue_number}: {issue.status} → {issue.new_status}")

    if not changes:
        return True

    message = {
        "embeds": [
            {
                "title": "🎫 Ticket Sync Update",
                "color": 5814783,
                "fields": [
                    {"name": "Total", "value": str(result.total_issues), "inline": True},
                    {"name": "Changed", "value": str(result.changed_issues), "inline": True},
                    {"name": "Open", "value": str(result.open_count), "inline": True},
                    {"name": "Closed", "value": str(result.closed_count), "inline": True},
                ],
                "description": "```\n" + "\n".join(changes) + "\n```",
                "timestamp": result.timestamp,
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
        print(f"⚠️  Discord notification failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# Dashboard JSON 출력
# ═══════════════════════════════════════════════════════════════


def generate_dashboard_json(result: SyncResult) -> dict:
    """Dashboard용 JSON 생성"""
    sections_data = []
    for section in result.sections:
        issues_data = []
        for issue in section.issues:
            issues_data.append(
                {
                    "layer": issue.layer,
                    "ticket": issue.ticket,
                    "issue": issue.issue_number,
                    "status": issue.new_status or issue.status,
                    "changed": issue.changed,
                    "notes": issue.notes,
                }
            )
        sections_data.append(
            {
                "name": section.name,
                "file": section.file_path,
                "last_sync": section.last_sync,
                "issues": issues_data,
            }
        )

    return {
        "timestamp": result.timestamp,
        "summary": {
            "total_issues": result.total_issues,
            "changed_issues": result.changed_issues,
            "open_count": result.open_count,
            "closed_count": result.closed_count,
            "completion_rate": round(result.closed_count / result.total_issues * 100, 1)
            if result.total_issues > 0
            else 0,
        },
        "sections": sections_data,
    }


def save_dashboard_json(data: dict, repo: Path) -> Path:
    """Dashboard JSON 저장"""
    output_dir = repo / OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "dashboard_tickets.json"
    output_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    return output_file


# ═══════════════════════════════════════════════════════════════
# 이력 관리
# ═══════════════════════════════════════════════════════════════


def save_sync_history(result: SyncResult, repo: Path) -> None:
    """동기화 이력 저장"""
    history_path = repo / HISTORY_FILE
    history_path.parent.mkdir(parents=True, exist_ok=True)

    history = []
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text())
        except json.JSONDecodeError:
            history = []

    # 최근 30개만 유지
    history.append(
        {
            "timestamp": result.timestamp,
            "total": result.total_issues,
            "changed": result.changed_issues,
            "open": result.open_count,
            "closed": result.closed_count,
        }
    )
    history = history[-30:]

    history_path.write_text(json.dumps(history, indent=2))


# ═══════════════════════════════════════════════════════════════
# 리포트 출력
# ═══════════════════════════════════════════════════════════════


def print_report(result: SyncResult) -> None:
    """콘솔 리포트 출력"""
    print("=" * 60)
    print("  UNIFIED TICKET SYNC REPORT")
    print("=" * 60)
    print(f"  Timestamp: {result.timestamp}")
    print("-" * 60)
    print(f"  Total Sections: {len(result.sections)}")
    print(f"  Total Issues: {result.total_issues}")
    print(f"  Changed: {result.changed_issues}")
    print(f"  Open: {result.open_count}")
    print(f"  Closed: {result.closed_count}")

    if result.total_issues > 0:
        completion = result.closed_count / result.total_issues * 100
        print(f"  Completion: {completion:.1f}%")

    print("-" * 60)

    for section in result.sections:
        print(f"\n  📋 {section.name}")
        print(f"     File: {section.file_path}")
        print(f"     Issues: {len(section.issues)}")

        changed = [i for i in section.issues if i.changed]
        if changed:
            print("     Changes:")
            for issue in changed:
                print(f"       {issue.issue_number}: {issue.status} → {issue.new_status}")

    print()
    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# 메인 함수
# ═══════════════════════════════════════════════════════════════


def main() -> int:
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Unified Ticket Sync System")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't update files, just show what would change",
    )
    parser.add_argument(
        "--slack-webhook",
        help="Slack webhook URL for notifications",
    )
    parser.add_argument(
        "--discord-webhook",
        help="Discord webhook URL for notifications",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    # 환경변수에서 웹훅 URL 가져오기
    slack_webhook = args.slack_webhook or os.environ.get("SLACK_WEBHOOK_URL")
    discord_webhook = args.discord_webhook or os.environ.get("DISCORD_WEBHOOK_URL")

    # 저장소 루트 찾기
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        repo = Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        repo = Path.cwd()

    # Issue Sync Map 섹션 찾기
    sections = find_sync_map_sections(repo)

    if not sections:
        if not args.quiet:
            print("⚠️  No Issue Sync Map sections found")
        return 0

    # GitHub 이슈 상태 가져오기
    github_states = fetch_github_issues()

    # 동기화 실행
    result = sync_issues(sections, github_states)

    # 리포트 출력
    if args.json:
        dashboard_data = generate_dashboard_json(result)
        print(json.dumps(dashboard_data, indent=2, ensure_ascii=False))
    elif not args.quiet:
        print_report(result)

    # 파일 업데이트 (dry-run이 아닐 때)
    if not args.dry_run and result.changed_issues > 0:
        updated = update_markdown_files(sections)
        if not args.quiet:
            print(f"✅ Updated {updated} issues in markdown files")

    # Dashboard JSON 저장
    dashboard_data = generate_dashboard_json(result)
    json_path = save_dashboard_json(dashboard_data, repo)
    if not args.quiet:
        print(f"📊 Dashboard JSON: {json_path}")

    # 이력 저장
    save_sync_history(result, repo)

    # 알림 전송
    if result.changed_issues > 0:
        if slack_webhook:
            if send_slack_notification(slack_webhook, result):
                if not args.quiet:
                    print("📢 Slack notification sent")

        if discord_webhook:
            if send_discord_notification(discord_webhook, result):
                if not args.quiet:
                    print("📢 Discord notification sent")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
