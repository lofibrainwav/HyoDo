"""
Meta-SSOT Checkers - Individual health check functions

Contains all the check_* functions for different health check methods.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path


def check_log_file(repo: Path, log_path: str, expected_hours: int) -> dict:
    """로그 파일 기반 건강 체크"""
    full_path = repo / log_path
    if not full_path.exists():
        return {
            "status": "MISSING",
            "message": f"Log file not found: {log_path}",
            "last_run": None,
        }

    mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600

    if age_hours > expected_hours * 2:
        status = "STALE"
    elif age_hours > expected_hours:
        status = "WARNING"
    else:
        status = "HEALTHY"

    return {
        "status": status,
        "message": f"Last modified {age_hours:.1f}h ago",
        "last_run": mtime.isoformat(),
    }


def check_artifact_dir(repo: Path, expected_hours: int) -> dict:
    """artifact 디렉토리 기반 건강 체크 (drift_* 폴더)"""
    artifacts_dir = repo / "artifacts"
    drift_dirs = sorted(artifacts_dir.glob("drift_*"), reverse=True)

    if not drift_dirs:
        return {
            "status": "MISSING",
            "message": "No drift artifacts found",
            "last_run": None,
        }

    latest = drift_dirs[0]
    # drift_YYYYMMDD-HHMMSS 형식 파싱
    try:
        timestamp_str = latest.name.replace("drift_", "")
        mtime = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
    except ValueError:
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)

    age_hours = (datetime.now() - mtime).total_seconds() / 3600

    if age_hours > expected_hours * 2:
        status = "STALE"
    elif age_hours > expected_hours:
        status = "WARNING"
    else:
        status = "HEALTHY"

    return {
        "status": status,
        "message": f"Latest: {latest.name} ({age_hours:.1f}h ago)",
        "last_run": mtime.isoformat(),
    }


def check_document_drift_dir(repo: Path, expected_hours: int) -> dict:
    """문서 드리프트 디렉토리 기반 건강 체크"""
    drift_dir = repo / "artifacts" / "document_drift"
    drift_files = sorted(drift_dir.glob("drift_*.json"), reverse=True)

    if not drift_files:
        return {
            "status": "MISSING",
            "message": "No document drift reports found",
            "last_run": None,
        }

    latest = drift_files[0]
    # drift_YYYYMMDD-HHMMSS.json 형식 파싱
    try:
        timestamp_str = latest.stem.replace("drift_", "")
        mtime = datetime.strptime(timestamp_str, "%Y%m%d-%H%M%S")
    except ValueError:
        mtime = datetime.fromtimestamp(latest.stat().st_mtime)

    age_hours = (datetime.now() - mtime).total_seconds() / 3600

    if age_hours > expected_hours * 2:
        status = "STALE"
    elif age_hours > expected_hours:
        status = "WARNING"
    else:
        status = "HEALTHY"

    return {
        "status": status,
        "message": f"Latest: {latest.name} ({age_hours:.1f}h ago)",
        "last_run": mtime.isoformat(),
    }


def check_ticket_sync_dir(repo: Path, expected_hours: int) -> dict:
    """티켓 동기화 디렉토리 기반 건강 체크"""
    sync_dir = repo / "artifacts" / "ticket_sync"
    dashboard_file = sync_dir / "dashboard_tickets.json"

    if not dashboard_file.exists():
        return {
            "status": "MISSING",
            "message": "No ticket sync dashboard found",
            "last_run": None,
        }

    mtime = datetime.fromtimestamp(dashboard_file.stat().st_mtime)
    age_hours = (datetime.now() - mtime).total_seconds() / 3600

    # 추가 정보: completion rate 읽기
    try:
        data = json.loads(dashboard_file.read_text())
        completion = data.get("summary", {}).get("completion_rate", 0)
        extra_info = f", {completion}% done"
    except Exception:
        extra_info = ""

    if age_hours > expected_hours * 2:
        status = "STALE"
    elif age_hours > expected_hours:
        status = "WARNING"
    else:
        status = "HEALTHY"

    return {
        "status": status,
        "message": f"Last sync {age_hours:.1f}h ago{extra_info}",
        "last_run": mtime.isoformat(),
    }


def check_launchd(label: str) -> dict:
    """launchd 서비스 상태 체크"""
    try:
        result = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            check=True,
        )
        if label in result.stdout:
            return {
                "status": "HEALTHY",
                "message": f"launchd service '{label}' is loaded",
                "last_run": None,
            }
        return {
            "status": "NOT_LOADED",
            "message": f"launchd service '{label}' not found in launchctl list",
            "last_run": None,
        }
    except subprocess.CalledProcessError:
        return {
            "status": "ERROR",
            "message": "Failed to check launchctl",
            "last_run": None,
        }


def check_github_action(repo: Path, workflow_name: str) -> dict:
    """GitHub Actions 워크플로우 상태 체크 (gh CLI 사용)"""
    try:
        result = subprocess.run(
            [
                "gh",
                "run",
                "list",
                "--workflow",
                workflow_name,
                "--limit",
                "1",
                "--json",
                "conclusion,createdAt",
            ],
            capture_output=True,
            text=True,
            cwd=repo,
        )
        if result.returncode != 0:
            return {
                "status": "UNKNOWN",
                "message": "gh CLI not available or not authenticated",
                "last_run": None,
            }

        runs = json.loads(result.stdout)
        if not runs:
            return {
                "status": "NEVER_RUN",
                "message": f"No runs found for {workflow_name}",
                "last_run": None,
            }

        latest = runs[0]
        return {
            "status": "HEALTHY" if latest.get("conclusion") == "success" else "FAILED",
            "message": f"Last run: {latest.get('conclusion', 'unknown')}",
            "last_run": latest.get("createdAt"),
        }
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        return {
            "status": "ERROR",
            "message": str(e),
            "last_run": None,
        }
