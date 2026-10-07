"""Evidence linkage: check/dashboard/history must preserve code identity.

Each surface creates part of the story (provenance, per-gate rows, trust)
and used to drop it at the next boundary: check JSON had no gate rows or
timestamp and described cwd instead of the target; dashboard evidence
discarded the trust decision; history receipts dropped provenance and
pillars. A mid-check tree change was invisible everywhere.

These tests pin the additive restoration. Past receipts are never rewritten.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
from datetime import datetime
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app, collect_dashboard_evidence
from hyodo.gates import GATES_CONFIG_RELATIVE_PATH, GATES_TRUST_ENV_VAR
from hyodo.pillars import (
    HISTORY_RELATIVE_PATH,
    RECEIPT_SCHEMA_VERSION,
    append_history_receipt,
)
from hyodo.provenance import resolve_provenance

runner = CliRunner()


def _write_gates(root: Path, body: str) -> None:
    config = root / GATES_CONFIG_RELATIVE_PATH
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('schema = "hyodo.gates/v1"\n' + body, encoding="utf-8")


@pytest.fixture
def trusted(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True)
    (tmp_path / "f.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "commit", "-qm", "init"], check=True)
    return tmp_path


def _head(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_check_json_carries_gate_rows_and_measured_at(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, '\n[gates.smoke]\npillar = "truth"\ncommand = "true"\n')
    result = runner.invoke(app, ["check", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["status"] == "PASS"
    assert payload["gates"] == {"smoke": {"status": "PASS", "pillar": "truth", "message": "ok"}}
    # A timestamp consumers can order and expire on.
    datetime.fromisoformat(payload["measured_at"])


def test_check_provenance_describes_target_not_cwd(
    tmp_path: Path, trusted: None, git_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_gates(git_repo, '\n[gates.smoke]\npillar = "truth"\ncommand = "true"\n')
    elsewhere = tmp_path / "elsewhere-not-a-repo"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    result = runner.invoke(app, ["check", str(git_repo), "--json"])
    payload = json.loads(result.output)
    assert payload["provenance"]["target_commit"] == _head(git_repo)


def test_midcheck_move_downgrades_and_withholds_rows(
    tmp_path: Path, trusted: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_gates(tmp_path, '\n[gates.smoke]\npillar = "truth"\ncommand = "true"\n')
    real_resolve = resolve_provenance
    pre = real_resolve(tmp_path)
    post = dataclasses.replace(pre, target_dirty=True)
    calls = {"n": 0}

    def _staged(target_root, **kwargs):
        # check() resolves: early cwd, then target, then post-gate target.
        calls["n"] += 1
        if calls["n"] <= 2:
            return pre
        return post

    monkeypatch.setattr("hyodo.cli.main.resolve_provenance", _staged)
    result = runner.invoke(app, ["check", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert calls["n"] == 3
    assert payload["status"] == "UNOBSERVED"
    assert payload["target_changed_during_run"] is True
    assert "gates" not in payload
    assert payload["provenance_post"]["target_dirty"] is True


def test_history_receipt_preserves_provenance_and_pillars(tmp_path: Path) -> None:
    evidence = {
        "measured_at": "2026-10-06T23:10:00+00:00",
        "provenance": {"target_commit": "a" * 40, "target_dirty": False},
        "gates": {
            "smoke": {"status": "PASS", "pillar": "truth", "message": "ok"},
        },
    }
    assert append_history_receipt(tmp_path, evidence) is True
    row = json.loads((tmp_path / HISTORY_RELATIVE_PATH).read_text().splitlines()[-1])
    assert row["schema_version"] == RECEIPT_SCHEMA_VERSION == "hyodo.history-receipt/v2"
    assert row["provenance"]["target_commit"] == "a" * 40
    assert row["pillars"] == {"smoke": "truth"}


def test_dashboard_evidence_preserves_trust(tmp_path: Path, trusted: None) -> None:
    _write_gates(tmp_path, '\n[gates.smoke]\npillar = "truth"\ncommand = "true"\n')
    evidence = collect_dashboard_evidence(tmp_path)
    assert isinstance(evidence["trust"]["fingerprint"], str)
    assert len(evidence["trust"]["fingerprint"]) == 64
