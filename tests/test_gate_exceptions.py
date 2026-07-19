"""Exception-branch coverage for the four HyoDo gate functions.

Each gate in ``hyodo.cli.main`` shells out through ``subprocess.run`` and
guards the call with three handlers: ``FileNotFoundError`` (tool binary
missing), ``subprocess.TimeoutExpired`` (tool exceeded its budget), and a
catch-all ``Exception``. These tests inject each failure via
``patch("hyodo.cli.main.subprocess.run", side_effect=...)`` and assert the
exact ``GateStatus`` and message the code produces.
"""

import subprocess
from unittest.mock import patch

import pytest

from hyodo.cli.main import (
    GateStatus,
    run_pyright_check,
    run_pytest_check,
    run_ruff_check,
    run_sbom_check,
)


def _pytest_root(tmp_path):
    """run_pytest_check requires a tests/ dir before it reaches subprocess."""
    (tmp_path / "tests").mkdir()
    return tmp_path


def _sbom_root(tmp_path):
    """run_sbom_check requires the SBOM script to exist to reach subprocess."""
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "generate_sbom.py").write_text("print('sbom')\n")
    return tmp_path


# ---------------------------------------------------------------------------
# Gate 1: run_pyright_check
# ---------------------------------------------------------------------------


def test_pyright_file_not_found(tmp_path):
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=FileNotFoundError()),
    ):
        result = run_pyright_check(tmp_path)
    # FileNotFoundError routes back through _missing_tool_result (root present).
    assert result.status is GateStatus.FAIL
    assert result.message == "pyright not found (install: pip install pyright or hyodo[dev])"


def test_pyright_timeout(tmp_path):
    timeout = subprocess.TimeoutExpired(cmd=["pyright"], timeout=120)
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=timeout),
    ):
        result = run_pyright_check(tmp_path)
    assert result.status is GateStatus.FAIL
    assert result.message == "timeout (>120s)"


def test_pyright_generic_exception(tmp_path):
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=RuntimeError("boom")),
    ):
        result = run_pyright_check(tmp_path)
    assert result.status is GateStatus.FAIL
    assert result.message == "exception: boom"


# ---------------------------------------------------------------------------
# Gate 2: run_ruff_check
# ---------------------------------------------------------------------------


def test_ruff_file_not_found(tmp_path):
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=FileNotFoundError()),
    ):
        result = run_ruff_check(tmp_path)
    assert result.status is GateStatus.FAIL
    assert result.message == "ruff not found (install: pip install ruff or hyodo[dev])"


def test_ruff_timeout(tmp_path):
    timeout = subprocess.TimeoutExpired(cmd=["ruff"], timeout=60)
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=timeout),
    ):
        result = run_ruff_check(tmp_path)
    assert result.status is GateStatus.FAIL
    assert result.message == "timeout (>60s)"


def test_ruff_generic_exception(tmp_path):
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=RuntimeError("boom")),
    ):
        result = run_ruff_check(tmp_path)
    assert result.status is GateStatus.FAIL
    assert result.message == "exception: boom"


# ---------------------------------------------------------------------------
# Gate 3: run_pytest_check
# ---------------------------------------------------------------------------


def test_pytest_file_not_found(tmp_path):
    root = _pytest_root(tmp_path)
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=FileNotFoundError()),
    ):
        result = run_pytest_check(root)
    assert result.status is GateStatus.FAIL
    assert result.message == "pytest not found (install: pip install pytest or hyodo[dev])"


def test_pytest_timeout(tmp_path):
    root = _pytest_root(tmp_path)
    timeout = subprocess.TimeoutExpired(cmd=["pytest"], timeout=300)
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=timeout),
    ):
        result = run_pytest_check(root)
    assert result.status is GateStatus.FAIL
    assert result.message == "timeout (>300s)"


def test_pytest_generic_exception(tmp_path):
    root = _pytest_root(tmp_path)
    with (
        patch("hyodo.cli.main._module_importable", return_value=True),
        patch("hyodo.cli.main.subprocess.run", side_effect=RuntimeError("boom")),
    ):
        result = run_pytest_check(root)
    assert result.status is GateStatus.FAIL
    assert result.message == "exception: boom"


# ---------------------------------------------------------------------------
# Gate 4: run_sbom_check
# ---------------------------------------------------------------------------


def test_sbom_skip_when_script_absent(tmp_path):
    # No scripts/generate_sbom.py exists: SKIP before any subprocess call.
    with patch("hyodo.cli.main.subprocess.run") as run:
        result = run_sbom_check(tmp_path)
    run.assert_not_called()
    assert result.status is GateStatus.SKIP
    assert result.message == "SBOM script not found; not executed"


def test_sbom_file_not_found_skips(tmp_path):
    # Environment failures must SKIP (never a false FAIL), like an absent script.
    root = _sbom_root(tmp_path)
    with patch("hyodo.cli.main.subprocess.run", side_effect=FileNotFoundError()):
        result = run_sbom_check(root)
    assert result.status is GateStatus.SKIP


def test_sbom_timeout_skips(tmp_path):
    root = _sbom_root(tmp_path)
    timeout = subprocess.TimeoutExpired(cmd=["python"], timeout=180)
    with patch("hyodo.cli.main.subprocess.run", side_effect=timeout):
        result = run_sbom_check(root)
    assert result.status is GateStatus.SKIP


def test_sbom_unexpected_exception_fails(tmp_path):
    root = _sbom_root(tmp_path)
    with patch("hyodo.cli.main.subprocess.run", side_effect=RuntimeError("boom")):
        result = run_sbom_check(root)
    assert result.status is GateStatus.FAIL
    assert "unexpected" in result.message


def test_sbom_oserror_skips(tmp_path):
    # A genuine OS/environment failure stays an honest SKIP, not a false FAIL.
    root = _sbom_root(tmp_path)
    with patch("hyodo.cli.main.subprocess.run", side_effect=OSError("disk full")):
        result = run_sbom_check(root)
    assert result.status is GateStatus.SKIP
    assert "environment" in result.message


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
