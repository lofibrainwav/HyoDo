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


def test_score_check_uses_public_name_and_keeps_formula_lineage() -> None:
    data = _load_workflow()
    job = data["jobs"]["trinity-score"]

    assert job["name"] == "HyoDo Integrity Score"
    run_text = "\n".join(step.get("run", "") for step in job["steps"])
    assert "HyoDo Integrity Score" in run_text
    assert "HYOGOOK V5" in run_text
    assert "HYOGOOK V5 Score" not in job["name"]
