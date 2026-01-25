"""
Meta-SSOT Health Monitor Module (메타인지 기반 자기참조 시스템) v2.0

원칙: "감시자를 감시하라" (Quis custodiet ipsos custodes?)

Modules:
- config: Constants, TypedDict definitions, registries
- checkers: Individual health check functions
- metacognitive: v2.0 self-healing layer
- notifier: Discord webhook notifications
- reporter: Console/file output
- orchestrator: Main execution logic
- cli: Command-line interface
"""

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
