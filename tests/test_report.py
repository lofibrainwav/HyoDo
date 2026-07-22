"""Contracts for the local, evidence-only FDE sign-off report."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _write_evidence(root: Path) -> None:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\nallowed_tools = ["safe"]\n', encoding="utf-8"
    )
    # ``evaluated_by`` is what makes a decision countable evidence. Without it an entry
    # is only a caller assertion — test_policy_self_report_boundary.py pins that an
    # unstamped ALLOW is reported as unevaluated instead of tallied.
    events = [
        {"policy": {"decision": "ALLOW", "evaluated_by": "hyodo.policy/v1"}},
        {"policy": {"decision": "DENY", "evaluated_by": "hyodo.policy/v1"}},
    ]
    (hyodo_dir / "agent-events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )
    (hyodo_dir / "eval-runs.jsonl").write_text(
        json.dumps({"status": "PASS", "pass_rate": 0.75, "result_path": ".hyodo/eval-runs/a.json"})
        + "\n",
        encoding="utf-8",
    )


def test_report_is_hash_stable_and_never_marks_missing_schema_as_pass(tmp_path: Path) -> None:
    _write_evidence(tmp_path)
    first = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "md", "--json"])
    second = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "md", "--json"])

    assert first.exit_code == second.exit_code == 0
    first_summary = json.loads(first.output)
    assert first_summary["report_hash"] == json.loads(second.output)["report_hash"]
    report = (tmp_path / first_summary["result_path"]).read_text(encoding="utf-8")
    assert "Events: 2 (ALLOW: 1, DENY: 1)" in report
    assert "Eval pass rate: 75.0%" in report
    assert "Schema gate results: Not measured" in report
    assert "Schema gate results: PASS" not in report
    assert "## Human sign-off" in report


def test_report_renders_local_html_and_marks_all_missing_evidence_not_measured(
    tmp_path: Path,
) -> None:
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "html", "--json"])

    assert result.exit_code == 0
    summary = json.loads(result.output)
    html = (tmp_path / summary["result_path"]).read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert "Not measured" in html
    assert "Eval pass rate: Not measured" in html
