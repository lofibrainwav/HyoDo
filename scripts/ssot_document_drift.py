#!/usr/bin/env python3
"""
SSOT Document Drift Detector (문서 해시 기반 드리프트 감지)

핵심 SSOT 문서의 해시를 추적하여 무단 변경을 감지합니다.
드리프트 발견 시 GitHub Issue를 자동 생성합니다.

원칙: "문서는 코드의 계약이다 - 계약 변경은 추적되어야 한다"
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

# ═══════════════════════════════════════════════════════════════
# SSOT: 추적할 핵심 문서 정의
# ═══════════════════════════════════════════════════════════════


class DocumentSpec(TypedDict):
    path: str
    category: str  # "governance" | "architecture" | "specification"
    criticality: str  # "critical" | "high" | "medium"
    description: str


TRACKED_DOCUMENTS: List[DocumentSpec] = [
    # Governance (통치 규칙)
    {
        "path": "CLAUDE.md",
        "category": "governance",
        "criticality": "critical",
        "description": "Claude Code 작업 지침 및 규칙",
    },
    {
        "path": "AGENTS.md",
        "category": "governance",
        "criticality": "critical",
        "description": "에이전트 거버넌스 및 Trinity Score",
    },
    {
        "path": "packages/afo-core/CLAUDE.md",
        "category": "governance",
        "criticality": "high",
        "description": "Backend 전용 Claude 지침",
    },
    {
        "path": "packages/dashboard/CLAUDE.md",
        "category": "governance",
        "criticality": "high",
        "description": "Frontend 전용 Claude 지침",
    },
    # Architecture (아키텍처)
    {
        "path": "docs/AFO_FINAL_SSOT.md",
        "category": "architecture",
        "criticality": "critical",
        "description": "최종 SSOT 정의서",
    },
    {
        "path": "docs/AFO_ROYAL_LIBRARY.md",
        "category": "architecture",
        "criticality": "critical",
        "description": "왕립 도서관 - 핵심 원칙",
    },
    {
        "path": "docs/AFO_CHANCELLOR_GRAPH_SPEC.md",
        "category": "specification",
        "criticality": "high",
        "description": "Chancellor Graph 스펙",
    },
    # Configuration (설정)
    {
        "path": "packages/trinity-os/TRINITY_OS_PERSONAS.yaml",
        "category": "specification",
        "criticality": "critical",
        "description": "Trinity Score 가중치 SSOT",
    },
]

BASELINE_FILE = "artifacts/ssot_document_baseline.json"
DRIFT_REPORT_DIR = "artifacts/document_drift"


# ═══════════════════════════════════════════════════════════════
# 해시 계산 함수
# ═══════════════════════════════════════════════════════════════


def get_repo_root() -> Path:
    """저장소 루트 경로 반환"""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def compute_file_hash(filepath: Path) -> Optional[str]:
    """파일의 SHA256 해시 계산"""
    if not filepath.exists():
        return None
    try:
        content = filepath.read_bytes()
        return hashlib.sha256(content).hexdigest()[:16]  # 16자로 축약
    except Exception:
        return None


def compute_all_hashes(repo: Path) -> Dict[str, dict]:
    """모든 추적 문서의 해시 계산"""
    results = {}
    for doc in TRACKED_DOCUMENTS:
        filepath = repo / doc["path"]
        file_hash = compute_file_hash(filepath)
        mtime = None
        if filepath.exists():
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime).isoformat()

        results[doc["path"]] = {
            "hash": file_hash,
            "exists": filepath.exists(),
            "category": doc["category"],
            "criticality": doc["criticality"],
            "description": doc["description"],
            "mtime": mtime,
        }
    return results


# ═══════════════════════════════════════════════════════════════
# 베이스라인 관리
# ═══════════════════════════════════════════════════════════════


def load_baseline(repo: Path) -> Optional[dict]:
    """저장된 베이스라인 로드"""
    baseline_path = repo / BASELINE_FILE
    if not baseline_path.exists():
        return None
    try:
        return json.loads(baseline_path.read_text())
    except Exception:
        return None


def save_baseline(repo: Path, hashes: Dict[str, dict]) -> None:
    """현재 해시를 베이스라인으로 저장"""
    baseline_path = repo / BASELINE_FILE
    baseline_path.parent.mkdir(parents=True, exist_ok=True)

    baseline = {
        "created_at": datetime.now().isoformat(),
        "documents": hashes,
    }
    baseline_path.write_text(json.dumps(baseline, indent=2, ensure_ascii=False))
    print(f"✅ Baseline saved: {baseline_path}")


# ═══════════════════════════════════════════════════════════════
# 드리프트 감지
# ═══════════════════════════════════════════════════════════════


class DriftResult(TypedDict):
    path: str
    status: str  # "changed" | "added" | "deleted" | "unchanged"
    criticality: str
    old_hash: Optional[str]
    new_hash: Optional[str]
    description: str


def detect_drift(baseline: dict, current: Dict[str, dict]) -> tuple[List[DriftResult], dict]:
    """베이스라인과 현재 상태 비교하여 드리프트 감지"""
    drifts: List[DriftResult] = []
    baseline_docs = baseline.get("documents", {})

    summary = {
        "total": len(current),
        "changed": 0,
        "added": 0,
        "deleted": 0,
        "unchanged": 0,
        "critical_drift": 0,
    }

    for path, curr_info in current.items():
        base_info = baseline_docs.get(path, {})
        old_hash = base_info.get("hash")
        new_hash = curr_info.get("hash")

        if old_hash is None and new_hash is not None:
            status = "added"
            summary["added"] += 1
        elif old_hash is not None and new_hash is None:
            status = "deleted"
            summary["deleted"] += 1
        elif old_hash != new_hash:
            status = "changed"
            summary["changed"] += 1
        else:
            status = "unchanged"
            summary["unchanged"] += 1

        if status != "unchanged":
            drift: DriftResult = {
                "path": path,
                "status": status,
                "criticality": curr_info.get("criticality", "medium"),
                "old_hash": old_hash,
                "new_hash": new_hash,
                "description": curr_info.get("description", ""),
            }
            drifts.append(drift)

            if curr_info.get("criticality") == "critical":
                summary["critical_drift"] += 1

    return drifts, summary


# ═══════════════════════════════════════════════════════════════
# GitHub Issue 생성
# ═══════════════════════════════════════════════════════════════


def create_github_issue(repo: Path, drifts: List[DriftResult], summary: dict) -> bool:
    """드리프트 발견 시 GitHub Issue 자동 생성"""
    if not drifts:
        return False

    # Issue 본문 생성
    today = datetime.now().strftime("%Y-%m-%d")
    critical_count = summary.get("critical_drift", 0)

    title = f"📄 SSOT Document Drift Detected - {today}"
    if critical_count > 0:
        title = f"🚨 CRITICAL: {title}"

    body_lines = [
        "## SSOT Document Drift Report",
        "",
        f"**Date**: {today}",
        f"**Total Documents**: {summary['total']}",
        f"**Changed**: {summary['changed']}",
        f"**Added**: {summary['added']}",
        f"**Deleted**: {summary['deleted']}",
        f"**Critical Drifts**: {critical_count}",
        "",
        "---",
        "",
        "## Detected Changes",
        "",
    ]

    for drift in drifts:
        icon = {"changed": "📝", "added": "➕", "deleted": "❌"}.get(drift["status"], "❓")
        crit_badge = "🔴" if drift["criticality"] == "critical" else "🟡"

        body_lines.append(f"### {icon} {drift['path']}")
        body_lines.append(f"- **Status**: {drift['status'].upper()}")
        body_lines.append(f"- **Criticality**: {crit_badge} {drift['criticality']}")
        body_lines.append(f"- **Description**: {drift['description']}")
        if drift["old_hash"]:
            body_lines.append(f"- **Old Hash**: `{drift['old_hash']}`")
        if drift["new_hash"]:
            body_lines.append(f"- **New Hash**: `{drift['new_hash']}`")
        body_lines.append("")

    body_lines.extend(
        [
            "---",
            "",
            "## Required Actions",
            "",
            "1. Review the changed documents",
            "2. Verify changes are intentional and approved",
            "3. Update baseline if changes are approved: `python scripts/ssot_document_drift.py --update-baseline`",
            "4. Close this issue after verification",
            "",
            "---",
            "",
            "🤖 Auto-generated by SSOT Document Drift Detector",
        ]
    )

    body = "\n".join(body_lines)

    # GitHub CLI로 Issue 생성
    labels = ["ssot", "document-drift", "automated"]
    if critical_count > 0:
        labels.append("critical")

    try:
        result = subprocess.run(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                ",".join(labels),
            ],
            capture_output=True,
            text=True,
            cwd=repo,
        )
        if result.returncode == 0:
            issue_url = result.stdout.strip()
            print(f"✅ GitHub Issue created: {issue_url}")
            return True
        else:
            print(f"⚠️  Failed to create GitHub Issue: {result.stderr}")
            return False
    except FileNotFoundError:
        print("⚠️  GitHub CLI (gh) not found - skipping issue creation")
        return False


# ═══════════════════════════════════════════════════════════════
# 리포트 생성
# ═══════════════════════════════════════════════════════════════


def save_drift_report(
    repo: Path, drifts: List[DriftResult], summary: dict, current: Dict[str, dict]
) -> Path:
    """드리프트 리포트 저장"""
    report_dir = repo / DRIFT_REPORT_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = report_dir / f"drift_{timestamp}.json"

    report = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary,
        "drifts": drifts,
        "current_state": current,
    }

    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False))
    return report_file


def print_report(drifts: List[DriftResult], summary: dict) -> None:
    """콘솔에 리포트 출력"""
    print("=" * 60)
    print("  SSOT DOCUMENT DRIFT REPORT")
    print("=" * 60)
    print(f"  Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)
    print(f"  Total Documents: {summary['total']}")
    print(f"  Changed: {summary['changed']}")
    print(f"  Added: {summary['added']}")
    print(f"  Deleted: {summary['deleted']}")
    print(f"  Unchanged: {summary['unchanged']}")
    print(f"  Critical Drifts: {summary['critical_drift']}")
    print("-" * 60)

    if not drifts:
        print("  ✅ No drift detected - all documents match baseline")
    else:
        print("  ⚠️  DRIFT DETECTED:")
        print()
        for drift in drifts:
            icon = {"changed": "📝", "added": "➕", "deleted": "❌"}.get(drift["status"], "❓")
            crit = "🔴" if drift["criticality"] == "critical" else "🟡"
            print(f"  {icon} {crit} {drift['path']}")
            print(f"       Status: {drift['status']} | {drift['description']}")
            print()

    print("=" * 60)


# ═══════════════════════════════════════════════════════════════
# Artifact 정리 (보존 정책)
# ═══════════════════════════════════════════════════════════════

RETENTION_DAYS = 30


def cleanup_old_reports(repo: Path, dry_run: bool = False) -> int:
    """오래된 드리프트 리포트 정리 (기본 30일 보존)"""
    report_dir = repo / DRIFT_REPORT_DIR
    if not report_dir.exists():
        return 0

    cutoff = datetime.now().timestamp() - (RETENTION_DAYS * 24 * 3600)
    removed = 0

    for report_file in report_dir.glob("drift_*.json"):
        if report_file.stat().st_mtime < cutoff:
            if dry_run:
                print(f"  Would remove: {report_file.name}")
            else:
                report_file.unlink()
            removed += 1

    return removed


# ═══════════════════════════════════════════════════════════════
# 메인 함수
# ═══════════════════════════════════════════════════════════════


def main() -> int:
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="SSOT Document Drift Detector")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Update baseline with current state",
    )
    parser.add_argument(
        "--create-issue",
        action="store_true",
        help="Create GitHub issue on drift detection",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up old reports (older than 30 days)",
    )
    parser.add_argument(
        "--no-auto-cleanup",
        action="store_true",
        help="Disable automatic cleanup after each run",
    )
    args = parser.parse_args()

    repo = get_repo_root()

    # 정리 전용 모드
    if args.cleanup:
        removed = cleanup_old_reports(repo, dry_run=False)
        print(f"🧹 Cleaned up {removed} old reports (>{RETENTION_DAYS} days)")
        return 0

    current = compute_all_hashes(repo)

    # 베이스라인 업데이트 모드
    if args.update_baseline:
        save_baseline(repo, current)
        return 0

    # 베이스라인 로드
    baseline = load_baseline(repo)
    if baseline is None:
        print("⚠️  No baseline found. Creating initial baseline...")
        save_baseline(repo, current)
        print("   Run again to detect drift against this baseline.")
        return 0

    # 드리프트 감지
    drifts, summary = detect_drift(baseline, current)

    # 리포트 출력
    if not args.quiet:
        print_report(drifts, summary)

    # 리포트 저장
    report_file = save_drift_report(repo, drifts, summary, current)
    if not args.quiet:
        print(f"\n📄 Report saved: {report_file}")

    # GitHub Issue 생성
    if args.create_issue and drifts:
        create_github_issue(repo, drifts, summary)

    # 자동 정리 (기본 활성화)
    if not args.no_auto_cleanup:
        removed = cleanup_old_reports(repo)
        if removed > 0 and not args.quiet:
            print(f"🧹 Auto-cleaned {removed} old reports")

    # 종료 코드
    if summary["critical_drift"] > 0:
        return 2  # Critical drift
    if drifts:
        return 1  # Non-critical drift
    return 0  # No drift


if __name__ == "__main__":
    sys.exit(main())
