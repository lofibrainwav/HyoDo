"""TDD for FDE Evidence Spine: agent event ledger + policy gate.

Covers ``hyodo.events`` / ``hyodo.policy`` and CLI:
``hyodo event validate|record``, ``hyodo policy check``.

Exit contract (PRD):
- event validate/record: 0 ok, 1 invalid or DENY, 2 unreadable/unobserved config
- policy check: 0 ALLOW, 1 DENY, 2 unobserved (missing/invalid policy)
"""

from __future__ import annotations

import json
import stat
import sys
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


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file mode bits only")
def test_ledger_file_is_owner_only_readable(tmp_path: Path):
    """The agent-event ledger holds sensitive prompt/response digests (and,
    opt-in, full bodies) — it must never be group/world readable regardless
    of the process umask."""
    event = validate_event(_valid_event())[2]
    assert event is not None
    assert append_agent_event(tmp_path, event) is True
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    mode = stat.S_IMODE(ledger.stat().st_mode)
    assert mode == 0o600, f"ledger mode is {oct(mode)}, expected 0o600"


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


def test_validate_tool_method_normalizes_case():
    ok, reasons, normalized = validate_event(
        _valid_event(tool={"name": "web_fetch", "args_digest": None, "paths": [], "method": "get"})
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["method"] == "GET"


def test_validate_tool_method_rejects_unknown_verb():
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={"name": "web_fetch", "args_digest": None, "paths": [], "method": "TRACE"}
        )
    )
    assert not ok
    assert normalized is None
    assert "invalid_field:tool.method" in reasons


def test_validate_tool_method_defaults_to_none():
    ok, reasons, normalized = validate_event(_valid_event())
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["method"] is None


def test_validate_tool_urls_round_trip():
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={
                "name": "web_fetch",
                "args_digest": None,
                "paths": [],
                "urls": [{"domain": "api.example.com", "path": "/v1/users"}],
            }
        )
    )
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["urls"] == [
        {
            "domain": "api.example.com",
            "digest": content_digest("/v1/users"),
            "credential_shaped": False,
        }
    ]


def test_validate_tool_urls_defaults_to_empty_list():
    ok, reasons, normalized = validate_event(_valid_event())
    assert ok, reasons
    assert normalized is not None
    assert normalized["tool"]["urls"] == []


def test_validate_tool_urls_requires_domain():
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={
                "name": "web_fetch",
                "args_digest": None,
                "paths": [],
                "urls": [{"path": "/v1/users"}],
            }
        )
    )
    assert not ok
    assert normalized is None
    assert "invalid_field:tool.urls" in reasons


def test_validate_event_edge_fields_are_optional_and_round_trip():
    ok, reasons, parent = validate_event(_valid_event(event_id="parent-1"))
    assert ok, reasons
    assert parent is not None

    ok, reasons, child = validate_event(
        _valid_event(parent_event_id=" parent-1 ", evidence_refs=[" parent-1 "])
    )
    assert ok, reasons
    assert child is not None
    assert child["parent_event_id"] == "parent-1"
    assert child["evidence_refs"] == ["parent-1"]

    again = json.loads(json.dumps(child, sort_keys=True))
    ok2, reasons2, normalized_again = validate_event(again)
    assert ok2, reasons2
    assert normalized_again == child


def test_validate_event_edge_fields_reject_invalid_shapes():
    ok, reasons, normalized = validate_event(_valid_event(parent_event_id=""))
    assert not ok
    assert normalized is None
    assert "invalid_field:parent_event_id" in reasons

    ok, reasons, normalized = validate_event(_valid_event(evidence_refs="not-a-list"))
    assert not ok
    assert normalized is None
    assert "invalid_field:evidence_refs" in reasons


def test_validate_event_actor_id_absent_normalizes_to_none():
    ok, reasons, normalized = validate_event(_valid_event())
    assert ok, reasons
    assert normalized is not None
    assert normalized["actor_id"] is None


def test_validate_event_actor_id_null_normalizes_to_none():
    ok, reasons, normalized = validate_event(_valid_event(actor_id=None))
    assert ok, reasons
    assert normalized is not None
    assert normalized["actor_id"] is None


def test_validate_event_actor_id_accepts_a_valid_label():
    ok, reasons, normalized = validate_event(_valid_event(actor_id="planner-01"))
    assert ok, reasons
    assert normalized is not None
    assert normalized["actor_id"] == "planner-01"


def test_validate_event_actor_id_accepts_a_uuid_shaped_session_id():
    session_id = str(uuid.uuid4())
    ok, reasons, normalized = validate_event(_valid_event(actor_id=session_id))
    assert ok, reasons
    assert normalized["actor_id"] == session_id


def test_validate_event_actor_id_rejects_empty_string():
    ok, reasons, normalized = validate_event(_valid_event(actor_id=""))
    assert not ok
    assert normalized is None
    assert "invalid_field:actor_id" in reasons


def test_validate_event_actor_id_rejects_disallowed_characters():
    ok, reasons, normalized = validate_event(_valid_event(actor_id="seat name!"))
    assert not ok
    assert normalized is None
    assert "invalid_field:actor_id" in reasons


def test_validate_event_actor_id_rejects_non_string():
    ok, reasons, normalized = validate_event(_valid_event(actor_id=123))
    assert not ok
    assert normalized is None
    assert "invalid_field:actor_id" in reasons


def test_validate_event_actor_id_rejects_over_64_chars():
    ok, reasons, normalized = validate_event(_valid_event(actor_id="a" * 65))
    assert not ok
    assert normalized is None
    assert "invalid_field:actor_id" in reasons


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
    """Budget is spent against the ledger count, not the caller's step_index.

    The previous version of this test asserted that a self-reported ``step_index=3``
    was enough to DENY. That was the bug: a caller that keeps sending ``step_index: 0``
    never trips the budget. The authoritative number is ``observed_steps``.
    """
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=2,
        allowed_tools=None,
        blocked_path_globs=(),
    )
    event = validate_event(_valid_event(step_index=3, kind="prompt"))[2]
    assert event is not None
    decision = evaluate_policy(event, policy, observed_steps=2)
    assert decision.decision == "DENY"
    assert decision.rule_id == "max_steps"


def test_policy_max_steps_ignores_self_reported_step_index():
    """A caller replaying step_index=0 forever must still exhaust the budget."""
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=2,
        allowed_tools=None,
        blocked_path_globs=(),
    )
    event = validate_event(_valid_event(step_index=0, kind="prompt"))[2]
    assert event is not None
    seen = [evaluate_policy(event, policy, observed_steps=n).decision for n in range(4)]
    assert seen == ["ALLOW", "ALLOW", "DENY", "DENY"]

    # A huge self-reported index must not DENY on its own either — only the ledger counts.
    liar = validate_event(_valid_event(step_index=9999, kind="prompt"))[2]
    assert liar is not None
    assert evaluate_policy(liar, policy, observed_steps=0).decision == "ALLOW"


def test_policy_max_steps_unobserved_ledger_is_not_allow():
    """Unenforceable is not permitted: no ledger count means UNOBSERVED, never ALLOW."""
    policy = PolicyConfig(
        schema=POLICY_SCHEMA_ID,
        max_steps=2,
        allowed_tools=None,
        blocked_path_globs=(),
    )
    event = validate_event(_valid_event(step_index=0, kind="prompt"))[2]
    assert event is not None
    decision = evaluate_policy(event, policy, observed_steps=None)
    assert decision.decision == "UNOBSERVED"
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
    # max_steps is set, so the ledger count must be supplied; without it the honest
    # answer is UNOBSERVED, not ALLOW.
    decision = evaluate_policy(event, policy, observed_steps=0)
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


@pytest.mark.parametrize("level", [2, 3])
@pytest.mark.parametrize("append_ok", [True, False])
def test_event_record_json_includes_ledger_obligation_at_trust_level_2(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, level: int, append_ok: bool
):
    from hyodo.policy_trust import grant_policy_trust

    policy = _write_policy(
        tmp_path, 'schema = "hyodo.policy/v1"\nask_tools = ["send_email"]\n[trust]\nmax_level = 3\n'
    )
    grant_policy_trust(tmp_path, level, by="human:test")
    if not append_ok:
        monkeypatch.setattr("hyodo.cli.main.append_agent_event", lambda *_: False)
    event = tmp_path / "event.json"
    event.write_text(
        json.dumps(_valid_event(tool={"name": "send_email", "args_digest": None, "paths": []})),
        encoding="utf-8",
    )
    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--file",
            str(event),
            "--root",
            str(tmp_path),
            "--policy",
            str(policy),
            "--json",
        ],
    )
    assert result.exit_code == (0 if append_ok else 2), result.output
    payload = json.loads(result.output)
    assert payload["ledger_write_required"] is True
    assert payload["ledger_written"] is append_ok
    if not append_ok:
        assert payload["reasons"] == ["append_failed"]
        assert not (tmp_path / AGENT_EVENTS_RELATIVE_PATH).exists()
        return
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert len(events) == 1
    assert events[0]["event_id"] == payload["event_id"]


def test_event_record_rejects_broken_parent_edge_without_appending(tmp_path: Path):
    event = _valid_event(event_id="child", parent_event_id="missing-parent")
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")

    result = runner.invoke(
        app,
        ["event", "record", "--root", str(tmp_path), "--file", str(event_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["reasons"] == ["unknown_edge_target:parent_event_id"]
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    assert not ledger.exists()


def test_event_record_actor_id_flag_fills_in_when_json_lacks_one(tmp_path: Path):
    event = _valid_event()
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--root",
            str(tmp_path),
            "--file",
            str(event_path),
            "--actor-id",
            "planner",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert events[0]["actor_id"] == "planner"


def test_event_record_actor_id_flag_does_not_override_an_existing_value(tmp_path: Path):
    event = _valid_event(actor_id="worker")
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps(event), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "event",
            "record",
            "--root",
            str(tmp_path),
            "--file",
            str(event_path),
            "--actor-id",
            "planner",
            "--json",
        ],
    )
    assert result.exit_code == 0, result.output
    events, _corrupt = read_agent_events(tmp_path)
    assert events[0]["actor_id"] == "worker"


def test_event_record_allows_resolved_parent_and_evidence_edges(tmp_path: Path):
    parent = _valid_event(event_id="parent", step_index=0)
    child = _valid_event(
        event_id="child", parent_event_id="parent", evidence_refs=["parent"], step_index=1
    )
    parent_path = tmp_path / "parent.json"
    child_path = tmp_path / "child.json"
    parent_path.write_text(json.dumps(parent), encoding="utf-8")
    child_path.write_text(json.dumps(child), encoding="utf-8")

    first = runner.invoke(
        app,
        ["event", "record", "--root", str(tmp_path), "--file", str(parent_path), "--json"],
    )
    second = runner.invoke(
        app,
        ["event", "record", "--root", str(tmp_path), "--file", str(child_path), "--json"],
    )

    assert first.exit_code == second.exit_code == 0
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert events is not None
    assert [event["event_id"] for event in events] == ["parent", "child"]
    assert events[1]["parent_event_id"] == "parent"
    assert events[1]["evidence_refs"] == ["parent"]


@pytest.mark.parametrize("duration", [0, 1, 2500])
def test_event_duration_ms_is_optional_and_preserved(duration):
    ok, reasons, normalized = validate_event(_valid_event(io={"duration_ms": duration}))
    assert ok, reasons
    assert normalized is not None
    assert normalized["io"]["duration_ms"] == duration


def test_event_duration_ms_rejects_negative_and_boolean_values():
    for duration in (-1, True):
        ok, reasons, _ = validate_event(_valid_event(io={"duration_ms": duration}))
        assert not ok
        assert "invalid_field:io.duration_ms" in reasons


@pytest.mark.parametrize("digest", ["abcdef123456", "BAD", "a" * 13, 12])
def test_url_explicit_digest(digest):
    ok, reasons, normalized = validate_event(
        _valid_event(
            tool={"urls": [{"domain": "example.com", "path": "/private", "digest": digest}]}
        )
    )
    if digest == "abcdef123456":
        assert ok
        assert normalized["tool"]["urls"] == [
            {"domain": "example.com", "digest": digest, "credential_shaped": False}
        ]
    else:
        assert not ok
        assert "invalid_field:tool.urls" in reasons


def test_url_full_body_and_graph_privacy():
    from hyodo.event_graph import build_event_graph

    raw = _valid_event(
        io={"input_text": "body"}, tool={"urls": [{"domain": "example.com", "path": "/private"}]}
    )
    ok, _, event = validate_event(raw)
    assert ok
    assert event["tool"]["urls"][0]["path"] == "/private"
    assert "path" not in strip_full_bodies(event)["tool"]["urls"][0]
    for source in (raw, event, strip_full_bodies(event)):
        url = build_event_graph([source])["nodes"][0]["tool"]["urls"][0]
        assert url == {
            "domain": "example.com",
            "digest": content_digest("/private"),
            "credential_shaped": False,
        }
    assert event["tool"]["urls"][0]["path"] == "/private"


@pytest.mark.parametrize("ref", ["gate:pytest@abcdef0", "gate:x-y.z_1@" + "f" * 64])
def test_gate_reference_record_and_graph(tmp_path, ref):
    from hyodo.event_graph import build_event_graph

    raw = _valid_event(evidence_refs=[ref])
    ok, _, event = validate_event(raw)
    assert ok
    graph = build_event_graph([event])
    assert graph["unresolved_refs"] == []
    assert graph["summary"]["gate_refs"] == 1
    assert graph["edges"][0]["kind"] == "evidence"
    assert graph["edges"][0]["target_kind"] == "gate"
    source = tmp_path / "event.json"
    source.write_text(json.dumps(raw))
    result = runner.invoke(
        app, ["event", "record", "--root", str(tmp_path), "--file", str(source), "--json"]
    )
    assert result.exit_code == 0, result.output
    assert len(read_agent_events(tmp_path)[0]) == 1


@pytest.mark.parametrize(
    "ref", ["gate:x", "gate:x@ABCDEF0", "gate:@abcdef0", "gate:x@abc", "gate:x@" + "a" * 65]
)
def test_malformed_gate_reference(ref):
    ok, reasons, _ = validate_event(_valid_event(evidence_refs=[ref]))
    assert not ok
    assert "invalid_field:evidence_refs" in reasons


def test_unknown_edges_deduplicate_by_field(tmp_path):
    source = tmp_path / "event.json"
    source.write_text(json.dumps(_valid_event(parent_event_id="missing", evidence_refs=["a", "b"])))
    result = runner.invoke(
        app, ["event", "record", "--root", str(tmp_path), "--file", str(source), "--json"]
    )
    assert result.exit_code == 1
    assert json.loads(result.output)["reasons"] == [
        "unknown_edge_target:parent_event_id",
        "unknown_edge_target:evidence_refs",
    ]
    assert not (tmp_path / AGENT_EVENTS_RELATIVE_PATH).exists()


@pytest.mark.parametrize(
    ("entry", "shape"),
    [
        ({}, None),
        ({"credential_shaped": True}, True),
        ({"credential_shaped": False}, False),
        ({"credential_shaped": "false"}, None),
        ({"path": "/.env", "credential_shaped": False}, True),
        ({"path": "/ordinary", "credential_shaped": True}, False),
    ],
)
def test_url_shape_observation_and_missing_digest(entry, shape):
    ok, reasons, event = validate_event(
        _valid_event(tool={"urls": [{"domain": "example.com", **entry}]})
    )
    assert ok, reasons
    url = event["tool"]["urls"][0]
    assert url["credential_shaped"] is shape
    assert url["digest"] == (content_digest(entry["path"]) if "path" in entry else None)
