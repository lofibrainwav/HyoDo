"""Contract tests for the public GitHub score check context."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def _load_workflow() -> dict:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_score_check_keeps_review_signal_advisory_and_checks_readiness() -> None:
    data = _load_workflow()
    job = data["jobs"]["trinity-score"]

    assert job["name"] == "HyoDo Integrity Score"
    run_text = "\n".join(step.get("run", "") for step in job["steps"])
    assert any(
        step.get("name") == "Validate HyoDo public release readiness" for step in job["steps"]
    )
    assert "Scores are advisory; required release gates determine readiness" in run_text
    assert "HYOGOOK V5 Score" not in job["name"]
