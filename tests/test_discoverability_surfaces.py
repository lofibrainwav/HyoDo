"""Contracts for HyoDo discoverability surfaces.

Three artifacts make HyoDo installable where other tools already live:

1. `.pre-commit-hooks.yaml` — exposes `hyodo check` (and `hyodo safe --strict`)
   to the pre-commit framework. The pre-commit framework installs the repo
   into an isolated venv and runs `entry`; the declared `entry` here must
   therefore match a console_script that the package actually ships.
2. `hyodo report --format sarif` — writes a SARIF v2.1.0 log so results can
   appear in the GitHub Security tab via code scanning upload.
3. `.github/actions/hyodo/action.yml` — a composite action that installs HyoDo
   from the same pinned repository ref and runs `hyodo check`.

These tests pin the *shape* and ref integrity of each artifact; they do not
execute pre-commit itself or the GitHub runner.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from typer.testing import CliRunner

import hyodo
from hyodo.cli.main import app
from hyodo.report import SARIF_SCHEMA_URI

REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_PATH = REPO_ROOT / ".pre-commit-hooks.yaml"
ACTION_PATH = REPO_ROOT / ".github" / "actions" / "hyodo" / "action.yml"
README_PATH = REPO_ROOT / "README.md"
SARIF_SCHEMA_PATH = Path(__file__).parent / "fixtures" / "sarif-schema-2.1.0.json"

runner = CliRunner()


def _write_deny_evidence(root: Path) -> None:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir()
    events = [
        {"policy": {"decision": "ALLOW", "evaluated_by": "hyodo.policy/v1"}},
        {"policy": {"decision": "DENY", "evaluated_by": "hyodo.policy/v1"}},
    ]
    (hyodo_dir / "agent-events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )


# --- pre-commit hooks surface -------------------------------------------------


def test_pre_commit_hooks_file_is_present_and_valid_yaml() -> None:
    hooks = yaml.safe_load(HOOKS_PATH.read_text(encoding="utf-8"))
    assert isinstance(hooks, list)
    assert len(hooks) >= 1
    by_id = {hook["id"]: hook for hook in hooks}
    assert "hyodo-check" in by_id


def test_pre_commit_hook_entry_matches_shipped_console_script() -> None:
    """The hook `entry` must start with a console script hyodo actually ships."""
    hooks = yaml.safe_load(HOOKS_PATH.read_text(encoding="utf-8"))
    hook = next(h for h in hooks if h["id"] == "hyodo-check")
    assert hook["entry"].split()[0] == "hyodo"
    assert "check" in hook["entry"].split()

    # The console script is declared in pyproject.toml; if packaging ever drops
    # it, every consumer's pre-commit run would fail at environment setup. The
    # dispatcher preserves the mature main app and only attaches additive
    # sub-apps such as `hyodo friction`.
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'hyodo = "hyodo.cli.dispatch:app"' in pyproject


def test_pre_commit_hook_declares_non_blocking_metadata() -> None:
    hooks = yaml.safe_load(HOOKS_PATH.read_text(encoding="utf-8"))
    hook = next(h for h in hooks if h["id"] == "hyodo-check")
    assert hook["language"] == "python"
    # pass_filenames: false — gates run over the project, not the changed files.
    assert hook["pass_filenames"] is False
    assert hook["name"]


def test_composite_action_exposes_actionable_gate_failure_summary() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    steps = action["runs"]["steps"]
    run_step = next(step for step in steps if step["name"] == "Run HyoDo gates")
    failure_step = next(step for step in steps if step["name"] == "Summarize gate failure")

    assert run_step["id"] == "run_gates"
    assert failure_step["if"] == "failure() && steps.run_gates.outcome == 'failure'"
    assert "GITHUB_STEP_SUMMARY" in failure_step["run"]
    assert "Failure reason:" in failure_step["run"]
    assert "Next action:" in failure_step["run"]


def test_composite_action_fails_closed_with_actionable_sarif_upload_summary() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    steps = action["runs"]["steps"]
    upload_step = next(step for step in steps if step["name"] == "Upload SARIF report")
    failure_step = next(step for step in steps if step["name"] == "Summarize SARIF upload failure")

    assert upload_step["id"] == "upload_sarif"
    assert failure_step["if"] == "failure() && steps.upload_sarif.outcome == 'failure'"
    assert "SARIF" in failure_step["run"]
    assert "Next action:" in failure_step["run"]


def test_new_surfaces_do_not_claim_they_exist_in_v4_11_0() -> None:
    """v4.11.0 predates both integration files; examples must not point at it."""
    readme = README_PATH.read_text(encoding="utf-8")
    hooks = HOOKS_PATH.read_text(encoding="utf-8")
    assert ".github/actions/hyodo@v4.11.0" not in readme
    assert "rev: v4.11.0" not in hooks


# --- SARIF report surface -----------------------------------------------------


def test_sarif_report_has_required_top_level_keys(tmp_path: Path) -> None:
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    sarif_path = tmp_path / summary["result_path"]
    assert sarif_path.name == "hyodo-report.sarif"
    log = json.loads(sarif_path.read_text(encoding="utf-8"))

    assert log["version"] == "2.1.0"
    assert log["$schema"] == SARIF_SCHEMA_URI
    assert log["runs"]
    assert log["runs"][0]["tool"]["driver"]["name"] == "HyoDo"


def test_sarif_report_is_schema_valid(tmp_path: Path) -> None:
    jsonschema = __import__("jsonschema")
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    sarif_path = tmp_path / summary["result_path"]
    log = json.loads(sarif_path.read_text(encoding="utf-8"))
    schema = json.loads(SARIF_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(schema).validate(log)


def test_sarif_report_records_deny_as_error(tmp_path: Path) -> None:
    _write_deny_evidence(tmp_path)
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    log = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    results = log["runs"][0]["results"]
    assert any(item["level"] == "error" for item in results)
    assert any(item["ruleId"] == "HYODO-POLICY-DENY" for item in results)


def test_sarif_report_records_unreadable_ledger_as_error(tmp_path: Path) -> None:
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "agent-events.jsonl").write_bytes(b"\xff\xfe\x00")
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    log = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    results = log["runs"][0]["results"]
    assert any(item["level"] == "error" for item in results)
    assert any(item["ruleId"] == "HYODO-LEDGER-UNREADABLE" for item in results)


# --- GitHub composite action --------------------------------------------------


def test_composite_action_exists_and_has_required_shape() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    assert action["name"] == "HyoDo"
    assert action["runs"]["using"] == "composite"
    steps = action["runs"]["steps"]
    assert any("pip install" in step.get("run", "") for step in steps)
    assert any("hyodo check" in step.get("run", "") for step in steps)


def test_composite_action_install_ref_is_not_a_branch() -> None:
    """Install examples must use a release tag or immutable commit, never main."""
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    install_step = next(step for step in action["runs"]["steps"] if "pip install" in step.get("run", ""))
    command = install_step["run"]
    assert "@main" not in command
    match = re.search(r"@([^#\s]+)", command)
    assert match is not None
    ref = match.group(1)
    assert re.fullmatch(r"v\d+\.\d+\.\d+|[0-9a-f]{40}", ref)
