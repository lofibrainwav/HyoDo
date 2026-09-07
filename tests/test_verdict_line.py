"""Presentation contracts must preserve command outcomes."""

import importlib
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.verdict import render_verdict_line

cli = importlib.import_module("hyodo.cli.main")
runner = CliRunner()


def test_render_verdict_line():
    assert render_verdict_line("PASS", 4, 4, "gates", "all executed gates passed") == (
        "HYODO PASS — 4/4 gates observed, all executed gates passed"
    )


@pytest.mark.parametrize(("status", "code"), [("PASS", 0), ("FAIL", 1), ("SKIP", 2)])
def test_checkout_modes_preserve_exit(monkeypatch, tmp_path, status, code):
    monkeypatch.setattr(cli, "find_repo_root", lambda target: tmp_path)
    for name in ("run_pyright_check", "run_ruff_check", "run_pytest_check", "run_sbom_check"):
        monkeypatch.setattr(cli, name, lambda *args: cli.GateResult(cli.GateStatus(status), "test"))
    assert_modes(["check", str(tmp_path)], code)


def assert_modes(args, code):
    baseline = runner.invoke(cli.app, args)
    assert baseline.exit_code == code, baseline.output
    assert baseline.output.splitlines()[-1].startswith("HYODO ")
    for flags in (["--quiet"], ["--explain"], ["--quiet", "--explain"]):
        first = runner.invoke(cli.app, args + flags)
        second = runner.invoke(cli.app, args + flags)
        assert first.exit_code == baseline.exit_code
        assert first.output == second.output
        assert (
            first.output.splitlines()[-2 if "--explain" in flags else -1]
            == baseline.output.splitlines()[-1]
        )
        if "--quiet" in flags:
            assert len(first.output.splitlines()) == (2 if "--explain" in flags else 1)
        for forbidden in ("probability", "confidence"):
            assert forbidden not in first.output.lower()
    machine = runner.invoke(cli.app, [*args, "--json"])
    payload = json.loads(machine.output)
    assert machine.exit_code == payload["exit_code"] == code
    assert payload["verdict"] == baseline.output.splitlines()[-1]


@pytest.mark.parametrize(("strict", "code"), [(False, 0), (True, 1)])
def test_safe_advisory_and_strict(tmp_path, strict, code):
    target = tmp_path / "danger.py"
    target.write_text('import os\nos.system("rm -rf /")\n')
    args = ["safe", str(target)] + (["--strict"] if strict else [])
    assert_modes(args, code)
    if not strict:
        assert "advisory; --strict blocks" in runner.invoke(cli.app, args).output.splitlines()[-1]


def test_unobserved_inputs(tmp_path):
    assert_modes(["check", str(tmp_path / "missing")], 2)
    assert_modes(["safe", str(tmp_path / "missing")], 2)
    assert_modes(["policy", "check", "--file", str(tmp_path / "missing")], 2)


def test_policy_sample(tmp_path):
    root = Path(__file__).resolve().parents[1]
    args = [
        "policy",
        "check",
        "--file",
        str(root / "examples/fde-evidence-spine/sample-tool-call.json"),
        "--config",
        str(root / "examples/fde-evidence-spine/policy.toml"),
        "--root",
        str(tmp_path),
    ]
    baseline = runner.invoke(cli.app, args)
    assert_modes(args, baseline.exit_code)
    assert "trust=" in baseline.output.splitlines()[-1]
    assert "surfaces observed" in baseline.output.splitlines()[-1]


@pytest.mark.parametrize(
    ("decision", "code"), [("ALLOW", 0), ("DENY", 1), ("ASK", 3), ("UNOBSERVED", 2)]
)
def test_policy_decision_modes(monkeypatch, tmp_path, decision, code):
    from hyodo.policy import PolicyDecision

    monkeypatch.setattr(
        cli,
        "evaluate_policy",
        lambda *args, **kwargs: PolicyDecision(
            decision, None, "measured policy result", coverage=(3, 4), trust_level=1
        ),
    )
    root = Path(__file__).resolve().parents[1]
    args = [
        "policy",
        "check",
        "--file",
        str(root / "examples/fde-evidence-spine/sample-tool-call.json"),
        "--config",
        str(root / "examples/fde-evidence-spine/policy.toml"),
        "--root",
        str(tmp_path),
    ]
    assert_modes(args, code)
    assert (
        f"HYODO {decision} — 3/4 surfaces observed, trust=1" in runner.invoke(cli.app, args).output
    )


def test_event_record_policy_first_line(tmp_path):
    root = Path(__file__).resolve().parents[1]
    args = [
        "event",
        "record",
        "--file",
        str(root / "examples/fde-evidence-spine/sample-tool-call.json"),
        "--policy",
        str(root / "examples/fde-evidence-spine/policy.toml"),
        "--root",
        str(tmp_path),
    ]
    result = runner.invoke(cli.app, args)
    assert result.output.startswith("HYODO "), result.output
    assert "surfaces observed, trust=" in result.output.splitlines()[0]
    for word in ("probability", "confidence"):
        assert word not in result.output.lower()


@pytest.mark.parametrize(("status", "code"), [("PASS", 0), ("FAIL", 1), ("SKIP", 2)])
def test_general_modes(monkeypatch, tmp_path, status, code):
    monkeypatch.setattr(
        cli,
        "_run_general_gates",
        lambda *args: [cli.GeneralGateResult("Python", "compile", cli.GateStatus(status), "test")],
    )
    assert_modes(["check", str(tmp_path), "--general"], code)


@pytest.mark.parametrize(("status", "code"), [("PASS", 0), ("FAIL", 1), ("SKIP", 2)])
def test_user_gate_modes(monkeypatch, tmp_path, status, code):
    from hyodo.gates import UserGateResult

    monkeypatch.setattr(cli, "load_gates_config", lambda *args: object())
    monkeypatch.setattr(
        cli,
        "run_user_gates",
        lambda *args, **kwargs: [
            UserGateResult(name="custom", pillar="truth", status=status, message="test")
        ],
    )
    assert_modes(["check", str(tmp_path)], code)


def test_default_check_streams_before_gate_finishes(monkeypatch, tmp_path):
    import io

    from rich.console import Console

    output = io.StringIO()
    monkeypatch.setattr(cli, "console", Console(file=output, color_system=None))
    monkeypatch.setattr(cli, "find_repo_root", lambda target: tmp_path)

    def gate(*args):
        assert "Type checking" in output.getvalue()
        return cli.GateResult(cli.GateStatus.PASS, "test")

    monkeypatch.setattr(cli, "run_pyright_check", gate)
    for name in ("run_ruff_check", "run_pytest_check", "run_sbom_check"):
        monkeypatch.setattr(cli, name, lambda *args: cli.GateResult(cli.GateStatus.PASS, "test"))
    result = runner.invoke(cli.app, ["check", str(tmp_path)])
    assert result.exit_code == 0, result.exception
