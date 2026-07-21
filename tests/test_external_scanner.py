"""Unit tests for the gitleaks/trufflehog external scanner integration in hyodo.safety.

All external scanners are monkeypatched — gitleaks/trufflehog are never actually
executed here (no external binary dependency for CI).
"""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import hyodo.safety as safety
from hyodo.safety import (
    Finding,
    _result_payload,
    _risk_level_action,
    _run_external_scanner,
    _run_merged_external_scan,
    run_safety_scan,
    summarize_checks,
)


def _fake_run(stdout: str = "", returncode: int = 0):
    """Build a stand-in for subprocess.run's CompletedProcess return value."""

    def _runner(*_args, **_kwargs):
        return SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)

    return _runner


# ---------------------------------------------------------------------------
# _run_external_scanner
# ---------------------------------------------------------------------------


def test_unknown_scanner_returns_error(tmp_path):
    findings, source = _run_external_scanner("nope", tmp_path)
    assert findings == []
    assert source.startswith("error:unknown scanner")


def test_scanner_binary_not_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda _name: None)
    findings, source = _run_external_scanner("gitleaks", tmp_path)
    assert findings == []
    assert "not installed" in source


def test_scanner_clean_run_yields_info_finding(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout=""))

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert source == "gitleaks:scan"
    assert len(findings) == 1
    assert findings[0].category == "external_scan"
    assert findings[0].severity == "info"
    assert findings[0].label == "gitleaks_clean"


def test_gitleaks_json_array_maps_high_and_location(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")
    raw = '[{"Description":"AWS key","File":"a.py","StartLine":3}]'
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout=raw))

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert source == "gitleaks:scan"
    assert len(findings) == 1
    finding = findings[0]
    assert finding.category == "external_scan"
    assert finding.severity == "high"
    assert finding.label == "gitleaks_finding"
    assert "AWS key" in finding.detail
    assert finding.path == "a.py"
    assert finding.line == 3


def test_trufflehog_ndjson_verified_high_unverified_medium(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")
    ndjson = '{"DetectorName":"AWS","Verified":true}\n{"DetectorName":"Slack","Verified":false}\n'
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout=ndjson))

    findings, source = _run_external_scanner("trufflehog", tmp_path)

    assert source == "trufflehog:scan"
    assert len(findings) == 2
    verified, unverified = findings
    assert verified.severity == "high"
    assert "AWS" in verified.detail
    assert unverified.severity == "medium"
    assert "Slack" in unverified.detail


def test_non_json_stdout_yields_info_output_finding(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout="not json at all"))

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert source == "gitleaks:scan"
    assert len(findings) == 1
    assert findings[0].severity == "info"
    assert findings[0].label == "gitleaks_output"


def test_scanner_timeout_reported_as_error(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")

    def _raise_timeout(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd=["gitleaks"], timeout=120)

    monkeypatch.setattr(safety.subprocess, "run", _raise_timeout)

    findings, source = _run_external_scanner("gitleaks", tmp_path)

    assert findings == []
    assert source.startswith("error:gitleaks scan timed out")


# ---------------------------------------------------------------------------
# run_safety_scan (single tool + "all")
# ---------------------------------------------------------------------------


def test_run_safety_scan_single_tool_success_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout=""))

    result = run_safety_scan(scan_tool="gitleaks", cwd=tmp_path)

    for key in ("source", "findings", "rows", "risk_score", "level", "action"):
        assert key in result
    assert result["source"] == "gitleaks:scan"


def test_run_safety_scan_all_merges_both_tools(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout=""))

    result = run_safety_scan(scan_tool="all", cwd=tmp_path)

    assert "+" in result["source"]
    assert len(result["findings"]) == 2
    assert all(f.label.endswith("_clean") for f in result["findings"])


def test_run_safety_scan_all_partial_failure(monkeypatch, tmp_path):
    def _which(name: str):
        return None if name == "gitleaks" else f"/usr/bin/{name}"

    monkeypatch.setattr(safety.shutil, "which", _which)
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(stdout=""))

    result = run_safety_scan(scan_tool="all", cwd=tmp_path)

    unavailable = [f for f in result["findings"] if f.label == "gitleaks_unavailable"]
    assert len(unavailable) == 1
    assert unavailable[0].severity == "medium"
    assert "[partial:" in result["source"]


def test_run_safety_scan_all_total_failure_is_error_source(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda _name: None)

    result = run_safety_scan(scan_tool="all", cwd=tmp_path)

    assert result["source"].startswith("error:")


def test_run_merged_external_scan_directly_total_failure(monkeypatch, tmp_path):
    monkeypatch.setattr(safety.shutil, "which", lambda _name: None)

    result = _run_merged_external_scan(tmp_path, None, strict=False)

    assert result["source"].startswith("error:")
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# _result_payload sanity (used implicitly above, checked directly too)
# ---------------------------------------------------------------------------


def test_result_payload_shape():
    findings = [Finding(category="external_scan", severity="high", label="x", detail="d")]
    payload = _result_payload("gitleaks:scan", findings, strict=False)
    assert payload["risk_score"] == 40
    assert payload["level"] == "high"
    assert payload["findings"] == findings


# ---------------------------------------------------------------------------
# summarize_checks — External scan row
# ---------------------------------------------------------------------------


def test_summarize_checks_external_row_present_when_info_only():
    findings = [
        Finding(category="external_scan", severity="info", label="gitleaks_clean", detail="clean"),
    ]
    rows = summarize_checks(findings)
    external_rows = [r for r in rows if r[0] == "External scan"]
    assert len(external_rows) == 1
    assert external_rows[0][1] == "✅"
    assert external_rows[0][2] == "green"


def test_summarize_checks_external_row_red_when_high_present():
    findings = [
        Finding(category="external_scan", severity="high", label="gitleaks_finding", detail="hit"),
    ]
    rows = summarize_checks(findings)
    external_rows = [r for r in rows if r[0] == "External scan"]
    assert len(external_rows) == 1
    assert external_rows[0][1] == "❌"
    assert external_rows[0][2] == "red"


def test_summarize_checks_no_external_row_when_absent():
    rows = summarize_checks([])
    assert len(rows) == 4
    assert all(r[0] != "External scan" for r in rows)


# ---------------------------------------------------------------------------
# _risk_level_action boundaries
# ---------------------------------------------------------------------------


def test_risk_level_action_low_boundary():
    level, _action = _risk_level_action(0)
    assert level == "low"


def test_risk_level_action_caution_boundary():
    level, _action = _risk_level_action(11)
    assert level == "caution"


def test_risk_level_action_high_boundary():
    level, _action = _risk_level_action(31)
    assert level == "high"
