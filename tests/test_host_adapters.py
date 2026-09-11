import json
from pathlib import Path

import pytest

from hyodo.events import (
    EVENT_ID_NEW,
    append_agent_event,
    check_event_id,
    validate_event,
)
from hyodo.host_adapters.codex import map_codex_hook_payload
from hyodo.host_adapters.codex_response import map_codex_permission_response
from hyodo.host_adapters.cursor import map_cursor_hook_payload
from hyodo.host_adapters.cursor_response import map_cursor_permission_response
from hyodo.policy import PolicyDecision


def _cursor(event: str = "preToolUse") -> dict[str, object]:
    return {
        "hook_event_name": event,
        "conversation_id": "cursor-session",
        "tool_name": "Shell",
        "tool_input": {"command": "printf safe"},
        "cwd": "/tmp/project",
        "duration": 42,
    }


def _codex(event: str = "PreToolUse") -> dict[str, object]:
    return {
        "hook_event_name": event,
        "session_id": "codex-session",
        "tool_use_id": "tool-1",
        "tool_name": "Bash",
        "tool_input": {"command": "printf safe"},
        "cwd": "/tmp/project",
    }


def test_cursor_native_pre_and_post_events_are_canonical() -> None:
    pre, error = map_cursor_hook_payload(_cursor(), Path("/tmp"))
    assert error is None
    assert pre is not None
    assert pre.raw["kind"] == "tool_call"
    assert "host:cursor" in pre.raw["meta"]["tags"]
    assert validate_event(pre.raw)[0] is True

    post, error = map_cursor_hook_payload(_cursor("postToolUse"), Path("/tmp"))
    assert error is None
    assert post is not None
    assert post.raw["kind"] == "tool_result"


def test_cursor_specialized_hook_can_correlate_without_native_tool_id() -> None:
    event, error = map_cursor_hook_payload(_cursor("beforeShellExecution"), Path("/tmp"))
    assert error is None
    assert event is not None
    assert str(event.raw["event_id"]).startswith("cursor:beforeShellExecution:")


def test_cursor_specialized_hooks_preserve_real_payload_shapes() -> None:
    shell, error = map_cursor_hook_payload(
        {
            "hook_event_name": "beforeShellExecution",
            "conversation_id": "cursor-session",
            "command": "printf shell",
        },
        Path("/tmp"),
    )
    assert error is None
    assert shell is not None
    assert shell.raw["tool"]["args_digest"]

    mcp, error = map_cursor_hook_payload(
        {
            "hook_event_name": "afterMCPExecution",
            "conversation_id": "cursor-session",
            "tool_name": "search",
            "tool_input": '{"query":"hyodo"}',
            "result_json": {"ok": True},
        },
        Path("/tmp"),
    )
    assert error is None
    assert mcp is not None
    assert mcp.raw["kind"] == "tool_result"
    assert mcp.raw["io"]["output_digest"]

    edit, error = map_cursor_hook_payload(
        {
            "hook_event_name": "afterFileEdit",
            "conversation_id": "cursor-session",
            "file_path": "src/main.py",
            "edits": [{"oldString": "a", "newString": "b"}],
        },
        Path("/tmp"),
    )
    assert error is None
    assert edit is not None
    assert edit.raw["tool"]["paths"] == ["src/main.py"]
    assert validate_event(edit.raw)[0] is True


def test_codex_pre_and_post_events_are_canonical() -> None:
    event, error = map_codex_hook_payload(_codex(), Path("/tmp"))
    assert error is None
    assert event is not None
    assert event.raw["kind"] == "tool_call"
    assert validate_event(event.raw)[0] is True

    event, error = map_codex_hook_payload(_codex("PostToolUse"), Path("/tmp"))
    assert error is None
    assert event is not None
    assert event.raw["kind"] == "tool_result"


def test_lifecycle_and_permission_events_remain_explicitly_unobserved() -> None:
    event, error = map_codex_hook_payload(_codex("SubagentStart"), Path("/tmp"))
    assert event is None
    assert error == "unsupported_event:v1_schema:SubagentStart"

    event, error = map_cursor_hook_payload(_cursor("subagentStart"), Path("/tmp"))
    assert event is None
    assert error == "unsupported_lifecycle_event:v1_schema"


def test_malformed_payloads_are_not_green() -> None:
    event, error = map_codex_hook_payload({}, Path("/tmp"))
    assert event is None
    assert error == "missing_field:session_id"


def test_event_record_accepts_cursor_native_stdin(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from hyodo.cli import main as cli

    payload = _cursor()
    payload["cwd"] = str(tmp_path)
    result = CliRunner().invoke(
        cli.app,
        ["event", "record", "--stdin", "--hook", "cursor", "--root", str(tmp_path), "--json"],
        input=json.dumps(payload),
    )
    assert result.exit_code == 0
    receipt = json.loads(result.stdout)
    assert receipt["ok"] is True
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    recorded = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])
    assert "host:cursor" in recorded["meta"]["tags"]


def test_cursor_permission_response_maps_all_decisions_fail_closed() -> None:
    for decision_name, permission in (
        ("ALLOW", "allow"),
        ("DENY", "deny"),
        ("ASK", "ask"),
        ("UNOBSERVED", "deny"),
    ):
        response = map_cursor_permission_response(
            PolicyDecision(decision_name, "rule", "reason"), event_name="preToolUse"
        )
        assert response["permission"] == permission
    assert "updated_input" not in map_cursor_permission_response(
        PolicyDecision("ALLOW", None, None), event_name="beforeShellExecution"
    )


def test_cursor_permission_response_allows_explicit_pretool_rewrite_only() -> None:
    response = map_cursor_permission_response(
        PolicyDecision("ALLOW", None, None),
        event_name="preToolUse",
        updated_input={"command": "npm test"},
    )
    assert response["updated_input"] == {"command": "npm test"}

    with pytest.raises(ValueError, match="updated_input_only_supported_for:preToolUse"):
        map_cursor_permission_response(
            PolicyDecision("ALLOW", None, None),
            event_name="beforeShellExecution",
            updated_input={"command": "npm test"},
        )


def test_codex_permission_response_maps_pretool_and_permission_request() -> None:
    denied = map_codex_permission_response(
        PolicyDecision("UNOBSERVED", None, "policy_missing"), event_name="PreToolUse"
    )
    assert denied["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert denied["hookSpecificOutput"]["permissionDecisionReason"]

    allowed = map_codex_permission_response(
        PolicyDecision("ALLOW", None, None),
        event_name="PreToolUse",
        updated_input={"command": "echo rewritten"},
    )
    assert allowed["hookSpecificOutput"]["permissionDecision"] == "allow"
    assert allowed["hookSpecificOutput"]["updatedInput"] == {"command": "echo rewritten"}

    requested = map_codex_permission_response(
        PolicyDecision("DENY", "rule", "blocked"), event_name="PermissionRequest"
    )
    assert requested["hookSpecificOutput"]["decision"]["behavior"] == "deny"


def test_policy_check_can_emit_cursor_native_response(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    policy_dir = tmp_path / ".hyodo"
    policy_dir.mkdir()
    (policy_dir / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\nallowed_tools = ["Shell"]\n',
        encoding="utf-8",
    )
    payload = _cursor("beforeShellExecution")
    payload["cwd"] = str(tmp_path)
    from hyodo.cli.main import app

    result = CliRunner().invoke(
        app,
        [
            "policy",
            "check",
            "--stdin",
            "--hook",
            "cursor",
            "--native-response",
            "--json",
            "--root",
            str(tmp_path),
        ],
        input=json.dumps(payload),
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"permission": "allow"}


def _codex_ids(event: str) -> str:
    mapped, error = map_codex_hook_payload(_codex(event), Path("/tmp"))
    assert error is None
    assert mapped is not None
    return str(mapped.raw["event_id"])


def _cursor_with_tool_id(event: str) -> dict[str, object]:
    """Cursor payload where the host *does* supply a tool id.

    The bare ``_cursor`` fixture omits ``tool_use_id`` and therefore exercises the
    digest fallback, which already carries the event name. Only the host-supplied
    id path can collide.
    """
    payload = _cursor(event)
    payload["tool_use_id"] = "cursor-tool-1"
    return payload


def test_codex_tool_call_and_tool_result_get_distinct_event_ids() -> None:
    """One Codex tool call emits two canonical events; they must not share an id."""
    assert _codex_ids("PreToolUse") != _codex_ids("PostToolUse")


def test_cursor_host_supplied_tool_id_still_separates_call_from_result() -> None:
    pre, error = map_cursor_hook_payload(_cursor_with_tool_id("preToolUse"), Path("/tmp"))
    assert error is None
    assert pre is not None
    post, error = map_cursor_hook_payload(_cursor_with_tool_id("postToolUse"), Path("/tmp"))
    assert error is None
    assert post is not None
    assert pre.raw["kind"] == "tool_call"
    assert post.raw["kind"] == "tool_result"
    assert pre.raw["event_id"] != post.raw["event_id"]


def test_both_tool_call_and_tool_result_reach_the_ledger(tmp_path: Path) -> None:
    """The end-to-end guard: a single tool call must leave two ledger lines.

    Mapping alone never surfaced the collision because no test recorded both
    halves of one tool call. The idempotency check refuses the second write when
    the ids match, so half the observation spine was dropped in silence.
    """
    for event_name in ("PreToolUse", "PostToolUse"):
        mapped, error = map_codex_hook_payload(_codex(event_name), tmp_path)
        assert error is None
        assert mapped is not None
        assert check_event_id(tmp_path, mapped.raw) == EVENT_ID_NEW
        assert append_agent_event(tmp_path, mapped.raw) is True

    recorded = [
        json.loads(line)
        for line in (tmp_path / ".hyodo" / "agent-events.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
        if line.strip()
    ]
    assert [event["kind"] for event in recorded] == ["tool_call", "tool_result"]


# --- Codex `tool_response` is the host's name for the tool result -----------
#
# Measured against codex-cli 0.154.0: a real PostToolUse payload carries the
# result as `tool_response`, a string. The adapter looked for `output` and
# `result_json`, so every live result was dropped and `io.output_digest` read
# null. The fixture never caught it because it sends no result field at all.


def _codex_post_with_response(response: object) -> dict[str, object]:
    payload = _codex("PostToolUse")
    payload["tool_response"] = response
    return payload


def test_codex_tool_response_becomes_the_output_digest() -> None:
    mapped, error = map_codex_hook_payload(_codex_post_with_response("ok"), Path("/tmp"))

    assert error is None
    assert mapped is not None
    assert mapped.raw["io"]["output_digest"]


def test_the_raw_response_never_reaches_the_canonical_event() -> None:
    """A digest, not the text. The privacy contract does not change here."""
    secret = "s3cr3t-value-the-host-returned"
    mapped, _ = map_codex_hook_payload(_codex_post_with_response(secret), Path("/tmp"))

    assert mapped is not None
    assert secret not in json.dumps(mapped.raw)
    assert mapped.raw["io"]["output_digest"] != secret


def test_a_tool_call_never_carries_a_result_digest() -> None:
    """`PreToolUse` is the call. A result on it would be a claim about the future."""
    payload = _codex("PreToolUse")
    payload["tool_response"] = "somehow present"

    mapped, _ = map_codex_hook_payload(payload, Path("/tmp"))

    assert mapped is not None
    assert mapped.raw["kind"] == "tool_call"
    assert "output_digest" not in mapped.raw.get("io", {})


def test_output_and_result_json_hosts_do_not_regress() -> None:
    """Cursor's existing result fields keep working."""
    mcp = _cursor("afterMCPExecution")
    mcp["result_json"] = {"ok": True}
    mapped, _ = map_cursor_hook_payload(mcp, Path("/tmp"))

    assert mapped is not None
    assert mapped.raw["io"]["output_digest"]


def test_tool_response_is_a_codex_reading_not_a_universal_one() -> None:
    """`_common` must not assume every host means a result by `tool_response`.

    Cursor has its own vocabulary. Teaching the shared mapper that this field
    is a result everywhere would be a guess about hosts nobody measured.
    """
    payload = _cursor("postToolUse")
    payload["tool_response"] = "cursor did not promise this means a result"

    mapped, _ = map_cursor_hook_payload(payload, Path("/tmp"))

    assert mapped is not None
    assert "output_digest" not in mapped.raw.get("io", {})
