"""Tests for BYOG gate-run progress lines (`hyodo.gates.GateProgress`).

A long gate used to leave the terminal silent between the trust prompt and the
first result, which reads as a freeze. Progress lines go to stderr only, never
change a result, and are off when stderr is not a terminal or --quiet is set.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import _gate_progress_for, app
from hyodo.gates import (
    GATES_TRUST_ENV_VAR,
    SCHEMA_ID,
    GateProgress,
    GatesConfig,
    UserGate,
    UserGateResult,
    run_user_gates_with_trust,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def _preapprove(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(GATES_TRUST_ENV_VAR, "1")


def _config(*gates: UserGate) -> GatesConfig:
    return GatesConfig(schema=SCHEMA_ID, gates=gates)


def test_progress_reports_run_start_each_gate_and_each_result(tmp_path: Path) -> None:
    stream = io.StringIO()
    config = _config(
        UserGate(name="ok", pillar="truth", command=("true",), timeout=5),
        UserGate(name="bad", pillar="beauty", command=("false",), timeout=5),
    )

    _, results = run_user_gates_with_trust(
        config, tmp_path, progress=GateProgress(stream, heartbeat_seconds=0)
    )

    lines = stream.getvalue().splitlines()
    assert lines[0].startswith("HyoDo: command set trusted (")
    assert lines[0].endswith("-- running 2 gates")
    assert lines[1] == "[1/2] ok (truth) ..."
    assert lines[2].startswith("[1/2] ok: PASS (")
    assert lines[3] == "[2/2] bad (beauty) ..."
    assert lines[4].startswith("[2/2] bad: FAIL (")
    assert [r.status for r in results] == ["PASS", "FAIL"]


def test_progress_does_not_change_results(tmp_path: Path) -> None:
    config = _config(
        UserGate(name="ok", pillar="truth", command=("true",), timeout=5),
        UserGate(name="bad", pillar="beauty", command=("false",), timeout=5),
        UserGate(name="gone", pillar="goodness", command=("hyodo-no-such-bin",), timeout=5),
    )

    _, plain = run_user_gates_with_trust(config, tmp_path)
    _, observed = run_user_gates_with_trust(
        config, tmp_path, progress=GateProgress(io.StringIO(), heartbeat_seconds=0)
    )

    assert observed == plain


def test_heartbeat_reports_elapsed_while_a_gate_runs(tmp_path: Path) -> None:
    stream = io.StringIO()
    config = _config(UserGate(name="slow", pillar="truth", command=("sleep", "0.5"), timeout=5))

    run_user_gates_with_trust(
        config, tmp_path, progress=GateProgress(stream, heartbeat_seconds=0.1)
    )

    heartbeats = [line for line in stream.getvalue().splitlines() if "still running" in line]
    assert heartbeats, stream.getvalue()
    assert heartbeats[0].startswith("[1/1] slow still running (")
    # The heartbeat thread is joined before the result line, so nothing
    # follows the final result.
    assert stream.getvalue().splitlines()[-1].startswith("[1/1] slow: PASS (")


def test_heartbeat_formats_minutes() -> None:
    stream = io.StringIO()
    ticks = iter([0.0, 272.0])
    progress = GateProgress(stream, heartbeat_seconds=0, clock=lambda: next(ticks))
    gate = UserGate(name="unit-tests", pillar="truth", command=("true",), timeout=5)

    progress.gate_started(1, 8, gate)
    progress.gate_stopped()
    progress.gate_finished(1, 8, UserGateResult("unit-tests", "truth", "PASS", "ok"))

    assert stream.getvalue().splitlines()[-1] == "[1/8] unit-tests: PASS (4m32s)"


def test_progress_neutralizes_terminal_controls_in_gate_names(tmp_path: Path) -> None:
    stream = io.StringIO()
    config = _config(UserGate(name="x\x1b[2Ky\nz", pillar="truth", command=("true",), timeout=5))

    run_user_gates_with_trust(config, tmp_path, progress=GateProgress(stream, heartbeat_seconds=0))

    assert "\x1b" not in stream.getvalue()
    assert all(line.startswith(("HyoDo:", "[1/1]")) for line in stream.getvalue().splitlines())


def test_unapproved_set_prints_no_progress(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(GATES_TRUST_ENV_VAR)
    monkeypatch.setenv("CI", "1")
    stream = io.StringIO()
    config = _config(UserGate(name="fresh", pillar="truth", command=("true",), timeout=5))

    trust, results = run_user_gates_with_trust(
        config, tmp_path / "unapproved", progress=GateProgress(stream, heartbeat_seconds=0)
    )

    assert not trust.approved
    assert [r.status for r in results] == ["SKIP"]
    assert stream.getvalue() == ""


def test_broken_progress_stream_does_not_fail_the_run(tmp_path: Path) -> None:
    stream = io.StringIO()
    stream.close()
    config = _config(UserGate(name="ok", pillar="truth", command=("true",), timeout=5))

    _, results = run_user_gates_with_trust(
        config, tmp_path, progress=GateProgress(stream, heartbeat_seconds=0)
    )

    assert [r.status for r in results] == ["PASS"]


def test_cli_progress_is_off_when_quiet_or_stderr_is_not_a_terminal() -> None:
    assert _gate_progress_for(quiet=True) is None
    with patch("sys.stderr.isatty", return_value=False):
        assert _gate_progress_for(quiet=False) is None
    with patch("sys.stderr.isatty", return_value=True):
        assert isinstance(_gate_progress_for(quiet=False), GateProgress)
        assert _gate_progress_for(quiet=True) is None


def test_cli_json_stdout_is_unchanged_by_progress(tmp_path: Path) -> None:
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "gates.toml").write_text(
        'schema = "hyodo.gates/v1"\n\n[gates.ok]\npillar = "truth"\ncommand = "true"\n',
        encoding="utf-8",
    )
    stderr = io.StringIO()

    with patch(
        "hyodo.cli.main._gate_progress_for",
        return_value=GateProgress(stderr, heartbeat_seconds=0),
    ):
        result = runner.invoke(app, ["check", str(tmp_path), "--json"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert "[1/1] ok (truth) ..." in stderr.getvalue()
    assert "[1/1]" not in result.stdout
