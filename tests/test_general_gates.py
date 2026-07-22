"""Tests for ``hyodo check --general`` and ``hyodo safe --max-files``.

Covers the language-agnostic gate helpers in ``hyodo/cli/main.py``
(``_collect_files``, ``_run_general_gates``, ``_run_per_file_general_cmd``,
``_print_general_results``, ``GeneralGateResult``) and the directory-scan cap
plumbed through ``safe`` / ``run_safety_scan``.

Only Python and Shell gates are exercised end to end here — they need no
external toolchain (tsc/go/cargo are skipped by the production code itself
when the matching binary/manifest is absent, so those paths stay untested
by design in this file).
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import GateStatus, _collect_files, _run_general_gates, app
from hyodo.safety import run_safety_scan

runner = CliRunner()


# --------------------------------------------------------------------------- #
# _collect_files
# --------------------------------------------------------------------------- #


def test_collect_files_skips_vendor_and_hidden_dirs(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("y = 2\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "c.py").write_text("z = 3\n")
    (tmp_path / ".hidden").mkdir()
    (tmp_path / ".hidden" / "d.py").write_text("w = 4\n")

    collected = _collect_files(tmp_path, (".py",))

    assert len(collected) == 2
    assert {p.name for p in collected} == {"a.py", "b.py"}


def test_collect_files_respects_cap(tmp_path: Path):
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("y = 2\n")

    collected = _collect_files(tmp_path, (".py",), cap=1)

    assert len(collected) == 1


def test_collect_files_empty_dir_returns_empty_list(tmp_path: Path):
    collected = _collect_files(tmp_path, (".py",))

    assert collected == []


def test_general_gate_excludes_only_documented_private_path(tmp_path: Path):
    hyodo_dir = tmp_path / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "scan-exceptions.toml").write_text(
        """schema = "hyodo.scan-exceptions/v1"

[[general_exceptions]]
path = "private/legal/**"
reason = "private legal working material"
""",
        encoding="utf-8",
    )
    private_file = tmp_path / "private" / "legal" / "broken.py"
    private_file.parent.mkdir(parents=True)
    private_file.write_text("def broken(:\n", encoding="utf-8")
    public_file = tmp_path / "public.py"
    public_file.write_text("x = 1\n", encoding="utf-8")

    result = runner.invoke(app, ["check", "--general", str(tmp_path)])

    assert result.exit_code == 0
    assert "Audited general exclusions configured: 1" in result.output


# --------------------------------------------------------------------------- #
# _run_general_gates - Python
# --------------------------------------------------------------------------- #


def test_run_general_gates_valid_python_passes(tmp_path: Path):
    (tmp_path / "ok.py").write_text("x = 1\n")

    results = _run_general_gates(tmp_path)

    python_results = [r for r in results if r.language == "Python"]
    assert len(python_results) == 1
    assert python_results[0].status is GateStatus.PASS


def test_run_general_gates_python_syntax_error_fails(tmp_path: Path):
    (tmp_path / "broken.py").write_text("def broken(:\n    pass\n")

    results = _run_general_gates(tmp_path)

    python_results = [r for r in results if r.language == "Python"]
    assert len(python_results) == 1
    assert python_results[0].status is GateStatus.FAIL


# --------------------------------------------------------------------------- #
# _run_general_gates - Shell
# --------------------------------------------------------------------------- #


def test_run_general_gates_valid_shell_passes(tmp_path: Path):
    (tmp_path / "ok.sh").write_text("echo ok\n")

    results = _run_general_gates(tmp_path)

    shell_results = [r for r in results if r.language == "Shell"]
    assert len(shell_results) == 1
    assert shell_results[0].status is GateStatus.PASS


def test_run_general_gates_shell_syntax_error_fails(tmp_path: Path):
    (tmp_path / "broken.sh").write_text("if [ ; then\n")

    results = _run_general_gates(tmp_path)

    shell_results = [r for r in results if r.language == "Shell"]
    assert len(shell_results) == 1
    assert shell_results[0].status is GateStatus.FAIL


# --------------------------------------------------------------------------- #
# CLI: hyodo check --general
# --------------------------------------------------------------------------- #


def test_cli_check_general_valid_python_exit_0(tmp_path: Path):
    (tmp_path / "ok.py").write_text("x = 1\n")

    result = runner.invoke(app, ["check", "--general", str(tmp_path)])

    assert result.exit_code == 0
    assert "Sampled syntax gates" in result.output


def test_cli_check_general_syntax_error_exit_1(tmp_path: Path):
    (tmp_path / "broken.py").write_text("def broken(:\n    pass\n")

    result = runner.invoke(app, ["check", "--general", str(tmp_path)])

    assert result.exit_code == 1
    assert "Some gates failed" in result.output


def test_cli_check_general_empty_dir_exit_2(tmp_path: Path):
    result = runner.invoke(app, ["check", "--general", str(tmp_path)])

    assert result.exit_code == 2
    assert "No language gates were executed" in result.output


# --------------------------------------------------------------------------- #
# CLI: hyodo safe --max-files
# --------------------------------------------------------------------------- #


def test_cli_safe_max_files_caps_directory_scan(tmp_path: Path):
    for name in ("one.txt", "two.txt", "three.txt"):
        (tmp_path / name).write_text("harmless content\n")

    result = runner.invoke(app, ["safe", str(tmp_path), "--max-files", "2"])

    assert result.exit_code == 0
    # Rich wraps long source lines at terminal width (wrap position varies
    # with tmp_path length across OSes) — normalize whitespace before asserting.
    assert "(2 files)" in " ".join(result.output.split())


def test_cli_safe_max_files_zero_is_unlimited(tmp_path: Path):
    for name in ("one.txt", "two.txt", "three.txt"):
        (tmp_path / name).write_text("harmless content\n")

    result = runner.invoke(app, ["safe", str(tmp_path), "--max-files", "0"])

    assert "(3 files)" in " ".join(result.output.split())


# --------------------------------------------------------------------------- #
# run_safety_scan (direct call)
# --------------------------------------------------------------------------- #


def test_run_safety_scan_max_files_zero_unlimited_source_suffix(tmp_path: Path):
    for name in ("one.txt", "two.txt", "three.txt"):
        (tmp_path / name).write_text("harmless content\n")

    result = run_safety_scan(path=str(tmp_path), max_files=0, cwd=tmp_path)

    assert str(result["source"]).endswith("(3 files)")
