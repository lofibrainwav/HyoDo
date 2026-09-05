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
    # it, every consumer's pre-commit run would fail at environment setup.
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'hyodo = "hyodo.cli.main:app"' in pyproject


def test_pre_commit_hook_declares_non_blocking_metadata() -> None:
    hooks = yaml.safe_load(HOOKS_PATH.read_text(encoding="utf-8"))
    hook = next(h for h in hooks if h["id"] == "hyodo-check")
    assert hook["language"] == "python"
    # pass_filenames: false — gates run over the project, not the changed files.
    assert hook["pass_filenames"] is False
    assert hook["name"]


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
    assert isinstance(log["runs"], list)
    assert len(log["runs"]) == 1
    run = log["runs"][0]
    assert run["tool"]["driver"]["name"] == "HyoDo"
    assert run["tool"]["driver"]["version"] == hyodo.__version__
    assert isinstance(run["results"], list)


def test_sarif_report_surfaces_deny_as_error_results(tmp_path: Path) -> None:
    _write_deny_evidence(tmp_path)
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    log = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    results = log["runs"][0]["results"]

    deny_results = [r for r in results if r["ruleId"] == "hyodo/policy-deny"]
    assert len(deny_results) == 1
    assert deny_results[0]["level"] == "error"
    rule_ids = {rule["id"] for rule in log["runs"][0]["tool"]["driver"]["rules"]}
    assert {"hyodo/policy-deny", "hyodo/ledger-unreadable"} <= rule_ids


def test_sarif_report_validates_against_official_sarif_2_1_0_schema(
    tmp_path: Path,
) -> None:
    """Full validation against the OASIS SARIF schema (checked in as a fixture)."""
    import jsonschema

    schema = json.loads(SARIF_SCHEMA_PATH.read_text(encoding="utf-8"))
    _write_deny_evidence(tmp_path)
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    log = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    jsonschema.validate(instance=log, schema=schema)

    # An empty-evidence SARIF log is schema-valid. It is a visibility artifact,
    # not a replacement for the fail-closed `hyodo check` command.
    empty = runner.invoke(
        app, ["report", "--root", str(tmp_path / "empty"), "--format", "sarif", "--json"]
    )
    assert empty.exit_code == 0
    empty_summary = json.loads(empty.output)
    empty_log = json.loads(
        (tmp_path / "empty" / empty_summary["result_path"]).read_text(encoding="utf-8")
    )
    jsonschema.validate(instance=empty_log, schema=schema)
    assert empty_log["runs"][0]["results"] == []


def test_sarif_report_never_turns_unreadable_ledger_into_clean_run(tmp_path: Path) -> None:
    (tmp_path / ".hyodo").mkdir()
    # A directory where a file is expected makes the ledger unreadable — HyoDo
    # must surface this as an error result, not a zero-event clean run.
    (tmp_path / ".hyodo" / "agent-events.jsonl").mkdir()
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "sarif", "--json"])
    assert result.exit_code == 0
    summary = json.loads(result.output)
    log = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    results = log["runs"][0]["results"]
    assert any(r["ruleId"] == "hyodo/ledger-unreadable" for r in results)


# --- Composite GitHub Action surface ------------------------------------------


def test_composite_action_parses_and_is_composite() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    assert action["runs"]["using"] == "composite"
    assert action["name"]
    assert action["description"]


def test_composite_action_installs_hyodo_from_same_pinned_ref() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    steps = action["runs"]["steps"]
    install_steps = [step for step in steps if "pip install" in str(step.get("run", ""))]
    assert install_steps, "action must install HyoDo"
    run_block = install_steps[0]["run"]
    assert "github.action_path" in run_block
    assert "../../.." in run_block
    assert "hyodo==" not in run_block
    assert "version" not in action.get("inputs", {})


def test_composite_action_runs_hyodo_check() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    run_blocks = [str(step.get("run", "")) for step in action["runs"]["steps"]]
    assert any("hyodo check" in block for block in run_blocks)


def test_composite_action_external_actions_are_sha_pinned() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    uses = [str(step["uses"]) for step in action["runs"]["steps"] if "uses" in step]
    assert uses
    for ref in uses:
        assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref), f"external action is not SHA-pinned: {ref}"


def test_composite_action_sarif_upload_is_opt_in() -> None:
    action = yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))
    assert action["inputs"]["upload-sarif"]["default"] == "false"
    sarif_steps = [
        step
        for step in action["runs"]["steps"]
        if "SARIF" in str(step.get("name", "")) or "upload-sarif" in str(step.get("uses", ""))
    ]
    assert len(sarif_steps) == 2
    for step in sarif_steps:
        assert "upload-sarif" in str(step.get("if", ""))
