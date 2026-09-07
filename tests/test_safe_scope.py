"""Tests for the `scope` / `coverage` fields on `run_safety_scan` results.

`hyodo safe` scans one of several corpora (a git diff, git status, a single
file, a directory, or an external scanner) and previously reported only a
free-text `source` string. A reader could not tell, without parsing that
string, which corpus was actually looked at. `scope` names it explicitly and
`coverage` (FULL / PARTIAL / UNOBSERVED) says whether the whole corpus was
read. See docs/SECURITY_SURFACE.md for the full value lists.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

from hyodo.safety import run_safety_scan


def _git_repo(root: Path) -> None:
    env = {
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.com",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.com",
        "PATH": "/usr/bin:/bin",
    }
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    (root / "tracked.py").write_text("value = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "tracked.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=root, check=True, env=env)


def test_diff_scope_reports_diff_for_a_modified_tracked_file(tmp_path: Path):
    """A modified tracked file produces a non-empty `git diff HEAD`, so scope is diff."""
    _git_repo(tmp_path)
    (tmp_path / "tracked.py").write_text("value = 2\n", encoding="utf-8")

    result = run_safety_scan(path=None, cwd=tmp_path)

    assert result["scope"] == "diff"
    assert result["source"] == "git diff HEAD"


def test_directory_scope_partial_when_max_files_caps_below_total(tmp_path: Path):
    """Three scannable files with --max-files 2 caps the read, so coverage is PARTIAL."""
    for i in range(3):
        (tmp_path / f"file_{i}.txt").write_text(f"content {i}\n", encoding="utf-8")

    result = run_safety_scan(path=str(tmp_path), max_files=2, cwd=tmp_path)

    assert result["scope"] == "directory"
    assert result["coverage"] == "PARTIAL"
    assert result["scanned_files"] == 2
    assert result["total_scannable"] == 3


def test_directory_scope_full_when_max_files_unlimited(tmp_path: Path):
    """--max-files 0 (unlimited) reads every scannable file, so coverage is FULL."""
    for i in range(3):
        (tmp_path / f"file_{i}.txt").write_text(f"content {i}\n", encoding="utf-8")

    result = run_safety_scan(path=str(tmp_path), max_files=0, cwd=tmp_path)

    assert result["scope"] == "directory"
    assert result["coverage"] == "FULL"
    assert result["scanned_files"] == 3
    assert result["total_scannable"] == 3


def test_missing_path_scope_none_and_unobserved(tmp_path: Path):
    """A path that does not exist has no corpus at all: scope none, coverage UNOBSERVED."""
    missing = tmp_path / "does-not-exist.txt"

    result = run_safety_scan(path=str(missing), cwd=tmp_path)

    assert result["scope"] == "none"
    assert result["coverage"] == "UNOBSERVED"
    assert result["source"].startswith("missing:")


def test_external_scanner_failure_scope_external_and_unobserved(tmp_path: Path, monkeypatch):
    """A missing scanner binary means the external scan never ran: UNOBSERVED, not clean."""
    import hyodo.safety as safety

    monkeypatch.setattr(safety.shutil, "which", lambda _name: None)

    result = run_safety_scan(scan_tool="gitleaks", cwd=tmp_path)

    assert result["scope"] == "external"
    assert result["coverage"] == "UNOBSERVED"
    assert result["source"].startswith("error:")


def test_external_scanner_success_scope_external_and_full(tmp_path: Path, monkeypatch):
    """A scanner that runs and reports clean is a fully observed external scan."""
    import hyodo.safety as safety

    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")

    def fake_run(cmd, **_kwargs):
        # The adapter first asks `gitleaks version` (positive control), then scans.
        stdout = "8.30.1\n" if "version" in cmd else "[]"
        return type("R", (), {"returncode": 0, "stdout": stdout, "stderr": ""})()

    with patch("hyodo.safety.subprocess.run", side_effect=fake_run):
        result = run_safety_scan(scan_tool="gitleaks", cwd=tmp_path)

    assert result["scope"] == "external"
    assert result["coverage"] == "FULL"
    assert not result["source"].startswith("error:")
