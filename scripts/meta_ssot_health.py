#!/usr/bin/env python3
"""
Meta-SSOT Health Monitor (메타인지 기반 자기참조 시스템) v2.0

원칙: "감시자를 감시하라" (Quis custodiet ipsos custodes?)

⚠️ DEPRECATED: This file is a thin wrapper for backward compatibility.
   Use `scripts.meta_ssot` module directly for new code.

Usage:
    python scripts/meta_ssot_health.py
    python -m scripts.meta_ssot.cli
"""

import sys
from pathlib import Path

# Add repo root to sys.path for module imports
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Re-export from modular structure for backward compatibility
from scripts.meta_ssot.checkers import (
    check_artifact_dir,
    check_document_drift_dir,
    check_github_action,
    check_launchd,
    check_log_file,
    check_ticket_sync_dir,
)
from scripts.meta_ssot.cli import main
from scripts.meta_ssot.config import (
    AUTOMATION_REGISTRY,
    LAUNCHD_SERVICES,
    AutomationSpec,
    get_repo_root,
)
from scripts.meta_ssot.metacognitive import (
    check_launchd_runtime,
    cross_validate_data,
    self_heal,
)
from scripts.meta_ssot.notifier import send_discord_alert, should_alert
from scripts.meta_ssot.orchestrator import (
    check_launchd_installation,
    run_health_check,
)
from scripts.meta_ssot.reporter import print_report

__all__ = [
    # Config
    "AutomationSpec",
    "AUTOMATION_REGISTRY",
    "LAUNCHD_SERVICES",
    "get_repo_root",
    # Checkers
    "check_log_file",
    "check_artifact_dir",
    "check_document_drift_dir",
    "check_ticket_sync_dir",
    "check_launchd",
    "check_github_action",
    # Metacognitive
    "check_launchd_runtime",
    "cross_validate_data",
    "self_heal",
    # Notifier
    "send_discord_alert",
    "should_alert",
    # Reporter
    "print_report",
    # Orchestrator
    "run_health_check",
    "check_launchd_installation",
    # CLI
    "main",
]

if __name__ == "__main__":
    sys.exit(main())
