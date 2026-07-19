"""Exit-code contract tests for `hyodo check`.

These tests pin the exit-code branch in `hyodo/cli/main.py` where the `check`
command exits 1 once any gate returns FAIL (the `if failed: raise typer.Exit(1)`
branch), and reinforce the all-pass boundary that exits 0. Gate functions are
mocked so no nested pyright/ruff/pytest/SBOM run actually executes; the command
is invoked against the real HyoDo checkout root so `find_repo_root` succeeds.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import GateResult, GateStatus, app, find_repo_root

runner = CliRunner()


def _hyodo_root() -> Path:
    """Resolve the real HyoDo checkout root from this test file location."""
    root = find_repo_root(Path(__file__).resolve())
    assert root is not None, "test must run inside a HyoDo checkout"
    return root


def test_check_gate_failure_exits_1():
    """One FAIL gate (pytest) makes `check` exit 1 with the failure banner."""
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "no sbom")
    fail = GateResult(GateStatus.FAIL, "1 failed")

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=fail),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root)])

    assert result.exit_code == 1
    assert "Some gates failed" in result.output
    # A FAIL must never be reported as a passing run.
    assert "All executed gates passed" not in result.output


def test_check_all_pass_exits_0():
    """All executed gates PASS (SBOM SKIP) makes `check` exit 0."""
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "no sbom")

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=ok),
        patch("hyodo.cli.main.run_ruff_check", return_value=ok),
        patch("hyodo.cli.main.run_pytest_check", return_value=ok),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root)])

    assert result.exit_code == 0
    assert "All executed gates passed" in result.output
    assert "Some gates failed" not in result.output


@pytest.mark.parametrize("failing_gate", ["pyright", "ruff", "pytest"])
def test_check_exits_1_regardless_of_which_gate_fails(failing_gate):
    """`check` exits 1 whenever any single executed gate returns FAIL."""
    hyodo_root = _hyodo_root()
    ok = GateResult(GateStatus.PASS, "ok")
    skip = GateResult(GateStatus.SKIP, "no sbom")
    fail = GateResult(GateStatus.FAIL, "boom")

    returns = {
        "pyright": ok,
        "ruff": ok,
        "pytest": ok,
    }
    returns[failing_gate] = fail

    with (
        patch("hyodo.cli.main.run_pyright_check", return_value=returns["pyright"]),
        patch("hyodo.cli.main.run_ruff_check", return_value=returns["ruff"]),
        patch("hyodo.cli.main.run_pytest_check", return_value=returns["pytest"]),
        patch("hyodo.cli.main.run_sbom_check", return_value=skip),
    ):
        result = runner.invoke(app, ["check", str(hyodo_root)])

    assert result.exit_code == 1
    assert "Some gates failed" in result.output
