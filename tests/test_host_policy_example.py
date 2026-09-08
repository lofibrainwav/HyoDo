"""The dual-host allowed_tools copy file is an allowlist, not a hook adapter."""

from __future__ import annotations

from pathlib import Path

from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, content_digest, validate_event
from hyodo.policy import evaluate_policy, load_policy_config

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_POLICY = REPO_ROOT / "examples" / "host-policies" / "claude-and-cursor.policy.toml"
EXAMPLE_README = REPO_ROOT / "examples" / "host-policies" / "README.md"


def _tool_event(name: str) -> dict:
    raw = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": "11111111-1111-4111-8111-111111111111",
        "run_id": "22222222-2222-4222-8222-222222222222",
        "ts": "2026-07-21T20:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {
            "name": name,
            "args_digest": content_digest("{}"),
            "paths": [],
        },
        "io": {
            "input_digest": content_digest("in"),
            "output_digest": None,
            "bytes_in": 2,
            "bytes_out": 0,
        },
        "policy": {"decision": None, "rule_id": None, "reason": None},
    }
    _ok, _reasons, event = validate_event(raw)
    assert event is not None, _reasons
    return event


def test_example_policy_parses_and_allows_both_host_families() -> None:
    policy = load_policy_config(EXAMPLE_POLICY)
    assert policy.allowed_tools is not None
    assert "Read" in policy.allowed_tools
    assert "read_file" in policy.allowed_tools
    assert evaluate_policy(_tool_event("Read"), policy).decision == "ALLOW"
    assert evaluate_policy(_tool_event("read_file"), policy).decision == "ALLOW"
    denied = evaluate_policy(_tool_event("NotARealTool"), policy)
    assert denied.decision == "DENY"
    assert denied.rule_id == "tool_not_allowed"


def test_example_readme_does_not_claim_a_cursor_hook_adapter() -> None:
    text = EXAMPLE_README.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "UNOBSERVED" in text
    assert "not" in lowered
    assert "hook adapter" in lowered
    assert "hyodo connect cursor" in text
