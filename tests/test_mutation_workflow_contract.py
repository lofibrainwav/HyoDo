"""Contract tests for targeted mutation workflow triggering."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "mutation.yml"


def _load_workflow() -> dict:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_scoring_mutation_pull_request_trigger_is_targeted() -> None:
    data = _load_workflow()
    paths = set(data["on"]["pull_request"]["paths"])

    assert paths == {
        "hyodo/__init__.py",
        "tests/test_scoring_math.py",
        "tests/test_scoring_properties.py",
        "tests/conftest.py",
        "cosmic-ray.scoring.toml",
        "pyproject.toml",
        ".github/workflows/mutation.yml",
    }

    assert "hyodo/**" not in paths
    assert "tests/**" not in paths
    assert "cosmic-ray*.toml" not in paths
    assert "docs/research/mutation-testing-receipt.md" not in paths


def test_full_core_schedule_and_manual_scopes_remain_available() -> None:
    data = _load_workflow()
    triggers = data["on"]

    assert triggers["schedule"] == [{"cron": "17 9 * * 1"}]
    assert triggers["workflow_dispatch"]["inputs"]["scope"]["options"] == [
        "scoring",
        "full",
        "both",
    ]
