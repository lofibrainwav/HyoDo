from pathlib import Path

from hyodo.event_graph import build_event_graph
from hyodo.events import append_agent_event, content_digest, validate_event
from hyodo.host_adapters.codex import map_codex_hook_payload, map_codex_prompt_payload


def _prompt(turn_id: str = "turn-1") -> dict[str, object]:
    return {
        "hook_event_name": "UserPromptSubmit",
        "cwd": "/tmp/project",
        "model": "gpt-5-codex",
        "permission_mode": "default",
        "prompt": "효도 대시보드 상태를 확인해 줘",
        "session_id": "codex-session",
        "transcript_path": "/tmp/codex-session.jsonl",
        "turn_id": turn_id,
    }


def test_codex_user_prompt_maps_to_digest_only_human_event() -> None:
    event, error = map_codex_prompt_payload(_prompt(), Path("/tmp"))

    assert error is None
    assert event is not None
    assert event.raw["kind"] == "prompt"
    assert event.raw["actor"] == "human"
    assert event.raw["event_id"] == "codex:UserPromptSubmit:codex-session:turn-1"
    assert event.raw["io"] == {"input_digest": content_digest("효도 대시보드 상태를 확인해 줘")}
    assert "input_text" not in event.raw["io"]
    assert "source:codex-transcript" in event.raw["meta"]["tags"]
    assert (
        f"source-path-digest:{content_digest('/tmp/codex-session.jsonl')}"
        in event.raw["meta"]["tags"]
    )
    assert validate_event(event.raw)[0] is True


def test_codex_hook_dispatches_prompt_without_unresolved_graph_refs() -> None:
    event, error = map_codex_hook_payload(_prompt(), Path("/tmp"))

    assert error is None
    assert event is not None
    ok, reasons, normalized = validate_event(event.raw)
    assert ok is True, reasons
    assert normalized is not None
    graph = build_event_graph([normalized])
    assert graph["unresolved_refs"] == []


def test_codex_pretooluse_links_only_to_a_recorded_matching_prompt(tmp_path: Path) -> None:
    prompt_payload = _prompt("turn-1")
    prompt_payload["cwd"] = str(tmp_path)
    prompt, prompt_error = map_codex_hook_payload(prompt_payload, tmp_path)
    assert prompt_error is None
    assert prompt is not None
    ok, reasons, normalized_prompt = validate_event(prompt.raw)
    assert ok is True, reasons
    assert normalized_prompt is not None
    assert append_agent_event(tmp_path, normalized_prompt) is True

    action_payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(tmp_path),
        "model": "gpt-5-codex",
        "permission_mode": "default",
        "session_id": "codex-session",
        "turn_id": "turn-1",
        "tool_name": "Bash",
        "tool_input": {"command": "printf safe"},
        "tool_use_id": "tool-1",
    }
    action, action_error = map_codex_hook_payload(action_payload, tmp_path)

    assert action_error is None
    assert action is not None
    assert action.raw["parent_event_id"] == prompt.raw["event_id"]
    graph = build_event_graph([normalized_prompt, action.raw])
    assert graph["unresolved_refs"] == []


def test_codex_pretooluse_does_not_invent_missing_or_mismatched_prompt_parent(
    tmp_path: Path,
) -> None:
    base = {
        "hook_event_name": "PreToolUse",
        "cwd": str(tmp_path),
        "model": "gpt-5-codex",
        "permission_mode": "default",
        "session_id": "codex-session",
        "tool_name": "Bash",
        "tool_input": {"command": "printf safe"},
        "tool_use_id": "tool-1",
    }
    for session_id, turn_id in (("codex-session", "turn-1"), ("other-session", "turn-2")):
        payload = {**base, "session_id": session_id, "turn_id": turn_id}
        action, error = map_codex_hook_payload(payload, tmp_path)
        assert error is None
        assert action is not None
        assert "parent_event_id" not in action.raw


def test_codex_pretooluse_fails_closed_on_corrupt_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text("{not-json}\n", encoding="utf-8")
    payload = {
        "hook_event_name": "PreToolUse",
        "cwd": str(tmp_path),
        "model": "gpt-5-codex",
        "permission_mode": "default",
        "session_id": "codex-session",
        "turn_id": "turn-1",
        "tool_name": "Bash",
        "tool_input": {"command": "printf safe"},
        "tool_use_id": "tool-1",
    }

    action, error = map_codex_hook_payload(payload, tmp_path)

    assert error is None
    assert action is not None
    assert "parent_event_id" not in action.raw


def test_codex_prompt_turn_id_keeps_distinct_submissions_distinct() -> None:
    first, first_error = map_codex_prompt_payload(_prompt("turn-1"), Path("/tmp"))
    second, second_error = map_codex_prompt_payload(_prompt("turn-2"), Path("/tmp"))

    assert first_error is None
    assert second_error is None
    assert first is not None
    assert second is not None
    assert first.raw["event_id"] != second.raw["event_id"]


def test_codex_prompt_rejects_missing_required_native_fields() -> None:
    payload = _prompt()
    del payload["turn_id"]

    event, error = map_codex_prompt_payload(payload, Path("/tmp"))

    assert event is None
    assert error == "missing_field:turn_id"


def test_codex_tool_mapper_does_not_guess_prompt_schema() -> None:
    event, error = map_codex_prompt_payload(
        {"hook_event_name": "UserPromptSubmit", "session_id": "s"}, Path("/tmp")
    )

    assert event is None
    assert error == "missing_field:cwd"


def test_prompt_lookup_rejects_corruption_after_match_and_invalid_encoding(tmp_path: Path) -> None:
    import json

    from hyodo.host_adapters.codex import _recorded_prompt_id

    payload = _prompt()
    payload["cwd"] = str(tmp_path)
    mapped, error = map_codex_prompt_payload(payload, tmp_path)
    assert error is None
    assert mapped is not None
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text(json.dumps(mapped.raw) + "\n{broken\n")
    assert _recorded_prompt_id(tmp_path, "codex-session", "turn-1") is None
    ledger.write_bytes(b"\xff\n")
    assert _recorded_prompt_id(tmp_path, "codex-session", "turn-1") is None
