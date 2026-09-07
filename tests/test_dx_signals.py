"""Tests for `hyodo/dx_signals.py`.

Covers the three onboarding/DX signals `_derive_benevolence` consumes
(`readme_present`, `start_hint_present`, `help_text_present`): a project with
all three present, independent failure of each, foreign-project help-text
detection via a declared entry point plus a README usage mention, and that
collection never shells out (a monkeypatched `subprocess.run` that raises
must not stop the collector from succeeding).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from hyodo.dx_signals import collect_dx_signals

_LONG_README_FILLER = (
    "This project does something useful and this paragraph exists purely to "
    "push the README past the two-hundred-byte non-empty threshold that "
    "`readme_present` checks for, so the test fixture is realistic.\n"
)


def _write_pyproject_with_scripts(root: Path, name: str = "sample-project") -> None:
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\n\n[project.scripts]\n{name} = "{name.replace("-", "_")}.cli:app"\n',
        encoding="utf-8",
    )


def test_all_three_signals_true_with_evidence(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Sample\n\n" + _LONG_README_FILLER + "\n## Quick start\n\n```bash\nhyodo start\n```\n\n"
        "Run `sample-project --help` for usage.\n",
        encoding="utf-8",
    )
    _write_pyproject_with_scripts(tmp_path)

    signals = collect_dx_signals(tmp_path)

    assert signals.readme_present is True
    assert signals.start_hint_present is True
    assert signals.help_text_present is True
    assert "readme_present" in signals.evidence
    assert "start_hint_present" in signals.evidence
    assert "help_text_present" in signals.evidence
    assert "README.md" in signals.evidence["readme_present"]
    assert "hyodo start" in signals.evidence["start_hint_present"]


def test_readme_missing_makes_readme_signal_false_others_independent(tmp_path: Path) -> None:
    _write_pyproject_with_scripts(tmp_path)
    # No README at all: readme_present is false, but help_text_present can
    # still be evaluated (it has its own evidence path) and is false here
    # because there is no usage mention anywhere to find.
    signals = collect_dx_signals(tmp_path)

    assert signals.readme_present is False
    assert signals.start_hint_present is False
    assert signals.help_text_present is False
    assert "readme_present" not in signals.evidence or "only" in signals.evidence.get(
        "readme_present", ""
    )


def test_readme_present_without_start_hint_is_false(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Sample\n\n" + _LONG_README_FILLER + "\nNo onboarding commands mentioned here at all.\n",
        encoding="utf-8",
    )

    signals = collect_dx_signals(tmp_path)

    assert signals.readme_present is True
    assert signals.start_hint_present is False
    assert "start_hint_present" not in signals.evidence


def test_package_json_bin_plus_readme_help_usage(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Sample CLI\n\n"
        + _LONG_README_FILLER
        + "\n## Installation\n\n```bash\nnpm start\n```\n\nSee `sample --help` for usage.\n",
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "sample", "bin": {"sample": "./bin/sample.js"}}),
        encoding="utf-8",
    )

    signals = collect_dx_signals(tmp_path)

    assert signals.help_text_present is True
    assert "entrypoint:sample" in signals.evidence["help_text_present"]
    assert signals.start_hint_present is True


def test_entry_point_without_readme_usage_mention_is_false(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Sample\n\n" + _LONG_README_FILLER, encoding="utf-8")
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "sample", "bin": {"sample": "./bin/sample.js"}}),
        encoding="utf-8",
    )

    signals = collect_dx_signals(tmp_path)

    assert signals.help_text_present is False


def test_determinism(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Sample\n\n" + _LONG_README_FILLER + "\n`pip install -e .`\n\n`--help`\n",
        encoding="utf-8",
    )
    _write_pyproject_with_scripts(tmp_path)

    first = collect_dx_signals(tmp_path)
    second = collect_dx_signals(tmp_path)

    assert first == second


def test_never_executes_a_subprocess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "README.md").write_text(
        "# Sample\n\n" + _LONG_README_FILLER + "\n`make setup`\n\n`--help`\n",
        encoding="utf-8",
    )
    _write_pyproject_with_scripts(tmp_path)

    def _boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("collect_dx_signals must never call subprocess.run")

    monkeypatch.setattr(subprocess, "run", _boom)

    signals = collect_dx_signals(tmp_path)

    assert signals.readme_present is True
    assert signals.start_hint_present is True


def test_hyodo_self_check_uses_in_process_import(tmp_path: Path) -> None:
    """Root that declares itself as the `hyodo` project imports the real app."""
    (tmp_path / "README.md").write_text(
        "# HyoDo\n\n" + _LONG_README_FILLER + "\n`hyodo start`\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "hyodo"\n\n[project.scripts]\nhyodo = "hyodo.cli.main:app"\n',
        encoding="utf-8",
    )

    signals = collect_dx_signals(tmp_path)

    # The real hyodo.cli.main:app is importable in this test environment and
    # every registered command carries help text.
    assert signals.help_text_present is True
    assert signals.evidence["help_text_present"].startswith("entrypoint:hyodo.cli.main")
