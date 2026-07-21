"""Tests for `hyodo check`'s `.hyodo/gates.toml` (Bring-Your-Own-Gates) resolution.

Verifies the priority order layered on top of the existing --general / HyoDo
checkout preset (see `tests/test_check_exit_contract.py` and
`tests/test_cli_tools.py` for those unaffected paths): a valid
`.hyodo/gates.toml` under the target root runs user gates and short-circuits
before the checkout preset entirely; a malformed config exits 2 with the
parse/schema error surfaced; an all-SKIP run still exits 2 (never a fake
green, matching the existing zero-executed-gates contract).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _write_gates_toml(root: Path, body: str) -> Path:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    path = hyodo_dir / "gates.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_check_user_gates_all_pass_exits_0(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.ok]
pillar = "goodness"
command = "true"
""",
    )

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 0
    assert "User gates" in result.output
    assert "PASS" in result.output
    assert "ok" in result.output
    assert "All executed gates passed" in result.output


def test_check_user_gates_fail_exits_1(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.bad]
pillar = "goodness"
command = "false"
""",
    )

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 1
    assert "FAIL" in result.output
    assert "Some gates failed" in result.output
    assert "All executed gates passed" not in result.output


def test_check_user_gates_all_skip_exits_2_not_a_validation_pass(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.ghost]
pillar = "truth"
command = "totally-nonexistent-binary-xyz-hyodo"
""",
    )

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 2
    assert "SKIP" in result.output
    assert "No user gates were executed" in result.output
    assert "This is not a validation pass." in result.output


def test_check_malformed_gates_toml_exits_2_with_cause(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        'schema = "hyodo.gates/v999"\n\n[gates.x]\npillar = "goodness"\ncommand = "true"\n',
    )

    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 2
    assert "schema" in result.output.lower()
    assert "This is not a validation pass." in result.output


def test_check_gates_toml_takes_priority_over_hyodo_checkout_preset(tmp_path: Path) -> None:
    """A .hyodo/gates.toml short-circuits `check` before the 4-gate HyoDo
    preset, even when the target also looks like a HyoDo checkout
    (pyproject.toml + hyodo/)."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "demo"\n', encoding="utf-8")
    (tmp_path / "hyodo").mkdir()
    (tmp_path / "hyodo" / "__init__.py").write_text("", encoding="utf-8")
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.ok]
pillar = "goodness"
command = "true"
""",
    )

    with (
        patch("hyodo.cli.main.run_pyright_check") as pyright_mock,
        patch("hyodo.cli.main.run_ruff_check") as ruff_mock,
        patch("hyodo.cli.main.run_pytest_check") as pytest_mock,
        patch("hyodo.cli.main.run_sbom_check") as sbom_mock,
    ):
        result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 0
    assert "User gates" in result.output
    pyright_mock.assert_not_called()
    ruff_mock.assert_not_called()
    pytest_mock.assert_not_called()
    sbom_mock.assert_not_called()


def test_check_no_gates_toml_and_no_checkout_hints_init(tmp_path: Path) -> None:
    result = runner.invoke(app, ["check", str(tmp_path)])

    assert result.exit_code == 2
    assert "hyodo init" in result.output
