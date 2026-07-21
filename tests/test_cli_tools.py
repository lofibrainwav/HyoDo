"""Unit tests for CLI tool invocation helpers and check truth contract."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import (
    GateResult,
    GateStatus,
    _missing_tool_result,
    _tool_cmd,
    app,
    collect_dashboard_evidence,
    find_repo_root,
    resolve_check_target,
    run_pyright_check,
    run_pytest_check,
    run_ruff_check,
)

runner = CliRunner()


def test_tool_cmd_uses_current_interpreter():
    cmd = _tool_cmd("pytest", "tests", "-q")
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "pytest"]
    assert cmd[3:] == ["tests", "-q"]


def test_dashboard_evidence_is_versioned_and_preserves_raw_gate_statuses(tmp_path):
    ok = GateResult(GateStatus.PASS, "ok")
    safety = {
        "risk_score": 5,
        "findings": [],
    }
    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=ok),
        patch("hyodo.cli.main.run_safety_scan", return_value=safety),
    ):
        evidence = collect_dashboard_evidence(tmp_path)
    assert evidence["schema_version"] == "hyodo.dashboard-evidence/v1"
    assert evidence["gates"]["typecheck"]["status"] == "PASS"
    assert evidence["safety"]["risk_score"] == 5


def test_run_pytest_check_uses_python_m_pytest(tmp_path):
    root = tmp_path
    (root / "tests").mkdir()
    mock_result = MagicMock(returncode=0, stdout="5 passed in 0.01s\n", stderr="")
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", return_value=mock_result) as run,
    ):
        result = run_pytest_check(root, verbose=False)
    assert result.status is GateStatus.PASS
    assert "passed" in result.message.lower()
    cmd = run.call_args.args[0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "pytest"]


def test_run_pyright_check_uses_host_interpreter_for_import_resolution(tmp_path):
    """Pyright must resolve dependencies from the interpreter running HyoDo."""
    ok = MagicMock(returncode=0, stdout="0 errors, 0 warnings\n", stderr="")
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", return_value=ok) as run,
    ):
        result = run_pyright_check(tmp_path, verbose=False)

    assert result.status is GateStatus.PASS
    cmd = run.call_args.args[0]
    assert cmd[:3] == [sys.executable, "-m", "pyright"]
    assert cmd[3:5] == ["--pythonpath", sys.executable]
    assert cmd[5:] == ["hyodo"]


def test_missing_tool_soft_skip_without_root():
    result = _missing_tool_result("ruff", root=None)
    assert result.status is GateStatus.SKIP
    assert "skipped" in result.message


def test_missing_tool_fails_in_repo_mode(tmp_path):
    result = _missing_tool_result("ruff", root=tmp_path)
    assert result.status is GateStatus.FAIL
    assert "not found" in result.message


def test_ruff_unsupported_outside_hyodo_checkout():
    result = run_ruff_check(root=None)
    assert result.status is GateStatus.UNSUPPORTED
    assert "not executed" in result.message


def test_ruff_runs_lint_and_format_check(tmp_path):
    """Gate 2 must invoke both ruff check and ruff format --check."""
    ok = MagicMock(returncode=0, stdout="All checks passed!\n", stderr="")
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", return_value=ok) as run,
    ):
        result = run_ruff_check(tmp_path, fix=False, verbose=False)
    assert result.status is GateStatus.PASS
    assert "format" in result.message.lower() or "lint" in result.message.lower()
    assert run.call_count == 2
    cmds = [c.args[0] for c in run.call_args_list]
    assert any(cmd[1:4] == ["-m", "ruff", "check"] for cmd in cmds)
    assert any(cmd[1:4] == ["-m", "ruff", "format"] and "--check" in cmd for cmd in cmds)


def test_ruff_format_failure_fails_gate(tmp_path):
    """Lint pass + format fail must not green the ruff gate."""
    lint_ok = MagicMock(returncode=0, stdout="All checks passed!\n", stderr="")
    fmt_fail = MagicMock(returncode=1, stdout="Would reformat: hyodo/cli/main.py\n", stderr="")

    def side_effect(cmd, **_kwargs):
        if "format" in cmd:
            return fmt_fail
        return lint_ok

    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=side_effect),
    ):
        result = run_ruff_check(tmp_path, fix=False, verbose=False)
    assert result.status is GateStatus.FAIL
    assert "format" in result.message.lower()


def test_resolve_check_target_missing(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(FileNotFoundError):
        resolve_check_target(str(missing))


def test_find_repo_root_from_nested_path():
    # Real HyoDo checkout
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None
    assert (root / "hyodo").is_dir()
    assert (root / "pyproject.toml").is_file()


def test_check_missing_path_exit_2():
    result = runner.invoke(app, ["check", "/tmp/hyodo-definitely-missing-path-xyz"])
    assert result.exit_code == 2
    assert "not a validation pass" in result.output.lower() or "Path not found" in result.output


def test_check_empty_dir_not_false_green(tmp_path):
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 2
    assert "No project gates were executed" in result.output
    assert "All gates passed" not in result.output
    assert "All executed gates passed" not in result.output


def test_check_generic_python_project_not_false_green(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname="x"\nversion="0"\n', encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_x.py").write_text(
        "def test_x():\n    assert True\n", encoding="utf-8"
    )
    result = runner.invoke(app, ["check", str(tmp_path)])
    assert result.exit_code == 2
    assert "No project gates were executed" in result.output
    assert "All gates passed" not in result.output


def test_check_path_targets_hyodo_checkout_from_other_cwd(tmp_path):
    """hyodo check /path/to/HyoDo must resolve that checkout (gates mocked — no nested pytest)."""
    hyodo_root = find_repo_root(Path(__file__).resolve())
    assert hyodo_root is not None
    from hyodo.cli.main import GateResult

    ok = GateResult(GateStatus.PASS, "ok")
    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok) as p,
        patch("hyodo.cli.main.run_ruff_check", return_value=ok) as r,
        patch("hyodo.cli.main.run_pytest_check", return_value=ok) as t,
        patch("hyodo.cli.main.run_sbom_check", return_value=GateResult(GateStatus.SKIP, "no sbom")),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root)])
    assert result.exit_code == 0
    assert "HyoDo checkout:" in result.output
    # Rich may wrap long absolute paths across lines; strip newlines before match.
    assert str(hyodo_root) in result.output.replace("\n", "")
    assert "All executed gates passed" in result.output
    assert "All gates passed" not in result.output
    # Gates must receive the resolved HyoDo root, not an empty/foreign cwd.
    assert p.call_args.args[0] == hyodo_root
    assert r.call_args.args[0] == hyodo_root
    assert t.call_args.args[0] == hyodo_root


def test_check_zero_executed_gates_never_exit_0():
    with (
        patch("hyodo.cli.main.run_pyright_check") as p,
        patch("hyodo.cli.main.run_ruff_check") as r,
        patch("hyodo.cli.main.run_pytest_check") as t,
        patch("hyodo.cli.main.run_sbom_check") as s,
        patch("hyodo.cli.main.find_repo_root", return_value=Path("/tmp/fake-hyodo")),
    ):
        from hyodo.cli.main import GateResult

        skip = GateResult(GateStatus.SKIP, "skipped")
        p.return_value = skip
        r.return_value = skip
        t.return_value = skip
        s.return_value = skip
        result = runner.invoke(app, ["check", "."])
    assert result.exit_code == 2
    assert "No project gates were executed" in result.output


def test_safe_default_high_finding_exit_0(tmp_path):
    sample = tmp_path / "tok.txt"
    sample.write_text("token = ghp_abcdefghijklmnopqrstuvwxyz012345\n", encoding="utf-8")
    result = runner.invoke(app, ["safe", str(sample)])
    assert result.exit_code == 0
    assert "secret" in result.output.lower() or "high" in result.output.lower()


def test_safe_strict_high_finding_exit_1(tmp_path):
    sample = tmp_path / "tok.txt"
    sample.write_text("token = ghp_abcdefghijklmnopqrstuvwxyz012345\n", encoding="utf-8")
    result = runner.invoke(app, ["safe", "--strict", str(sample)])
    assert result.exit_code == 1


def test_safe_strict_dangerous_command_exit_1(tmp_path):
    sample = tmp_path / "danger.txt"
    sample.write_text("please DROP DATABASE production;\n", encoding="utf-8")
    result = runner.invoke(app, ["safe", "--strict", str(sample)])
    assert result.exit_code == 1


def test_safe_strict_bare_rm_rf_root_exit_1(tmp_path):
    """Regression: bare `rm -rf /` (root) must be a high-severity strict blocker.

    Previously the rm_rf_root regex missed a root target at end of line, so this
    catastrophic command scanned clean. It must now exit 1 under --strict.
    """
    sample = tmp_path / "danger.txt"
    sample.write_text("sudo rm -rf /\n", encoding="utf-8")
    result = runner.invoke(app, ["safe", "--strict", str(sample)])
    assert result.exit_code == 1


def test_safe_strict_medium_only_exit_0(tmp_path):
    sample = tmp_path / "prod.txt"
    sample.write_text("kubectl apply -f deploy.yaml\n", encoding="utf-8")
    result = runner.invoke(app, ["safe", "--strict", str(sample)])
    assert result.exit_code == 0
    assert (
        "production" in result.output.lower()
        or "caution" in result.output.lower()
        or "high" in result.output.lower()
        or "medium" in result.output.lower()
        or "Risk" in result.output
    )


def test_safe_strict_clean_exit_0(tmp_path):
    sample = tmp_path / "clean.txt"
    sample.write_text("hello world plain notes\n", encoding="utf-8")
    result = runner.invoke(app, ["safe", "--strict", str(sample)])
    assert result.exit_code == 0


def test_safe_missing_path_exit_2():
    result = runner.invoke(app, ["safe", "/tmp/hyodo-safe-missing-path-xyz"])
    assert result.exit_code == 2


def test_safe_unreadable_file_exit_2(tmp_path):
    """Read/permission failure must exit 2 (scan failure), not silent exit 0."""
    sample = tmp_path / "unreadable.txt"
    sample.write_text("plain notes\n", encoding="utf-8")
    scan_result = {
        "source": f"error:read:{sample}",
        "findings": [],
        "rows": [
            ("Secrets exposure", "✅", "green"),
            ("Dangerous commands", "✅", "green"),
            ("Production impact", "✅", "green"),
            ("Rollback signal", "✅", "green"),
        ],
        "risk_score": 0,
        "level": "low",
        "action": "Low early-warning risk — final approval remains human",
    }
    with patch("hyodo.cli.main.run_safety_scan", return_value=scan_result):
        result = runner.invoke(app, ["safe", str(sample)])
    assert result.exit_code == 2
    assert "not a validation pass" in result.output.lower()
    assert "Scan failed" in result.output or "error:read:" in result.output
