"""End-to-end projection tests for native output observation provenance."""

from pathlib import Path

from hyodo.event_graph import build_event_graph
from hyodo.events import content_digest, validate_event
from hyodo.host_adapters.codex import map_codex_hook_payload
from hyodo.verification_view import build_verification_view


def _codex_result(**fields: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "hook_event_name": "PostToolUse",
        "session_id": "view-output-run",
        "tool_use_id": "result-tool-1",
        "tool_name": "Bash",
        "tool_input": {"command": "printf test"},
        "cwd": "/tmp/project",
    }
    payload.update(fields)
    return payload


def _mapped_event(**fields: object) -> dict[str, object]:
    mapped, error = map_codex_hook_payload(_codex_result(**fields), Path("/tmp"))
    assert error is None
    assert mapped is not None
    ok, reasons, normalized = validate_event(mapped.raw)
    assert ok, reasons
    assert normalized is not None
    return normalized


def _view_for(event: dict[str, object]) -> dict[str, object]:
    return build_verification_view(build_event_graph([event]), root=Path("/tmp"))


def test_adapter_tag_reaches_graph_and_verification_view() -> None:
    event = _mapped_event(tool_response="")
    graph = build_event_graph([event])
    node = graph["nodes"][0]
    view = _view_for(event)

    assert node["io"]["output_observation"] == "output:empty"
    assert view["events"][event["event_id"]]["how"]["output_observation"] == "output:empty"


def test_missing_and_old_digest_only_records_are_unobserved() -> None:
    missing = _mapped_event()
    old = {
        **missing,
        "event_id": "old-digest-only",
        "io": {"output_digest": content_digest("historical")},
        "meta": {"tags": ["host:codex", "host_event:PostToolUse"]},
    }

    missing_view = _view_for(missing)
    old_graph = build_event_graph([old])

    assert (
        missing_view["events"][missing["event_id"]]["how"]["output_observation"] == "output:missing"
    )
    assert old_graph["nodes"][0]["io"]["output_observation"] == "UNOBSERVED"


def test_conflicting_or_unknown_output_tags_fail_closed() -> None:
    for tags in (
        ["output:empty", "output:observed"],
        ["output:future_shape"],
        ["output:empty", "output:future_shape"],
    ):
        event = _mapped_event()
        event["meta"] = {"tags": tags}
        view = _view_for(event)
        assert view["events"][event["event_id"]]["how"]["output_observation"] == "UNOBSERVED"


def test_input_digest_survives_graph_and_view_projection() -> None:
    event = _mapped_event(tool_response="done")
    event["io"]["input_digest"] = content_digest("request")
    graph = build_event_graph([event])
    view = _view_for(event)

    assert graph["nodes"][0]["io"]["input_digest"] == content_digest("request")
    assert view["events"][event["event_id"]]["how"]["input_digest"] == content_digest("request")


def test_pretool_with_a_result_looking_field_remains_unobserved() -> None:
    payload = _codex_result(hook_event_name="PreToolUse", tool_response="not-a-result")
    mapped, error = map_codex_hook_payload(payload, Path("/tmp"))
    assert error is None
    assert mapped is not None
    ok, reasons, event = validate_event(mapped.raw)
    assert ok, reasons
    assert event is not None
    graph = build_event_graph([event])
    assert graph["nodes"][0]["io"]["output_observation"] == "UNOBSERVED"
