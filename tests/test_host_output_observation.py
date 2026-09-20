"""Regression coverage for native tool-result observation states."""

from pathlib import Path

import pytest

from hyodo.events import content_digest
from hyodo.host_adapters.codex import map_codex_hook_payload


def _payload(event: str = "PostToolUse", **fields: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": event,
        "session_id": "output-observation-test",
        "tool_use_id": "tool-1",
        "tool_name": "Bash",
        "tool_input": {"command": "printf test"},
        "cwd": "/tmp/project",
    }
    payload.update(fields)
    return payload


@pytest.mark.parametrize("value", ["", 0, False])
def test_supported_explicit_tool_response_is_digestable(value: object) -> None:
    mapped, error = map_codex_hook_payload(_payload(tool_response=value), Path("/tmp"))

    assert error is None
    assert mapped is not None
    expected = value if isinstance(value, str) else str(value).lower()
    assert mapped.raw["io"]["output_digest"] == content_digest(expected)
    expected_tag = "output:empty" if value == "" else "output:observed"
    assert expected_tag in mapped.raw["meta"]["tags"]


def test_missing_tool_response_has_no_digest_and_is_explicitly_tagged() -> None:
    mapped, error = map_codex_hook_payload(_payload(), Path("/tmp"))

    assert error is None
    assert mapped is not None
    assert "output_digest" not in mapped.raw.get("io", {})
    assert "output:missing" in mapped.raw["meta"]["tags"]


def test_null_tool_response_has_no_digest_and_is_distinct_from_missing() -> None:
    mapped, error = map_codex_hook_payload(_payload(tool_response=None), Path("/tmp"))

    assert error is None
    assert mapped is not None
    assert "output_digest" not in mapped.raw.get("io", {})
    assert "output:null" in mapped.raw["meta"]["tags"]
    assert "output:missing" not in mapped.raw["meta"]["tags"]


def test_unsupported_tool_response_shape_has_no_digest() -> None:
    mapped, error = map_codex_hook_payload(_payload(tool_response=object()), Path("/tmp"))

    assert error is None
    assert mapped is not None
    assert "output_digest" not in mapped.raw.get("io", {})
    assert "output:unsupported_shape" in mapped.raw["meta"]["tags"]


def test_first_non_null_host_output_key_keeps_declared_precedence() -> None:
    mapped, error = map_codex_hook_payload(
        _payload(tool_response=None, output="lower-priority"), Path("/tmp")
    )

    assert error is None
    assert mapped is not None
    assert mapped.raw["io"]["output_digest"] == content_digest("lower-priority")
    assert "output:observed" in mapped.raw["meta"]["tags"]


def test_all_null_host_output_keys_are_tagged_null() -> None:
    mapped, error = map_codex_hook_payload(
        _payload(tool_response=None, output=None, result_json=None), Path("/tmp")
    )

    assert error is None
    assert mapped is not None
    assert "output_digest" not in mapped.raw.get("io", {})
    assert "output:null" in mapped.raw["meta"]["tags"]


def test_pretool_never_claims_a_result() -> None:
    mapped, error = map_codex_hook_payload(
        _payload("PreToolUse", tool_response="must-not-be-a-result"), Path("/tmp")
    )

    assert error is None
    assert mapped is not None
    assert mapped.raw["kind"] == "tool_call"
    assert "output_digest" not in mapped.raw.get("io", {})
    assert not any(tag.startswith("output:") for tag in mapped.raw["meta"]["tags"])
