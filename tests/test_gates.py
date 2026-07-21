"""Tests for hyodo.gates: Bring-Your-Own-Gates config loading, execution, and detection.

All commands are cheap stdlib/system binaries (true, false, echo, sleep) or
deliberately nonexistent names -- no real project tooling is invoked so the
suite stays fast and hermetic.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hyodo.gates import (
    DEFAULT_TIMEOUT_SECONDS,
    SCHEMA_ID,
    GatesConfig,
    GatesConfigError,
    UserGate,
    UserGateResult,
    detect_project_gates,
    load_gates_config,
    render_gates_toml,
    run_user_gates,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write_gates_toml(root: Path, body: str) -> Path:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir(parents=True, exist_ok=True)
    path = hyodo_dir / "gates.toml"
    path.write_text(body, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# load_gates_config
# ---------------------------------------------------------------------------


def test_load_gates_config_missing_file_returns_none(tmp_path: Path) -> None:
    assert load_gates_config(tmp_path) is None


def test_load_gates_config_normal(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.tests]
pillar = "goodness"
command = "pytest -q"
timeout = 300
""",
    )

    config = load_gates_config(tmp_path)

    assert isinstance(config, GatesConfig)
    assert config.schema == SCHEMA_ID
    assert config.gates == (
        UserGate(name="tests", pillar="goodness", command=("pytest", "-q"), timeout=300),
    )


def test_load_gates_config_uses_default_timeout(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.lint]
pillar = "beauty"
command = "ruff check"
""",
    )

    config = load_gates_config(tmp_path)

    assert config is not None
    assert config.gates[0].timeout == DEFAULT_TIMEOUT_SECONDS


def test_load_gates_config_command_as_array(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.tests]
pillar = "goodness"
command = ["pytest", "-q", "-k", "smoke"]
""",
    )

    config = load_gates_config(tmp_path)

    assert config is not None
    assert config.gates[0].command == ("pytest", "-q", "-k", "smoke")


def test_load_gates_config_broken_toml_raises(tmp_path: Path) -> None:
    _write_gates_toml(tmp_path, "schema = 'unterminated\n[gates.tests\n")

    with pytest.raises(GatesConfigError):
        load_gates_config(tmp_path)


def test_load_gates_config_schema_mismatch_raises(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v999"

[gates.tests]
pillar = "goodness"
command = "pytest -q"
""",
    )

    with pytest.raises(GatesConfigError, match="schema"):
        load_gates_config(tmp_path)


def test_load_gates_config_missing_schema_raises(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
[gates.tests]
pillar = "goodness"
command = "pytest -q"
""",
    )

    with pytest.raises(GatesConfigError, match="schema"):
        load_gates_config(tmp_path)


def test_load_gates_config_pillar_typo_raises(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.tests]
pillar = "goodnes"
command = "pytest -q"
""",
    )

    with pytest.raises(GatesConfigError, match="pillar"):
        load_gates_config(tmp_path)


def test_load_gates_config_empty_gates_raises(tmp_path: Path) -> None:
    _write_gates_toml(tmp_path, 'schema = "hyodo.gates/v1"\n')

    with pytest.raises(GatesConfigError, match="no gates"):
        load_gates_config(tmp_path)


def test_load_gates_config_missing_command_raises(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.tests]
pillar = "goodness"
""",
    )

    with pytest.raises(GatesConfigError, match="command"):
        load_gates_config(tmp_path)


def test_load_gates_config_invalid_timeout_raises(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.tests]
pillar = "goodness"
command = "pytest -q"
timeout = -5
""",
    )

    with pytest.raises(GatesConfigError, match="timeout"):
        load_gates_config(tmp_path)


# ---------------------------------------------------------------------------
# run_user_gates
# ---------------------------------------------------------------------------


def test_run_user_gates_pass(tmp_path: Path) -> None:
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(UserGate(name="ok", pillar="goodness", command=("true",), timeout=5),),
    )

    results = run_user_gates(config, tmp_path)

    assert results == [UserGateResult(name="ok", pillar="goodness", status="PASS", message="ok")]


def test_run_user_gates_fail(tmp_path: Path) -> None:
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(UserGate(name="bad", pillar="goodness", command=("false",), timeout=5),),
    )

    results = run_user_gates(config, tmp_path)

    assert len(results) == 1
    assert results[0].name == "bad"
    assert results[0].pillar == "goodness"
    assert results[0].status == "FAIL"


def test_run_user_gates_skip_missing_binary(tmp_path: Path) -> None:
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(
            UserGate(
                name="ghost",
                pillar="truth",
                command=("totally-nonexistent-binary-xyz-hyodo",),
                timeout=5,
            ),
        ),
    )

    results = run_user_gates(config, tmp_path)

    assert results[0].status == "SKIP"
    assert "not installed" in results[0].message


def test_run_user_gates_timeout(tmp_path: Path) -> None:
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(UserGate(name="slow", pillar="goodness", command=("sleep", "5"), timeout=1),),
    )

    results = run_user_gates(config, tmp_path)

    assert results[0].status == "FAIL"
    assert "timeout" in results[0].message.lower()


def test_run_user_gates_string_vs_array_command_equivalent(tmp_path: Path) -> None:
    _write_gates_toml(
        tmp_path,
        """
schema = "hyodo.gates/v1"

[gates.string_form]
pillar = "goodness"
command = "true"

[gates.array_form]
pillar = "goodness"
command = ["true"]
""",
    )
    config = load_gates_config(tmp_path)
    assert config is not None

    results = run_user_gates(config, tmp_path)

    assert {r.name: r.status for r in results} == {"string_form": "PASS", "array_form": "PASS"}


def test_run_user_gates_verbose_includes_stdout_tail(tmp_path: Path) -> None:
    config = GatesConfig(
        schema=SCHEMA_ID,
        gates=(
            UserGate(
                name="echoer",
                pillar="goodness",
                command=("echo", "hyodo-verbose-marker"),
                timeout=5,
            ),
        ),
    )

    quiet = run_user_gates(config, tmp_path, verbose=False)
    loud = run_user_gates(config, tmp_path, verbose=True)

    assert quiet[0].message == "ok"
    assert "hyodo-verbose-marker" in loud[0].message


# ---------------------------------------------------------------------------
# detect_project_gates
# ---------------------------------------------------------------------------


def test_detect_project_gates_empty_repo(tmp_path: Path) -> None:
    assert detect_project_gates(tmp_path) == {}


def test_detect_project_gates_pyproject_pytest(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
name = "demo"

[project.optional-dependencies]
dev = ["pytest>=8.0", "mypy", "ruff"]

[tool.pyright]
pythonVersion = "3.10"
""",
        encoding="utf-8",
    )

    detected = detect_project_gates(tmp_path)

    assert detected["pytest"]["pillar"] == "goodness"
    assert detected["pytest"]["command"] == "pytest -q"
    assert detected["mypy"]["pillar"] == "truth"
    assert detected["ruff"]["pillar"] == "beauty"
    assert detected["pyright"]["pillar"] == "truth"
    assert all("source" in spec for spec in detected.values())


def test_detect_project_gates_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        """
{
  "name": "demo",
  "scripts": {
    "test": "vitest run",
    "lint": "eslint ."
  }
}
""",
        encoding="utf-8",
    )

    detected = detect_project_gates(tmp_path)

    assert detected["npm-test"] == {
        "pillar": "goodness",
        "command": "npm test",
        "source": "package.json",
    }
    assert detected["npm-lint"] == {
        "pillar": "beauty",
        "command": "npm run lint",
        "source": "package.json",
    }


def test_detect_project_gates_package_json_no_test_script_skipped(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        """{"name": "demo", "scripts": {"test": "echo \\"Error: no test specified\\" && exit 1"}}""",
        encoding="utf-8",
    )

    detected = detect_project_gates(tmp_path)

    assert "npm-test" not in detected


def test_detect_project_gates_go_mod(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/demo\n\ngo 1.22\n", encoding="utf-8")

    detected = detect_project_gates(tmp_path)

    assert detected["go-vet"]["pillar"] == "truth"
    assert detected["go-test"]["pillar"] == "goodness"


def test_detect_project_gates_cargo_toml(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "demo"\n', encoding="utf-8")

    detected = detect_project_gates(tmp_path)

    assert detected["cargo-check"]["pillar"] == "truth"
    assert detected["cargo-test"]["pillar"] == "goodness"


def test_detect_project_gates_tsconfig(tmp_path: Path) -> None:
    (tmp_path / "tsconfig.json").write_text("{}", encoding="utf-8")

    detected = detect_project_gates(tmp_path)

    assert detected["tsc"]["pillar"] == "truth"


def test_detect_project_gates_makefile(tmp_path: Path) -> None:
    (tmp_path / "Makefile").write_text(
        "test:\n\tpytest -q\n\nlint:\n\truff check\n",
        encoding="utf-8",
    )

    detected = detect_project_gates(tmp_path)

    assert detected["make-test"]["pillar"] == "goodness"
    assert detected["make-lint"]["pillar"] == "beauty"


# ---------------------------------------------------------------------------
# render_gates_toml round trip
# ---------------------------------------------------------------------------


def test_render_gates_toml_round_trip(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff"]
""",
        encoding="utf-8",
    )
    detected = detect_project_gates(tmp_path)
    assert detected  # sanity: pyproject fixture must produce at least one gate

    rendered = render_gates_toml(detected)
    _write_gates_toml(tmp_path, rendered)

    config = load_gates_config(tmp_path)

    assert config is not None
    assert config.schema == SCHEMA_ID
    names = {gate.name for gate in config.gates}
    assert names == set(detected.keys())
    for gate in config.gates:
        assert gate.pillar == detected[gate.name]["pillar"]
        assert " ".join(gate.command) == detected[gate.name]["command"]
        assert gate.timeout == DEFAULT_TIMEOUT_SECONDS


def test_render_gates_toml_includes_native_pillar_note() -> None:
    rendered = render_gates_toml(
        {"tests": {"pillar": "goodness", "command": "pytest -q", "source": "manual"}}
    )

    assert 'schema = "hyodo.gates/v1"' in rendered
    assert "HyoDo measures them natively" in rendered
    assert "[gates.tests]" in rendered
