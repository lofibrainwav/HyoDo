"""
Meta-SSOT Metacognitive Layer - v2.0 self-healing features

Contains:
- launchd runtime status check
- Cross-validation between data sources
- Self-healing (auto-repair of failed services)
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from scripts.meta_ssot.config import LAUNCHD_SERVICES


def check_launchd_runtime() -> dict:
    """launchd 서비스 런타임 상태 체크 (메타인지 계층)"""
    results = {
        "total": len(LAUNCHD_SERVICES),
        "loaded": 0,
        "running": 0,
        "services": [],
    }

    try:
        # launchctl list 실행
        proc = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
        )

        for service in LAUNCHD_SERVICES:
            loaded = service in proc.stdout
            # 서비스가 로드되어 있으면 실행 상태 확인
            running = False
            last_exit = None

            if loaded:
                results["loaded"] += 1
                # 각 라인에서 서비스 상태 파싱: PID STATUS LABEL
                for line in proc.stdout.split("\n"):
                    if service in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            pid = parts[0]
                            last_exit = parts[1] if parts[1] != "-" else "0"
                            running = pid != "-"
                            if running:
                                results["running"] += 1
                        break

            results["services"].append(
                {
                    "name": service,
                    "loaded": loaded,
                    "running": running,
                    "last_exit_code": last_exit,
                }
            )

    except Exception as e:
        results["error"] = str(e)

    return results


def cross_validate_data(repo: Path) -> dict:
    """교차 검증: 여러 데이터 소스 간 일관성 체크 (메타인지 계층)"""
    validations = []

    # 1. meta_ssot_health.json vs 실제 artifact 상태
    meta_json = repo / "artifacts" / "meta_ssot_health.json"
    if meta_json.exists():
        try:
            meta_data = json.loads(meta_json.read_text())
            meta_timestamp = meta_data.get("timestamp", "")

            # 실제 파일 수정 시간과 비교
            actual_mtime = datetime.fromtimestamp(meta_json.stat().st_mtime)
            reported_time = datetime.fromisoformat(meta_timestamp) if meta_timestamp else None

            if reported_time:
                drift_seconds = abs((actual_mtime - reported_time).total_seconds())
                validations.append(
                    {
                        "check": "meta_ssot_json_timestamp",
                        "valid": drift_seconds < 60,  # 1분 이내 허용
                        "drift_seconds": drift_seconds,
                    }
                )
        except Exception as e:
            validations.append(
                {
                    "check": "meta_ssot_json_timestamp",
                    "valid": False,
                    "error": str(e),
                }
            )

    # 2. ticket_sync 데이터 일관성
    ticket_json = repo / "artifacts" / "ticket_sync" / "dashboard_tickets.json"
    if ticket_json.exists():
        try:
            ticket_data = json.loads(ticket_json.read_text())
            summary = ticket_data.get("summary", {})

            # 총합 검증: total = open + closed
            total = summary.get("total_issues", 0)
            open_count = summary.get("open_count", 0)
            closed_count = summary.get("closed_count", 0)

            validations.append(
                {
                    "check": "ticket_counts_consistency",
                    "valid": total == open_count + closed_count,
                    "total": total,
                    "open": open_count,
                    "closed": closed_count,
                }
            )
        except Exception as e:
            validations.append(
                {
                    "check": "ticket_counts_consistency",
                    "valid": False,
                    "error": str(e),
                }
            )

    # 3. document_drift 최신 파일과 실제 문서 상태 비교
    drift_dir = repo / "artifacts" / "document_drift"
    drift_files = sorted(drift_dir.glob("drift_*.json"), reverse=True) if drift_dir.exists() else []

    if drift_files:
        try:
            latest_drift = json.loads(drift_files[0].read_text())
            docs_checked = latest_drift.get("documents_checked", 0)
            docs_drifted = latest_drift.get("documents_drifted", 0)

            validations.append(
                {
                    "check": "document_drift_sanity",
                    "valid": docs_drifted <= docs_checked,
                    "checked": docs_checked,
                    "drifted": docs_drifted,
                }
            )
        except Exception as e:
            validations.append(
                {
                    "check": "document_drift_sanity",
                    "valid": False,
                    "error": str(e),
                }
            )

    return {
        "validations": validations,
        "all_valid": all(v.get("valid", False) for v in validations),
        "total_checks": len(validations),
        "passed": sum(1 for v in validations if v.get("valid", False)),
    }


def self_heal(repo: Path, dry_run: bool = True) -> dict:
    """자가 치유: 실패한 서비스 재시작 시도 (메타인지 계층)"""
    import shutil

    actions = []
    user_agents = Path.home() / "Library" / "LaunchAgents"

    # launchd 런타임 상태 확인
    runtime = check_launchd_runtime()

    for service_info in runtime.get("services", []):
        service_name = service_info["name"]
        plist_name = f"{service_name}.plist"
        plist_path = user_agents / plist_name
        repo_plist = repo / "scripts" / "cron" / plist_name

        # 케이스 1: plist가 설치되어 있지 않은 경우
        if not plist_path.exists() and repo_plist.exists():
            action = {
                "service": service_name,
                "issue": "not_installed",
                "action": f"cp {repo_plist} {plist_path}",
                "executed": False,
            }
            if not dry_run:
                try:
                    shutil.copy(repo_plist, plist_path)
                    action["executed"] = True
                except Exception as e:
                    action["error"] = str(e)
            actions.append(action)

        # 케이스 2: plist가 설치되었지만 로드되지 않은 경우
        elif plist_path.exists() and not service_info["loaded"]:
            action = {
                "service": service_name,
                "issue": "not_loaded",
                "action": f"launchctl load {plist_path}",
                "executed": False,
            }
            if not dry_run:
                try:
                    subprocess.run(
                        ["launchctl", "load", str(plist_path)],
                        check=True,
                        capture_output=True,
                    )
                    action["executed"] = True
                except Exception as e:
                    action["error"] = str(e)
            actions.append(action)

        # 케이스 3: 서비스가 로드되었지만 마지막 실행이 실패한 경우
        elif service_info["loaded"] and service_info.get("last_exit_code") not in (None, "0", 0):
            action = {
                "service": service_name,
                "issue": f"last_exit_code={service_info.get('last_exit_code')}",
                "action": f"launchctl kickstart -k user/$(id -u)/{service_name}",
                "executed": False,
            }
            if not dry_run:
                try:
                    uid = subprocess.run(
                        ["id", "-u"], capture_output=True, text=True
                    ).stdout.strip()
                    subprocess.run(
                        ["launchctl", "kickstart", "-k", f"user/{uid}/{service_name}"],
                        check=True,
                        capture_output=True,
                    )
                    action["executed"] = True
                except Exception as e:
                    action["error"] = str(e)
            actions.append(action)

    return {
        "dry_run": dry_run,
        "actions": actions,
        "healed": sum(1 for a in actions if a.get("executed", False)),
        "pending": sum(1 for a in actions if not a.get("executed", False) and "error" not in a),
    }
