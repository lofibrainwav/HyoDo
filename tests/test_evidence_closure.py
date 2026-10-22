"""Regression coverage for bounded input identity and receipt persistence."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app, collect_dashboard_evidence
from hyodo.gates import GATES_TRUST_ENV_VAR


def _gates(root: Path, command: str = "true") -> None:
    config = root / ".hyodo" / "gates.toml"
    config.parent.mkdir(exist_ok=True)
    config.write_text(
        'schema = "hyodo.gates/v1"\n[gates.smoke]\npillar = "truth"\n'
        f"command = {json.dumps(command)}\n",
        encoding="utf-8",
    )


@pytest.fixture
def dirty_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text(".hyodo/\n", encoding="utf-8")
    (tmp_path / "input.txt").write_text("committed", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    (tmp_path / "input.txt").write_text("dirty before", encoding="utf-8")
    return tmp_path


def test_dirty_to_dirty_content_change_is_unobserved(dirty_repo: Path) -> None:
    _gates(dirty_repo, "sh -c 'printf after > input.txt'")
    result = CliRunner().invoke(app, ["check", str(dirty_repo), "--json"])
    payload = json.loads(result.output)
    assert (dirty_repo / "input.txt").read_text() == "after"
    assert payload["provenance"]["target_dirty"] is True
    assert payload["provenance_post"]["target_dirty"] is True
    assert payload["status"] == "UNOBSERVED"
    assert result.exit_code == 2
    assert payload["target_changed_during_run"] is True
    assert "gates" not in payload


def test_unchanged_dirty_input_still_has_gate_results(dirty_repo: Path) -> None:
    _gates(dirty_repo)
    result = CliRunner().invoke(app, ["check", str(dirty_repo), "--json"])
    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload["status"] == "PASS"
    assert payload["gates"]["smoke"]["status"] == "PASS"
    assert "target_changed_during_run" not in payload


@pytest.mark.parametrize("persisted", [False, True])
def test_history_persistence_is_separate_from_gate_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, persisted: bool
) -> None:
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")
    _gates(tmp_path)
    monkeypatch.setattr("hyodo.cli.main.append_history_receipt", lambda *a, **k: persisted)
    evidence = collect_dashboard_evidence(tmp_path)
    assert evidence["gates"]["smoke"]["status"] == "PASS"
    assert evidence["history_receipt"]["persistence"] == ("OBSERVED" if persisted else "UNOBSERVED")


@pytest.mark.parametrize("missing", [0, 1])
def test_unreadable_git_snapshot_withholds_success_and_rows(
    dirty_repo: Path, monkeypatch: pytest.MonkeyPatch, missing: int
) -> None:
    _gates(dirty_repo)
    values = ["a" * 64, "a" * 64]
    values[missing] = None
    calls = iter(values)
    monkeypatch.setattr("hyodo.cli.main.git_input_digest", lambda root: next(calls))
    result = CliRunner().invoke(app, ["check", str(dirty_repo), "--json"])
    payload = json.loads(result.output)
    assert result.exit_code == 2
    assert payload["exit_code"] == 2
    assert payload["status"] == "UNOBSERVED"
    assert payload["input_snapshot"]["state"] == "UNOBSERVED"
    assert "gates" not in payload


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_BYTES"])
def test_content_snapshot_bounds_are_unobserved(
    dirty_repo: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    from hyodo import input_snapshot

    _gates(dirty_repo)
    monkeypatch.setattr(input_snapshot, limit, 0)
    assert input_snapshot.git_input_digest(dirty_repo) is None


def test_gitignore_rule_change_is_part_of_content_identity(dirty_repo: Path) -> None:
    from hyodo.input_snapshot import git_input_digest

    _gates(dirty_repo)
    before = git_input_digest(dirty_repo)
    (dirty_repo / ".gitignore").write_text(".hyodo/\noutput.txt\n", encoding="utf-8")
    assert before is not None
    assert git_input_digest(dirty_repo) != before


def test_tracked_history_append_does_not_invalidate_inputs(dirty_repo: Path) -> None:
    from hyodo.input_snapshot import git_input_digest

    _gates(dirty_repo)
    history = dirty_repo / ".hyodo" / "history.jsonl"
    history.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(dirty_repo), "add", "-f", str(history)], check=True)
    before = git_input_digest(dirty_repo)
    history.write_text("{}\n{}\n", encoding="utf-8")
    assert before is not None
    assert git_input_digest(dirty_repo) == before


def test_non_git_byog_keeps_existing_gate_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")
    _gates(tmp_path)
    result = CliRunner().invoke(app, ["check", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert result.exit_code == 0
    assert payload["status"] == "PASS"
    assert "input_snapshot" not in payload
