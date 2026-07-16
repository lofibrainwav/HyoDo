"""Unit tests for CLI tool invocation helpers (venv-safe paths)."""

import sys
from unittest.mock import MagicMock, patch

from hyodo.cli.main import _missing_tool_result, _tool_cmd, run_pytest_check, run_ruff_check


def test_tool_cmd_uses_current_interpreter():
    cmd = _tool_cmd("pytest", "tests", "-q")
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "pytest"]
    assert cmd[3:] == ["tests", "-q"]


def test_run_pytest_check_uses_python_m_pytest():
    mock_result = MagicMock(returncode=0, stdout="5 passed in 0.01s\n", stderr="")
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", return_value=mock_result) as run,
    ):
        ok, msg = run_pytest_check(verbose=False)
    assert ok is True
    assert "passed" in msg.lower()
    cmd = run.call_args.args[0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "pytest"]


def test_missing_tool_soft_skip_in_package_mode():
    ok, msg = _missing_tool_result("ruff", root=None)
    assert ok is True
    assert "package mode" in msg


def test_missing_tool_fails_in_repo_mode(tmp_path):
    ok, msg = _missing_tool_result("ruff", root=tmp_path)
    assert ok is False
    assert "not found" in msg


def test_ruff_missing_soft_skip_outside_repo():
    with (
        patch("hyodo.cli.main.find_repo_root", return_value=None),
        patch("hyodo.cli.main._module_importable", return_value=False),
    ):
        ok, msg = run_ruff_check()
    assert ok is True
    assert "package mode" in msg
