"""Regression test for the gitleaks CLI-drift fix in ``hyodo.safety``.

gitleaks 8.x removed the ``--format`` flag; the correct contract is
``--report-format json --report-path -``. These tests exercise
``_run_external_scanner`` against a *fake* gitleaks executable placed first on
``PATH`` — no real gitleaks binary is required, so this suite runs in CI
without the tool installed.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from hyodo.safety import _run_external_scanner

_GOOD_GITLEAKS = """#!/bin/sh
if [ "$1" = "version" ]; then
  echo "9.9.9"
  exit 0
fi
for arg in "$@"; do
  if [ "$arg" = "--format" ]; then
    echo "Error: unknown flag: --format" >&2
    exit 126
  fi
done
echo "[]"
exit 0
"""

_NO_VERSION_GITLEAKS = """#!/bin/sh
if [ "$1" = "version" ]; then
  echo "Error: unknown command \\"version\\"" >&2
  exit 1
fi
for arg in "$@"; do
  if [ "$arg" = "--format" ]; then
    echo "Error: unknown flag: --format" >&2
    exit 126
  fi
done
echo "[]"
exit 0
"""

_FINDING_GITLEAKS = """#!/bin/sh
if [ "$1" = "version" ]; then
  echo "9.9.9"
  exit 0
fi
for arg in "$@"; do
  if [ "$arg" = "--format" ]; then
    echo "Error: unknown flag: --format" >&2
    exit 126
  fi
done
echo '[{"RuleID":"aws-access-key","File":"secrets.env","StartLine":5,"Description":"AWS Access Key"}]'
exit 1
"""


def _install_fake_gitleaks(tmp_path: Path, script: str, monkeypatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "gitleaks"
    fake.write_text(script, encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return fake


def test_clean_scan_uses_report_format_flags_not_removed_format_flag(tmp_path, monkeypatch):
    """A gitleaks that rejects `--format` (as 8.x does) must still succeed.

    This is the core regression: the old adapter passed `--format json`,
    which gitleaks 8.30.1 rejects with exit 126. The fake here mirrors that
    real behavior — if the adapter still sends `--format`, the fake exits 126
    and this test fails.
    """
    _install_fake_gitleaks(tmp_path, _GOOD_GITLEAKS, monkeypatch)

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert findings == []
    assert source.startswith("gitleaks:scan")
    assert "9.9.9" in source


def test_binary_without_version_support_is_a_high_severity_failure(tmp_path, monkeypatch):
    """A binary that cannot answer `version` fails the positive control.

    The scan itself must not be attempted (and cannot be trusted) in this case.
    """
    _install_fake_gitleaks(tmp_path, _NO_VERSION_GITLEAKS, monkeypatch)

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert source.startswith("error:")
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].label == "gitleaks_failed"


def test_finding_in_report_json_is_surfaced_with_exit_1(tmp_path, monkeypatch):
    """gitleaks exits 1 when leaks are found — that is a successful scan with
    findings, not a failed scan, and must not be treated as an error."""
    _install_fake_gitleaks(tmp_path, _FINDING_GITLEAKS, monkeypatch)

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert not source.startswith("error:")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "external_scan"
    assert finding.severity == "high"
    assert finding.label == "gitleaks_finding"
    assert "AWS Access Key" in finding.detail
    assert finding.path == "secrets.env"
    assert finding.line == 5
