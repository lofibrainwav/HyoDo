"""Contract tests for advisory mutation workflow boundaries."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "mutation.yml"


def _load_workflow() -> dict:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_advisory_mutation_does_not_enter_pull_request_merge_rollup() -> None:
    data = _load_workflow()
    assert "pull_request" not in data["on"]


def test_full_core_schedule_and_manual_scopes_remain_available() -> None:
    data = _load_workflow()
    triggers = data["on"]

    assert triggers["schedule"] == [{"cron": "17 9 * * 1"}]
    assert triggers["workflow_dispatch"]["inputs"]["scope"]["options"] == [
        "scoring",
        "full",
        "both",
    ]
