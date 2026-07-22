"""Regression: a caller must not be able to assert its own policy evidence.

The trust boundary these tests pin down is the whole point of the ledger — HyoDo is
supposed to record what *it* measured, not what the audited agent claims about itself.
Deleting any of these is a gate weakening, not a cleanup.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    AGENT_EVENTS_RELATIVE_PATH,
    content_digest,
    count_run_events,
    validate_event,
)
from hyodo.policy import (
    POLICY_SCHEMA_ID,
    PolicyConfig,
    _path_blocked,
    apply_decision_to_event,
    evaluate_policy,
)
from hyodo.report import render_report


def _event(**overrides: object) -> dict:
    base: dict = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": str(uuid.uuid4()),
        "run_id": "run-fixed",
        "ts": "2026-07-22T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {"name": "search", "args_digest": content_digest("{}"), "paths": []},
        "io": {"input_digest": content_digest("in"), "output_digest": None},
        "meta": {"model": "test-model", "tags": ["unit"]},
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------- #
# Caller-asserted policy decisions
# --------------------------------------------------------------------------- #


def test_caller_asserted_allow_is_not_a_decision():
    ok, reasons, normalized = validate_event(
        _event(policy={"decision": "ALLOW", "reason": "trust me"})
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["policy"]["decision"] is None
    assert normalized["policy"]["evaluated_by"] is None
    assert normalized["policy"]["reason"] == "unevaluated"


def test_caller_assertion_is_preserved_for_audit():
    """The claim is quarantined, not deleted — it loses authority, not existence."""
    _, _, normalized = validate_event(_event(policy={"decision": "ALLOW", "reason": "trust me"}))
    assert normalized is not None
    assert normalized["policy"]["claimed"] == {
        "decision": "ALLOW",
        "rule_id": None,
        "reason": "trust me",
    }


def test_measured_decision_carries_provenance():
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID, max_steps=None, allowed_tools=None, blocked_path_globs=()
    )
    _, _, normalized = validate_event(_event())
    assert normalized is not None
    stamped = apply_decision_to_event(normalized, evaluate_policy(normalized, policy))
    assert stamped["policy"]["decision"] == "ALLOW"
    assert stamped["policy"]["evaluated_by"] == POLICY_SCHEMA_ID


def test_report_does_not_count_caller_asserted_allow(tmp_path: Path):
    """The forged ALLOW must not reach the human sign-off tally."""
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    _, _, forged = validate_event(_event(policy={"decision": "ALLOW"}))
    assert forged is not None
    ledger.write_text(json.dumps(forged) + "\n", encoding="utf-8")

    text, _digest, _meta = render_report(tmp_path, "md")
    assert "ALLOW: 0" in text
    assert "Unevaluated by HyoDo (caller-asserted or no policy run): 1" in text


# --------------------------------------------------------------------------- #
# Ledger-backed step budget
# --------------------------------------------------------------------------- #


def test_count_run_events_distinguishes_missing_from_unreadable(tmp_path: Path):
    assert count_run_events(tmp_path, "run-fixed") == 0  # nothing recorded yet = honest zero

    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    _, _, ev = validate_event(_event())
    assert ev is not None
    ledger.write_text(json.dumps(ev) + "\n", encoding="utf-8")
    assert count_run_events(tmp_path, "run-fixed") == 1
    assert count_run_events(tmp_path, "other-run") == 0

    ledger.chmod(0o000)
    try:
        # Unreadable must be None (unobserved), never 0 — 0 would buy a free ALLOW.
        assert count_run_events(tmp_path, "run-fixed") is None
    finally:
        ledger.chmod(0o644)


# --------------------------------------------------------------------------- #
# blocked_path_globs — the shipped example patterns must actually block
# --------------------------------------------------------------------------- #


def test_shipped_example_globs_block_root_level_paths():
    """`**/X` is documented as recursive; fnmatch alone misses depth zero."""
    for pattern, path in [
        ("**/.env", ".env"),
        ("**/.env", "./.env"),
        ("**/.env", "app/.env"),
        ("**/secrets/**", "secrets/key.txt"),
        ("**/secrets/**", "nested/secrets/key.txt"),
        ("**/id_rsa", "id_rsa"),
        ("**/*.pem", "key.pem"),
    ]:
        assert _path_blocked(path, (pattern,)) == pattern, f"{pattern} failed to block {path}"


def test_glob_fix_does_not_overblock():
    harmless = ["README.md", "src/env_utils.py", "docs/secretsauce.md", "notes.txt"]
    globs = ("**/.env", "**/secrets/**", "**/id_rsa", "**/*.pem")
    for path in harmless:
        assert _path_blocked(path, globs) is None, f"{path} should not be blocked"
