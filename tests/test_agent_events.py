"""TDD for FDE Evidence Spine: agent event ledger + policy gate.

Covers ``hyodo.events`` / ``hyodo.policy`` and CLI:
``hyodo event validate|record``, ``hyodo policy check``.

Exit contract (PRD):
- event validate/record: 0 ok, 1 invalid or DENY, 2 unreadable/unobserved config
- policy check: 0 ALLOW, 1 DENY, 2 unobserved (missing/invalid policy)
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import (
    AGENT_EVENT_SCHEMA_VERSION,
    AGENT_EVENTS_RELATIVE_PATH,
    append_agent_event,
    content_digest,
    read_agent_events,
    strip_full_bodies,
    validate_event,
)
from hyodo.policy import (
    POLICY_SCHEMA_ID,
    PolicyConfig,
    evaluate_policy,
    load_policy_config,
    try_load_policy,
)

runner = CliRunner()


def _eid() -> str:
    return str(uuid.uuid4())


def _valid_event(**overrides: object) -> dict:
    base: dict = {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": _eid(),
        "run_id": _eid(),
        "ts": "2026-07-21T12:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {"name": "search", "args_digest": content_digest('{"q":"x"}'), "paths": []},
        "io": {
            "input_digest": content_digest("in"),
            "output_digest": None,
            "bytes_in": 2,
            "bytes_out": 0,
        },
        "policy": {"decision": None, "rule_id": None, "reason": None},
        "meta": {"model": "test-model", "tags": ["unit"]},
    }
    base.update(overrides)
    return base


def _write_policy(root: Path, body: str) -> Path:
    path = root / ".hyodo" / "policy.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Schema unit (T1.1-T1.4)
# --------------------------------------------------------------------------- #


def test_validate_missing_event_id():
    event = _valid_event()
    del event["event_id"]
    ok, reasons, normalized = validate_event(event)
    assert ok is False
    assert normalized is None
    assert any(r == "missing_field:event_id" for r in reasons)


def test_validate_unknown_kind():
    ok, reasons, normalized = validate_event(_valid_event(kind="teleport"))
    assert ok is False
    assert normalized is None
    assert "invalid_kind" in reasons


def test_validate_valid_tool_call_round_trip():
    raw = _valid_event()
    ok, reasons, normalized = validate_event(raw)
    assert ok is True
    assert reasons == []
    assert normalized is not None
    assert normalized["schema_version"] == AGENT_EVENT_SCHEMA_VERSION
    assert normalized["kind"] == "tool_call"
    assert normalized["tool"]["name"] == "search"
    # Round-trip via JSON is stable for ledger write.
    again = json.loads(json.dumps(normalized, sort_keys=True))
    ok2, _, norm2 = validate_event(again)
    assert ok2 is True
    assert norm2 == normalized


def test_digest_from_full_body_and_strip():
    raw = _valid_event(
        io={
            "input_text": "secret-customer-prompt",
            "output_text": "model-out",
            "bytes_in": 21,
            "bytes_out": 9,
        }
    )
    ok, _, normalized = validate_event(raw)
    assert ok is True
    assert normalized is not None
    assert normalized["io"]["input_digest"] == content_digest("secret-customer-prompt")
    assert "input_text" in normalized["io"]
    stripped = strip_full_bodies(normalized)
    assert "input_text" not in stripped["io"]
    assert "output_text" not in stripped["io"]
    assert stripped["io"]["input_digest"] == content_digest("secret-customer-prompt")


# --------------------------------------------------------------------------- #
# Ledger unit (T1.5-T1.8)
# --------------------------------------------------------------------------- #


def test_append_and_read_agent_events(tmp_path: Path):
    event = validate_event(_valid_event())[2]
    assert event is not None
    assert append_agent_event(tmp_path, event) is True
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert len(events) == 1
    assert events[0]["event_id"] == event["event_id"]
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    assert ledger.is_file()
    # One line, valid JSON.
    lines = ledger.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    json.loads(lines[0])


def test_append_unwritable_returns_false(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    event = validate_event(_valid_event())[2]
    assert event is not None

    def boom(*_a, **_k):
        raise OSError("read-only")

    monkeypatch.setattr(Path, "mkdir", boom)
    assert append_agent_event(tmp_path, event) is False


def test_corrupt_middle_line_counted(tmp_path: Path):
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    good1 = validate_event(_valid_event())[2]
    good2 = validate_event(_valid_event(step_index=1))[2]
    assert good1 is not None
    assert good2 is not None
    ledger.write_text(
        json.dumps(good1, sort_keys=True)
        + "\n"
        + "{not-json\n"
        + json.dumps(good2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 1
    assert len(events) == 2


def test_agent_events_path_separate_from_history():
    history = Path(".hyodo") / "history.jsonl"
    assert history != AGENT_EVENTS_RELATIVE_PATH
    assert AGENT_EVENTS_RELATIVE_PATH.name == "agent-events.jsonl"


# --------------------------------------------------------------------------- #
# Policy unit (T1.9-T1.13)
# --------------------------------------------------------------------------- #


def test_policy_tool_not_allowed():
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=10,
        allowed_tools=("search",),
        blocked_path_globs=(),
    )
    event = validate_event(_valid_event(tool={"name": "shell", "args_digest": None, "paths": []}))[
        2
    ]
    assert event is not None
    decision = evaluate_policy(event, policy)
    assert decision.decision == "DENY"
    assert decision.rule_id == "tool_not_allowed"


def test_policy_max_steps():
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=2,
        allowed_tools=None,
        blocked_path_globs=(),
    )
    event = validate_event(_valid_event(step_index=3, kind="prompt"))[2]
    assert event is not None
    decision = evaluate_policy(event, policy)
    assert decision.decision == "DENY"
    assert decision.rule_id == "max_steps"


def test_policy_data_boundary():
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=None,
        allowed_tools=None,
        blocked_path_globs=("**/.env", "**/secrets/**"),
    )
    event = validate_event(
        _valid_event(
            tool={
                "name": "read_file",
                "args_digest": content_digest("/app/secrets/key"),
                "paths": ["/app/secrets/key.pem"],
            }
        )
    )[2]
    assert event is not None
    decision = evaluate_policy(event, policy)
    assert decision.decision == "DENY"
    assert decision.rule_id == "data_boundary"


def test_policy_missing_is_unobserved(tmp_path: Path):
    cfg, err = try_load_policy(tmp_path / ".hyodo" / "policy.toml")
    assert cfg is None
    assert err == "policy_missing"


def test_policy_load_and_allow(tmp_path: Path):
    path = _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
max_steps = 5
allowed_tools = ["search", "read_file"]
blocked_path_globs = ["**/.env"]
''',
    )
    policy = load_policy_config(path)
    event = validate_event(_valid_event(step_index=1))[2]
    assert event is not None
    decision = evaluate_policy(event, policy)
    assert decision.decision == "ALLOW"


# --------------------------------------------------------------------------- #
# CLI contracts
# --------------------------------------------------------------------------- #


def test_cli_event_validate_ok_and_fail(tmp_path: Path):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(_valid_event()), encoding="utf-8")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"kind": "tool_call"}), encoding="utf-8")

    ok = runner.invoke(app, ["event", "validate", "--file", str(good)])
    assert ok.exit_code == 0

    fail = runner.invoke(app, ["event", "validate", "--file", str(bad)])
    assert fail.exit_code == 1
    assert (
        "missing_field" in fail.output
        or "MISSING" in fail.output.upper()
        or "invalid" in fail.output.lower()
    )


def test_cli_event_record_digest_default(tmp_path: Path):
    raw = _valid_event(
        io={
            "input_text": "do-not-store-by-default",
            "bytes_in": 24,
            "bytes_out": 0,
        }
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(raw), encoding="utf-8")

    result = runner.invoke(
        app,
        ["event", "record", "--file", str(event_path), "--root", str(tmp_path)],
    )
    assert result.exit_code == 0
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert len(events) == 1
    assert "input_text" not in events[0].get("io", {})
    assert events[0]["io"]["input_digest"] == content_digest("do-not-store-by-default")


def test_cli_event_record_full_body_opt_in(tmp_path: Path):
    raw = _valid_event(
        io={
            "input_text": "keep-me",
            "bytes_in": 7,
            "bytes_out": 0,
        }
    )
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(raw), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event_path),
            "--root",
            str(tmp_path),
            "--full-body",
        ],
    )
    assert result.exit_code == 0
    events, _ = read_agent_events(tmp_path)
    assert events[0]["io"]["input_text"] == "keep-me"


def test_cli_event_record_with_policy_deny(tmp_path: Path):
    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
max_steps = 10
allowed_tools = ["search"]
''',
    )
    raw = _valid_event(tool={"name": "shell", "args_digest": None, "paths": []})
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(raw), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event_path),
            "--root",
            str(tmp_path),
            "--policy",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    assert result.exit_code == 1
    events, _ = read_agent_events(tmp_path)
    assert len(events) == 1
    assert events[0]["policy"]["decision"] == "DENY"
    assert events[0]["policy"]["rule_id"] == "tool_not_allowed"


def test_cli_policy_check_allow_deny_unobserved(tmp_path: Path):
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(_valid_event()), encoding="utf-8")

    missing = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(event_path),
            "--config",
            str(tmp_path / "nope.toml"),
        ],
    )
    assert missing.exit_code == 2

    _write_policy(
        tmp_path,
        f'''schema = "{POLICY_SCHEMA_ID}"
allowed_tools = ["search"]
''',
    )
    allow = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(event_path),
            "--config",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    assert allow.exit_code == 0
    assert "ALLOW" in allow.output

    deny_event = tmp_path / "deny.json"
    deny_event.write_text(
        json.dumps(_valid_event(tool={"name": "shell", "args_digest": None, "paths": []})),
        encoding="utf-8",
    )
    deny = runner.invoke(
        app,
        [
            "policy",
            "check",
            "--file",
            str(deny_event),
            "--config",
            str(tmp_path / ".hyodo" / "policy.toml"),
        ],
    )
    assert deny.exit_code == 1
    assert "DENY" in deny.output


def test_cli_event_record_missing_file_exit_2(tmp_path: Path):
    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(tmp_path / "missing.json"),
            "--root",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 2
