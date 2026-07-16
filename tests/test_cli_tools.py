"""Unit tests for CLI tool invocation helpers (venv-safe paths)."""

import sys
from unittest.mock import MagicMock, patch

from hyodo.cli.main import _tool_cmd, run_pytest_check


def test_tool_cmd_uses_current_interpreter():
    cmd = _tool_cmd("pytest", "tests", "-q")
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "pytest"]
    assert cmd[3:] == ["tests", "-q"]


def test_run_pytest_check_uses_python_m_pytest():
    mock_result = MagicMock(returncode=0, stdout="5 passed in 0.01s\n", stderr="")
    with patch("hyodo.cli.main.subprocess.run", return_value=mock_result) as run:
        ok, msg = run_pytest_check(verbose=False)
    assert ok is True
    assert "passed" in msg.lower()
    cmd = run.call_args.args[0]
    assert cmd[0] == sys.executable
    assert cmd[1:3] == ["-m", "pytest"]
