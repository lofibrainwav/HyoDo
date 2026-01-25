"""
Meta-SSOT Orchestrator - Main execution logic

Contains:
- run_health_check: Main health check execution
- check_launchd_installation: launchd plist installation check
"""

from datetime import datetime
from pathlib import Path

from scripts.meta_ssot.checkers import (
    check_artifact_dir,
    check_document_drift_dir,
    check_launchd,
    check_log_file,
    check_ticket_sync_dir,
)
from scripts.meta_ssot.config import AUTOMATION_REGISTRY, LAUNCHD_SERVICES, get_repo_root


def run_health_check() -> dict:
    """모든 자동화 시스템 건강 체크 실행"""
    repo = get_repo_root()
    results = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "HEALTHY",
        "systems": [],
        "meta": {
            "total": len(AUTOMATION_REGISTRY),
            "healthy": 0,
            "warning": 0,
            "stale": 0,
            "missing": 0,
            "error": 0,
        },
    }

    for spec in AUTOMATION_REGISTRY:
        # 스크립트 존재 여부 확인
        script_path = repo / spec["path"]
        exists = script_path.exists()

        # 체크 방법에 따라 분기
        if spec["check_method"] == "log_file" and spec["log_path"]:
            health = check_log_file(repo, spec["log_path"], spec["expected_interval_hours"])
        elif spec["check_method"] == "artifact_dir":
            health = check_artifact_dir(repo, spec["expected_interval_hours"])
        elif spec["check_method"] == "launchd":
            health = check_launchd(spec["name"])
        elif spec["check_method"] == "git_action":
            health = {"status": "SKIP", "message": "Manual/pre-push trigger", "last_run": None}
        elif spec["check_method"] == "document_drift_dir":
            health = check_document_drift_dir(repo, spec["expected_interval_hours"])
        elif spec["check_method"] == "ticket_sync_dir":
            health = check_ticket_sync_dir(repo, spec["expected_interval_hours"])
        else:
            health = {"status": "UNKNOWN", "message": "Unknown check method", "last_run": None}

        system_result = {
            "name": spec["name"],
            "path": spec["path"],
            "exists": exists,
            "expected_interval_hours": spec["expected_interval_hours"],
            **health,
        }
        results["systems"].append(system_result)

        # 메타 통계 업데이트
        status = health["status"]
        if status == "HEALTHY":
            results["meta"]["healthy"] += 1
        elif status == "WARNING":
            results["meta"]["warning"] += 1
        elif status == "STALE":
            results["meta"]["stale"] += 1
        elif status in ("MISSING", "NOT_LOADED", "NEVER_RUN"):
            results["meta"]["missing"] += 1
        elif status in ("ERROR", "FAILED"):
            results["meta"]["error"] += 1

    # 전체 상태 결정
    if results["meta"]["error"] > 0:
        results["overall_status"] = "ERROR"
    elif results["meta"]["missing"] > 0:
        results["overall_status"] = "INCOMPLETE"
    elif results["meta"]["stale"] > 0:
        results["overall_status"] = "STALE"
    elif results["meta"]["warning"] > 0:
        results["overall_status"] = "WARNING"
    else:
        results["overall_status"] = "HEALTHY"

    return results


def check_launchd_installation() -> dict:
    """launchd plist 설치 상태 확인 (v2.0 업데이트)"""
    import subprocess

    user_agents = Path.home() / "Library" / "LaunchAgents"
    repo = get_repo_root()

    # 현재 활성 서비스 목록
    required_services = LAUNCHD_SERVICES

    result = subprocess.run(
        ["launchctl", "list"],
        capture_output=True,
        text=True,
    )

    missing_services = []
    for service in required_services:
        plist_name = f"{service}.plist"
        plist_path = user_agents / plist_name
        repo_plist = repo / "scripts" / "cron" / plist_name

        is_installed = plist_path.exists()
        is_loaded = service in result.stdout if result.returncode == 0 else False

        if not is_loaded and repo_plist.exists():
            missing_services.append(
                {
                    "service": service,
                    "plist": plist_name,
                    "installed": is_installed,
                    "loaded": is_loaded,
                }
            )

    recommendation = None
    if missing_services:
        # 첫 번째 누락된 서비스에 대한 권장 명령
        svc = missing_services[0]
        plist_path = user_agents / svc["plist"]
        repo_plist = repo / "scripts" / "cron" / svc["plist"]
        if not svc["installed"]:
            recommendation = f"cp {repo_plist} {plist_path} && launchctl load {plist_path}"
        else:
            recommendation = f"launchctl load {plist_path}"

    return {
        "total_services": len(required_services),
        "missing_count": len(missing_services),
        "missing_services": missing_services,
        "recommendation": recommendation,
    }
