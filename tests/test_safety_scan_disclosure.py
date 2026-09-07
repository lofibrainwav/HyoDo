"""Tests for directory-scan coverage disclosure in `hyodo safe`.

`hyodo safe` caps directory scans at `--max-files` (default 40). Before this
change the CLI stated the configured cap but never how many scannable files
existed, so a user could not tell whether 40 of 41 files were scanned or 40
of 4,000 — a silent partial scan, which violates "unobserved is never
green". These tests pin:

- `run_safety_scan` returning `scanned_files` / `total_scannable` in its
  result dict for a capped directory scan and for a fully-covered one.
- The `hyodo safe` text output disclosing the same numbers, with different
  phrasing depending on whether the cap actually truncated the scan.
- The `--json` payload carrying both fields.
- Default diff/status and single-file coverage includes skipped files.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.safety import run_safety_scan

runner = CliRunner()


def _make_files(tmp_path: Path, count: int) -> None:
    for i in range(count):
        (tmp_path / f"file{i:03d}.txt").write_text("harmless content\n", encoding="utf-8")


# --------------------------------------------------------------------------- #
# run_safety_scan (direct call)
# --------------------------------------------------------------------------- #


def test_run_safety_scan_dir_capped_reports_scanned_and_total(tmp_path: Path):
    _make_files(tmp_path, 45)

    result = run_safety_scan(path=str(tmp_path), max_files=40, cwd=tmp_path)

    assert result["scanned_files"] == 40
    assert result["total_scannable"] == 45


def test_run_safety_scan_dir_full_coverage_scanned_equals_total(tmp_path: Path):
    _make_files(tmp_path, 5)

    result = run_safety_scan(path=str(tmp_path), max_files=40, cwd=tmp_path)

    assert result["scanned_files"] == 5
    assert result["total_scannable"] == 5


def test_run_safety_scan_dir_unlimited_scanned_equals_total(tmp_path: Path):
    _make_files(tmp_path, 45)

    result = run_safety_scan(path=str(tmp_path), max_files=0, cwd=tmp_path)

    assert result["scanned_files"] == 45
    assert result["total_scannable"] == 45


# --------------------------------------------------------------------------- #
# CLI text output
# --------------------------------------------------------------------------- #


def test_cli_safe_text_discloses_partial_directory_coverage(tmp_path: Path):
    _make_files(tmp_path, 45)

    result = runner.invoke(app, ["safe", str(tmp_path), "--max-files", "40"])

    assert result.exit_code == 0
    normalized = " ".join(result.output.split())
    assert "scanned 40 of 45 files" in normalized
    assert "cap 40" in normalized
    assert "raise --max-files to scan all" in normalized
    assert "default corpus is git diff/status when no path" in normalized.lower()


def test_cli_safe_text_full_coverage_states_scanned_of_total(tmp_path: Path):
    _make_files(tmp_path, 5)

    result = runner.invoke(app, ["safe", str(tmp_path), "--max-files", "40"])

    assert result.exit_code == 0
    normalized = " ".join(result.output.split())
    assert "Scanned 5 of 5 files." in normalized
    # No cap-truncation language when nothing was dropped.
    assert "raise --max-files" not in normalized


# --------------------------------------------------------------------------- #
# CLI --json output
# --------------------------------------------------------------------------- #


def test_cli_safe_json_includes_scan_coverage_fields(tmp_path: Path):
    _make_files(tmp_path, 45)

    result = runner.invoke(app, ["safe", "--json", str(tmp_path), "--max-files", "40"])

    payload = json.loads(result.output)
    assert payload["scanned_files"] == 40
    assert payload["total_scannable"] == 45


def test_cli_safe_json_full_coverage_fields_equal(tmp_path: Path):
    _make_files(tmp_path, 5)

    result = runner.invoke(app, ["safe", "--json", str(tmp_path), "--max-files", "40"])

    payload = json.loads(result.output)
    assert payload["scanned_files"] == 5
    assert payload["total_scannable"] == 5


# --------------------------------------------------------------------------- #
# git diff/status corpus mode unaffected
# --------------------------------------------------------------------------- #


def test_run_safety_scan_default_corpus_makes_no_file_count_claim(tmp_path: Path):
    result = run_safety_scan(path=None, cwd=tmp_path)

    assert result["scanned_files"] is None
    assert result["total_scannable"] is None


def test_default_diff_coverage(monkeypatch, tmp_path):
    import subprocess

    import hyodo.safety as safety

    diff = (
        "diff --git a/a.py b/a.py\n--- a/a.py\n+++ b/a.py\n"
        "@@ -1 +1 @@\n-old\n+new\n"
        "diff --git a/image.png b/image.png\nBinary files differ\n"
    )
    monkeypatch.setattr(
        safety.subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, 0, diff, "")
    )
    result = run_safety_scan(cwd=tmp_path)
    assert (result["scanned_files"], result["total_scannable"]) == (1, 2)


def test_default_status_coverage(monkeypatch, tmp_path):
    import subprocess

    import hyodo.safety as safety

    (tmp_path / "a.py").write_text("print('hello')")
    (tmp_path / "b.png").write_bytes(b"\x00image")
    (tmp_path / "c.py").write_text("unreadable")
    read = safety._read_text_file

    def read_file(path):
        if path.name == "c.py":
            raise OSError("unreadable")
        return read(path)

    monkeypatch.setattr(safety, "_read_text_file", read_file)
    monkeypatch.setattr(
        safety.subprocess,
        "run",
        lambda args, **kw: subprocess.CompletedProcess(
            args, 0, "" if args[1] == "diff" else "?? a.py\n?? b.png\n?? c.py\n", ""
        ),
    )
    result = run_safety_scan(cwd=tmp_path)
    assert (result["scanned_files"], result["total_scannable"]) == (1, 3)


def test_single_file_coverage(tmp_path):
    target = tmp_path / "sample.py"
    target.write_text("print('hello')")
    result = run_safety_scan(str(target), cwd=tmp_path)
    assert (result["scanned_files"], result["total_scannable"]) == (1, 1)
    output = runner.invoke(app, ["safe", str(target), "--quiet"])
    assert "1/1 files observed" in output.output
    target.write_bytes(b"\x00binary")
    result = run_safety_scan(str(target), cwd=tmp_path)
    assert (result["scanned_files"], result["total_scannable"]) == (0, 1)


def test_single_unreadable_coverage(monkeypatch, tmp_path):
    import hyodo.safety as safety

    target = tmp_path / "sample.py"
    target.write_text("print('hello')")

    def unreadable(*args):
        raise OSError("unreadable")

    monkeypatch.setattr(safety, "_read_text_file", unreadable)
    result = run_safety_scan(str(target), cwd=tmp_path)
    assert (result["scanned_files"], result["total_scannable"]) == (0, 1)
    assert result["source"].startswith("error:")


def test_empty_corpus_never_prints_zero_over_zero(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    output = runner.invoke(app, ["safe", "--quiet"])
    assert "0/unknown files observed" in output.output
