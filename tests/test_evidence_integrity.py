"""Regression: evidence must survive a caller that lies about itself.

Companion to test_policy_self_report_boundary.py. Same trust boundary, later layer —
here the caller controls digests, event ids, declared paths, and MCP privacy flags.
Deleting any of these weakens a gate; none of them are cosmetic.
"""

from __future__ import annotations

import subprocess
import types
import uuid
from pathlib import Path

import pytest

import hyodo.safety as safety
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    AGENT_EVENTS_RELATIVE_PATH,
    EVENT_ID_CONFLICT,
    EVENT_ID_DUPLICATE,
    EVENT_ID_NEW,
    EVENT_ID_UNOBSERVED,
    append_agent_event,
    check_event_id,
    content_digest,
    validate_event,
)
from hyodo.policy import POLICY_SCHEMA_ID, PolicyConfig, evaluate_policy


def _event(**overrides: object) -> dict:
    base: dict = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": "run-fixed",
        "ts": "2026-07-22T12:00:00+00:00",
        "kind": "prompt",
        "step_index": 0,
        "actor": "agent",
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Digest is computed, not accepted
# --------------------------------------------------------------------------- #


def test_body_with_wrong_digest_is_rejected():
    ok, reasons, _ = validate_event(
        _event(io={"input_text": "real content", "input_digest": "aaaaaaaaaaaa"})
    )
    assert ok is False
    assert "digest_mismatch:io.input_digest" in reasons


def test_body_with_correct_digest_passes_and_is_recomputed():
    ok, _reasons, normalized = validate_event(
        _event(io={"input_text": "real content", "input_digest": content_digest("real content")})
    )
    assert ok is True
    assert normalized is not None
    assert normalized["io"]["input_digest"] == content_digest("real content")


def test_digest_only_event_still_accepts_a_supplied_digest():
    """Without a body there is nothing to check against — this must keep working."""
    ok, reasons, normalized = validate_event(_event(io={"input_digest": "abcdef012345"}))
    assert ok is True, reasons
    assert normalized is not None
    assert normalized["io"]["input_digest"] == "abcdef012345"


# --------------------------------------------------------------------------- #
# event_id idempotency
# --------------------------------------------------------------------------- #


def test_event_id_replay_is_idempotent_but_rewrite_is_refused(tmp_path: Path):
    _, _, first = validate_event(_event(event_id="fixed-id"))
    assert first is not None
    assert check_event_id(tmp_path, first) == EVENT_ID_NEW

    assert append_agent_event(tmp_path, first) is True
    assert check_event_id(tmp_path, first) == EVENT_ID_DUPLICATE

    _, _, rewritten = validate_event(_event(event_id="fixed-id", step_index=7))
    assert rewritten is not None
    assert check_event_id(tmp_path, rewritten) == EVENT_ID_CONFLICT


def test_event_id_check_reports_unobserved_when_ledger_unreadable(tmp_path: Path):
    _, _, event = validate_event(_event(event_id="fixed-id"))
    assert event is not None
    append_agent_event(tmp_path, event)
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.chmod(0o000)
    try:
        # Must not fall back to "new" — that would let a rewrite through.
        assert check_event_id(tmp_path, event) == EVENT_ID_UNOBSERVED
    finally:
        ledger.chmod(0o644)


# --------------------------------------------------------------------------- #
# Undeclared paths — opt-in strict mode
# --------------------------------------------------------------------------- #


def _tool_call_without_paths() -> dict:
    _, _, event = validate_event(
        _event(kind="tool_call", tool={"name": "shell", "args_digest": None, "paths": []})
    )
    assert event is not None
    return event


def test_undeclared_paths_allowed_by_default():
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=None,
        allowed_tools=None,
        blocked_path_globs=("**/.env",),
    )
    assert evaluate_policy(_tool_call_without_paths(), policy).decision == "ALLOW"


def test_undeclared_paths_are_unobserved_in_strict_mode():
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=None,
        allowed_tools=None,
        blocked_path_globs=("**/.env",),
        require_declared_paths=True,
    )
    decision = evaluate_policy(_tool_call_without_paths(), policy)
    assert decision.decision == "UNOBSERVED"
    assert decision.rule_id == "data_boundary_undeclared"


# --------------------------------------------------------------------------- #
# External scanner failures are not "clean"
# --------------------------------------------------------------------------- #


@pytest.fixture
def installed_scanner(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pretend the scanner binary exists so we exercise the *ran and failed* path."""
    monkeypatch.setattr(safety.shutil, "which", lambda binary: f"/usr/bin/{binary}")


def _fake_run(returncode: int, stdout: str):
    def run(*_args, **_kwargs):
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    return run


@pytest.mark.usefixtures("installed_scanner")
def test_crashed_scanner_is_high_not_clean(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(137, ""))
    findings, source = safety._run_external_scanner("gitleaks", Path("."), None)
    assert findings[0].severity == "high"  # --strict blocks on high only
    assert findings[0].label == "gitleaks_failed"
    assert source.startswith("error:")


@pytest.mark.usefixtures("installed_scanner")
def test_unparseable_scanner_output_is_high(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(0, "panic: runtime error"))
    findings, source = safety._run_external_scanner("gitleaks", Path("."), None)
    assert findings[0].severity == "high"
    assert findings[0].label == "gitleaks_unparseable"
    assert source.startswith("error:")


@pytest.mark.usefixtures("installed_scanner")
def test_genuinely_clean_scan_stays_info(monkeypatch: pytest.MonkeyPatch):
    """Exit 0 with no output really is clean — do not cry wolf."""
    monkeypatch.setattr(safety.subprocess, "run", _fake_run(0, ""))
    findings, source = safety._run_external_scanner("gitleaks", Path("."), None)
    assert findings[0].severity == "info"
    assert findings[0].label == "gitleaks_clean"
    assert not source.startswith("error:")


def test_missing_binary_stays_medium(monkeypatch: pytest.MonkeyPatch):
    """A tool you never installed is a known gap, not a broken observation."""
    monkeypatch.setattr(safety.shutil, "which", lambda _binary: None)
    _findings, source = safety._run_external_scanner("gitleaks", Path("."), None)
    assert safety.NOT_INSTALLED in source


@pytest.mark.usefixtures("installed_scanner")
def test_scanner_timeout_still_reported_as_error(monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise subprocess.TimeoutExpired(cmd="gitleaks", timeout=120)

    monkeypatch.setattr(safety.subprocess, "run", boom)
    _findings, source = safety._run_external_scanner("gitleaks", Path("."), None)
    assert source.startswith("error:")
    assert safety.NOT_INSTALLED not in source  # timeout is a failure, not an absence
