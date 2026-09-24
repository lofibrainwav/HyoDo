"""Tests for `hyodo init` (Bring-Your-Own-Gates onboarding).

Covers: detection -> `.hyodo/gates.toml` write, refusal to overwrite an
existing config, `--force` overwrite, and the honest empty-detection
template. Every case runs against an isolated `tmp_path`, never the real
HyoDo checkout, so it cannot pollute this repository's own `.hyodo/`.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.gates import SCHEMA_ID, GatesConfigError, load_gates_config

runner = CliRunner()


def _gates_path(root: Path) -> Path:
    return root / ".hyodo" / "gates.toml"


def test_init_detects_and_writes_gates_toml(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\n\n[project.optional-dependencies]\ndev = ["pytest", "ruff"]\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "Detected gates to absorb" in result.output
    assert "pytest" in result.output
    assert "ruff" in result.output

    gates_path = _gates_path(tmp_path)
    assert gates_path.exists()
    config = load_gates_config(tmp_path)
    assert config is not None
    assert config.schema == SCHEMA_ID
    names = {gate.name for gate in config.gates}
    assert "pytest" in names
    assert "ruff" in names


def test_init_shows_trilingual_pillar_labels(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project.optional-dependencies]\ndev = ["pytest", "mypy", "ruff"]\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    # pytest and mypy -> truth (眞/진/Truth): tests and typing are Truth.
    assert "眞" in result.output
    assert "\uc9c4" in result.output
    assert "Truth" in result.output
    # ruff -> beauty (美/미/Beauty)
    assert "美" in result.output
    assert "\ubbf8" in result.output
    assert "Beauty" in result.output
    # No detected test runner is proposed as Goodness.
    assert "善" not in result.output


def test_init_refuses_to_overwrite_existing_config_without_force(tmp_path: Path) -> None:
    gates_path = _gates_path(tmp_path)
    gates_path.parent.mkdir(parents=True)
    original = (
        'schema = "hyodo.gates/v1"\n\n[gates.custom]\npillar = "goodness"\ncommand = "true"\n'
    )
    gates_path.write_text(original, encoding="utf-8")

    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 1
    assert "already exists" in result.output
    assert gates_path.read_text(encoding="utf-8") == original


def test_init_force_overwrites_existing_config(tmp_path: Path) -> None:
    gates_path = _gates_path(tmp_path)
    gates_path.parent.mkdir(parents=True)
    gates_path.write_text(
        'schema = "hyodo.gates/v1"\n\n[gates.custom]\npillar = "goodness"\ncommand = "true"\n',
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project.optional-dependencies]\ndev = ["pytest"]\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["init", str(tmp_path), "--force"])

    assert result.exit_code == 0
    config = load_gates_config(tmp_path)
    assert config is not None
    names = {gate.name for gate in config.gates}
    assert "custom" not in names
    assert "pytest" in names


def test_init_zero_detection_writes_an_inert_example_not_a_live_config(tmp_path: Path) -> None:
    """4.21: zero detections must not switch `hyodo check` onto the BYOG branch.

    Until 4.20 the starter template was written to `.hyodo/gates.toml` itself.
    Its mere presence is what selects BYOG, and a config with no active gate
    table makes `hyodo check` report "no gates executed" (exit 2) instead of
    falling back to the built-in sampled gates. The starter content is still
    written -- to an inert `.example` name the operator renames on purpose.
    """
    result = runner.invoke(app, ["init", str(tmp_path)])

    assert result.exit_code == 0
    assert "No supported tool was detected" in result.output

    assert not _gates_path(tmp_path).exists()
    # Nothing to load means `hyodo check` keeps its sampled fallback.
    assert load_gates_config(tmp_path) is None

    example_path = tmp_path / ".hyodo" / "gates.toml.example"
    rendered = example_path.read_text(encoding="utf-8")
    assert f'schema = "{SCHEMA_ID}"' in rendered
    assert "# [gates.tests]" in rendered  # commented-out example, not an active gate
    # The suggested test gate follows hyodo/virtues.py: tests are Truth.
    assert '# [gates.tests]\n# pillar = "truth"' in rendered


def test_init_renamed_example_still_refuses_to_load_silently(tmp_path: Path) -> None:
    """Activating the untouched example must fail loudly, not run zero gates."""
    runner.invoke(app, ["init", str(tmp_path)])
    example_path = tmp_path / ".hyodo" / "gates.toml.example"
    example_path.rename(_gates_path(tmp_path))

    with pytest.raises(GatesConfigError, match="no gates"):
        load_gates_config(tmp_path)


def test_init_missing_path_exits_2(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(app, ["init", str(missing)])
    assert result.exit_code == 2


def test_init_prints_next_steps(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project.optional-dependencies]\ndev = ["pytest"]\n', encoding="utf-8"
    )
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "hyodo check" in result.output
    assert "hyodo dashboard" in result.output


def test_init_zero_detection_next_steps_point_at_the_example(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", str(tmp_path)])
    assert result.exit_code == 0
    assert "gates.toml.example" in result.output
    assert "hyodo check" in result.output
