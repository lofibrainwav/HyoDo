"""Regression test for the trufflehog positive control in ``hyodo.safety``.

Mirrors ``tests/test_safety_gitleaks_adapter.py``: a fake trufflehog
executable is placed first on ``PATH`` so this suite runs in CI without the
real tool installed, exercising ``_run_external_scanner`` end to end.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path

from hyodo.safety import _run_external_scanner

_GOOD_TRUFFLEHOG = """#!/bin/sh
if [ "$1" = "--version" ]; then
  echo "trufflehog 3.63.2" >&2
  exit 0
fi
exit 0
"""

_NO_VERSION_TRUFFLEHOG = """#!/bin/sh
if [ "$1" = "--version" ]; then
  echo "Error: unknown flag: --version" >&2
  exit 1
fi
exit 0
"""

_FINDING_TRUFFLEHOG = """#!/bin/sh
if [ "$1" = "--version" ]; then
  echo "trufflehog 3.63.2" >&2
  exit 0
fi
echo '{"DetectorName":"AWS","Verified":true,"SourceMetadata":{"data":{"filesystem":{"file":"secrets.env","line":5}}}}'
exit 0
"""


def _install_fake_trufflehog(tmp_path: Path, script: str, monkeypatch) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    fake = bin_dir / "trufflehog"
    fake.write_text(script, encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    return fake


def test_clean_scan_reads_version_from_stderr(tmp_path, monkeypatch):
    """trufflehog answers ``--version`` on stderr; that must count as success."""
    _install_fake_trufflehog(tmp_path, _GOOD_TRUFFLEHOG, monkeypatch)

    findings, source = _run_external_scanner("trufflehog", tmp_path)

    assert source.startswith("trufflehog:scan")
    assert "3.63.2" in source
    assert len(findings) == 1
    assert findings[0].severity == "info"
    assert findings[0].label == "trufflehog_clean"


def test_binary_without_version_support_is_a_high_severity_failure(tmp_path, monkeypatch):
    """A binary that cannot answer ``--version`` fails the positive control.

    The scan itself must not be attempted (and cannot be trusted) in this case.
    """
    _install_fake_trufflehog(tmp_path, _NO_VERSION_TRUFFLEHOG, monkeypatch)

    findings, source = _run_external_scanner("trufflehog", tmp_path)

    assert source.startswith("error:")
    assert len(findings) == 1
    assert findings[0].severity == "high"
    assert findings[0].label == "trufflehog_failed"


def test_finding_in_ndjson_output_is_surfaced(tmp_path, monkeypatch):
    """A single JSON-lines finding from a verified secret is reported as high."""
    _install_fake_trufflehog(tmp_path, _FINDING_TRUFFLEHOG, monkeypatch)

    findings, source = _run_external_scanner("trufflehog", tmp_path)

    assert not source.startswith("error:")
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "external_scan"
    assert finding.severity == "high"
    assert finding.label == "trufflehog_finding"
    assert "AWS" in finding.detail
    assert finding.path == "secrets.env"
    assert finding.line == 5
