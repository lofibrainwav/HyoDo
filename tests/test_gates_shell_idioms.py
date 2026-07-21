"""Tests for shell-idiom support in BYOG gate parsing/execution (issue #89).

Covers two POSIX shell conventions that ``shell=False`` historically broke:
  * env-prefix assignments (``KEY=VALUE bin args``)
  * glob expansion (``bin *.sh``)

These are regressions for dogfood defects D1 (env prefix misread as the
executable, surfacing as ``"<KEY>=value not installed"``) and D2 (glob left
unexpanded, surfacing as ``"openBinaryFile: does not exist"``).

All execution tests use hermetic stdlib binaries (``echo``) or the running
interpreter (``sys.executable -c ...``) so no real project tooling is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from hyodo.gates import (
    SCHEMA_ID,
    GatesConfig,
    GatesConfigError,
    UserGate,
    load_gates_config,
    run_user_gates,
)


def _write_gates(root: Path, body: str) -> None:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    (hyodo_dir / "gates.toml").write_text(body, encoding="utf-8")


# ---------------------------------------------------------------------------
# env-prefix: parsing
# ---------------------------------------------------------------------------


def test_env_prefix_separated_from_command(tmp_path: Path) -> None:
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.unit]
pillar = "truth"
command = "KINGDOM_TEST_SCOPE=unit bash x.sh"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    gate = config.gates[0]
    assert gate.env == ("KINGDOM_TEST_SCOPE=unit",)
    assert gate.command == ("bash", "x.sh")


def test_env_prefix_only_assignment_raises(tmp_path: Path) -> None:
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.bad]
pillar = "truth"
command = "FOO=bar"
""",
    )
    with pytest.raises(GatesConfigError, match="env"):
        load_gates_config(tmp_path)


def test_gate_without_env_has_empty_env(tmp_path: Path) -> None:
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.plain]
pillar = "goodness"
command = "true"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    assert config.gates[0].env == ()


def test_multiple_env_prefixes_separated(tmp_path: Path) -> None:
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.multi]
pillar = "truth"
command = "A=1 B=2 C=3 true"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    gate = config.gates[0]
    assert gate.env == ("A=1", "B=2", "C=3")
    assert gate.command == ("true",)


# ---------------------------------------------------------------------------
# env-prefix: execution
# ---------------------------------------------------------------------------


def test_env_prefix_passed_to_subprocess(tmp_path: Path) -> None:
    probe = "import os,sys; print(os.environ.get('HYODO_PROBE','MISSING')); sys.exit(0)"
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(
            UserGate(
                name="envprobe",
                pillar="truth",
                command=(sys.executable, "-c", probe),
                timeout=10,
                env=("HYODO_PROBE=seen",),
            ),
        ),
    )
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    assert "seen" in results[0].message


def test_env_prefix_missing_binary_no_longer_false_skip(tmp_path: Path) -> None:
    # D1 regression: previously "FOO=bar nonexistent" reported "FOO=bar not
    # installed". After the fix FOO=bar is consumed as env and the real
    # binary name is the one surfaced in the SKIP message.
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(
            UserGate(
                name="d1",
                pillar="truth",
                command=("totally-nonexistent-binary-xyz-hyodo",),
                timeout=5,
                env=("HYODO_VAR=x",),
            ),
        ),
    )
    results = run_user_gates(config, tmp_path)
    assert results[0].status == "SKIP"
    assert "totally-nonexistent-binary-xyz-hyodo" in results[0].message
    assert "HYODO_VAR=x" not in results[0].message


# ---------------------------------------------------------------------------
# glob expansion
# ---------------------------------------------------------------------------


def test_glob_expanded_relative_to_root(tmp_path: Path) -> None:
    (tmp_path / "a.sh").write_text("", encoding="utf-8")
    (tmp_path / "b.sh").write_text("", encoding="utf-8")
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.shells]
pillar = "goodness"
command = "echo *.sh"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    msg = results[0].message
    assert "a.sh" in msg
    assert "b.sh" in msg
    assert msg.find("a.sh") < msg.find("b.sh")  # sorted expansion order


def test_glob_no_match_kept_as_literal(tmp_path: Path) -> None:
    # POSIX nullglob=off: zero matches -> the literal pattern is passed through.
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.nomatch]
pillar = "goodness"
command = "echo *.nomatch"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    assert "*.nomatch" in results[0].message


def test_non_wildcard_args_untouched(tmp_path: Path) -> None:
    (tmp_path / "keep.me").write_text("", encoding="utf-8")
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.literal]
pillar = "goodness"
command = "echo hello world"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    assert results[0].message.strip().endswith("hello world")


# ---------------------------------------------------------------------------
# env-prefix + glob combined
# ---------------------------------------------------------------------------


def test_env_prefix_and_glob_combined(tmp_path: Path) -> None:
    (tmp_path / "x.txt").write_text("", encoding="utf-8")
    (tmp_path / "y.txt").write_text("", encoding="utf-8")
    probe = (
        "import os,sys; "
        "print('FILES=' + ' '.join(sys.argv[1:])); "
        "print('ENV=' + os.environ.get('HYODO_COMBINED','MISSING'))"
    )
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(
            UserGate(
                name="combo",
                pillar="truth",
                command=(sys.executable, "-c", probe, "*.txt"),
                timeout=10,
                env=("HYODO_COMBINED=ok",),
            ),
        ),
    )
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    msg = results[0].message
    assert "x.txt" in msg
    assert "y.txt" in msg
    assert "ENV=ok" in msg


# ---------------------------------------------------------------------------
# kingdom real-world reproduction (dogfood D1 / D2 canonical commands)
# ---------------------------------------------------------------------------


def test_kingdom_unit_gate_parses_env_prefix(tmp_path: Path) -> None:
    # kingdom canonical truth gate: KINGDOM_TEST_SCOPE=unit bash scripts/run-tests.sh
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.unit-tests]
pillar = "truth"
command = "KINGDOM_TEST_SCOPE=unit bash scripts/run-tests.sh"
timeout = 600
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    gate = config.gates[0]
    assert gate.name == "unit-tests"
    assert gate.env == ("KINGDOM_TEST_SCOPE=unit",)
    assert gate.command == ("bash", "scripts/run-tests.sh")
    assert gate.timeout == 600


def test_glob_absolute_pattern_kept_as_literal(tmp_path: Path) -> None:
    # glob.glob(..., root_dir=...) ignores root_dir for absolute patterns, so
    # an absolute wildcard would otherwise glob the real filesystem outside
    # root. It must never be expanded -- kept literal instead.
    outside = tmp_path.parent / f"{tmp_path.name}-sibling-abs"
    outside.mkdir(exist_ok=True)
    (outside / "secret.sh").write_text("", encoding="utf-8")
    pattern = f"{outside}/*.sh"
    _write_gates(
        tmp_path,
        f"""
schema = "hyodo.gates/v1"

[gates.abs]
pillar = "goodness"
command = "echo {pattern}"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    msg = results[0].message
    assert pattern in msg
    assert "secret.sh" not in msg


def test_glob_parent_escape_pattern_kept_as_literal(tmp_path: Path) -> None:
    # A "../" pattern can walk above root and match files outside the
    # sandboxed checkout. Those escaping matches must be filtered out; with
    # zero matches remaining the literal pattern is passed through untouched.
    root = tmp_path / "root"
    root.mkdir()
    sibling = tmp_path / "sibling"
    sibling.mkdir()
    (sibling / "escaped.sh").write_text("", encoding="utf-8")
    _write_gates(
        root,
        """
schema = "hyodo.gates/v1"

[gates.escape]
pillar = "goodness"
command = "echo ../sibling/*.sh"
""",
    )
    config = load_gates_config(root)
    assert config is not None
    results = run_user_gates(config, root, verbose=True)
    assert results[0].status == "PASS"
    msg = results[0].message
    assert "../sibling/*.sh" in msg
    assert "escaped.sh" not in msg


def test_kingdom_shellcheck_gate_expands_glob(tmp_path: Path) -> None:
    # kingdom canonical goodness gate: shellcheck scripts/*.sh scripts/hooks/*.sh
    scripts = tmp_path / "scripts"
    hooks = scripts / "hooks"
    hooks.mkdir(parents=True)
    (scripts / "a.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    (hooks / "b.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    _write_gates(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.shellcheck]
pillar = "goodness"
command = "echo scripts/*.sh scripts/hooks/*.sh"
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None
    results = run_user_gates(config, tmp_path, verbose=True)
    assert results[0].status == "PASS"
    msg = results[0].message
    assert "scripts/a.sh" in msg
    assert "scripts/hooks/b.sh" in msg
