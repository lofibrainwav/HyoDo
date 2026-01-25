"""
Meta-SSOT Config - Constants, TypedDict definitions, and registries

SSOT: 모든 자동화 시스템 정의 (단일 진실 공급원)
"""

import subprocess
from pathlib import Path
from typing import Optional, TypedDict


class AutomationSpec(TypedDict):
    """자동화 시스템 스펙 정의"""

    name: str
    path: str
    expected_interval_hours: int
    log_path: Optional[str]
    check_method: str  # "log_file" | "artifact_dir" | "git_action" | "launchd"


# SSOT: 모든 자동화 시스템 레지스트리
AUTOMATION_REGISTRY: list[AutomationSpec] = [
    {
        "name": "SSOT Drift Monitor",
        "path": "scripts/ssot_drift_monitor.sh",
        "expected_interval_hours": 24,
        "log_path": None,
        "check_method": "artifact_dir",
    },
    {
        "name": "Unified Ticket Sync",
        "path": "scripts/unified_ticket_sync.py",
        "expected_interval_hours": 1,
        "log_path": None,
        "check_method": "ticket_sync_dir",
    },
    {
        "name": "Drift Detector",
        "path": "scripts/drift_detector.sh",
        "expected_interval_hours": 168,  # pre-push 시 실행, 주간 기준
        "log_path": None,
        "check_method": "git_action",
    },
    {
        "name": "Personas Drift Guard",
        "path": "scripts/ssot_personas_drift_guard.py",
        "expected_interval_hours": 168,
        "log_path": None,
        "check_method": "git_action",
    },
    {
        "name": "Meta SSOT Health (자기참조)",
        "path": "scripts/meta_ssot_health.py",
        "expected_interval_hours": 24,
        "log_path": "artifacts/run/meta_ssot_health.out",
        "check_method": "log_file",
    },
    {
        "name": "Document Drift Detector",
        "path": "scripts/ssot_document_drift.py",
        "expected_interval_hours": 24,
        "log_path": None,
        "check_method": "document_drift_dir",
    },
]

# launchd 서비스 목록
LAUNCHD_SERVICES = [
    "com.afo.meta_ssot_health",
    "com.afo.unified_ticket_sync",
    "com.afo.ssot_document_drift",
]


def get_repo_root() -> Path:
    """저장소 루트 경로 반환"""
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())
