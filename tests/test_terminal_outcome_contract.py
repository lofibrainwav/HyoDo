"""Terminal-disposition contract tests for the verification projection."""

from __future__ import annotations

from typing import Any

from hyodo.event_graph import build_event_graph
from hyodo.events import validate_event
from hyodo.verification_view import build_verification_view


def _event(event_id: str, kind: str, *, parent: str | None = None, **extra: Any) -> dict[str, Any]:
    event: dict[str, Any] = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": event_id,
        "run_id": "run-1",
        "ts": "2026-09-20T00:00:00+00:00",
        "kind": kind,
        "step_index": 0,
        "actor": "agent" if kind != "prompt" else "human",
        "parent_event_id": parent,
    }
    event.update(extra)
    return event


def _view(*events: dict[str, Any]) -> dict[str, Any]:
    normalized = []
    for event in events:
        ok, reasons, result = validate_event(event)
        assert ok, reasons
        assert result is not None
        normalized.append(result)
    return build_verification_view(build_event_graph(normalized))


def test_recorded_tool_result_means_returned_not_success() -> None:
    view = _view(
        _event("prompt", "prompt"),
        _event("call", "tool_call", parent="prompt"),
        _event("result", "tool_result", parent="call", io={"output_digest": "abc123456789"}),
    )
    terminal = view["events"]["call"]["terminal"]
    assert terminal == {
        "state": "RETURNED",
        "cardinality": 1,
        "evidence_source": "tool_result",
        "event_ids": ["result"],
    }
    assert "SUCCESS" not in terminal.values()


def test_missing_terminal_callback_stays_unobserved() -> None:
    view = _view(
        _event("prompt", "prompt"),
        _event("call", "tool_call", parent="prompt"),
    )
    terminal = view["events"]["call"]["terminal"]
    assert terminal["state"] == "UNOBSERVED"
    assert terminal["cardinality"] == 0
    assert view["missing"]["calls_without_terminal_outcome"] == ["call"]
    assert view["missing"]["calls_without_result"] == ["call"]


def test_explicit_error_event_is_error_not_inferred_failure() -> None:
    view = _view(
        _event("prompt", "prompt"),
        _event("call", "tool_call", parent="prompt"),
        _event("error", "error", parent="call"),
    )
    terminal = view["events"]["call"]["terminal"]
    assert terminal["state"] == "ERROR"
    assert terminal["evidence_source"] == "error_event"


def test_duplicate_terminal_children_are_contradicted() -> None:
    view = _view(
        _event("prompt", "prompt"),
        _event("call", "tool_call", parent="prompt"),
        _event("result-1", "tool_result", parent="call"),
        _event("result-2", "tool_result", parent="call"),
    )
    terminal = view["events"]["call"]["terminal"]
    assert terminal["state"] == "CONTRADICTED"
    assert terminal["cardinality"] == 2
    assert view["missing"]["duplicate_terminal_outcomes"] == ["call"]


def test_unobserved_host_modes_are_reserved_but_not_invented() -> None:
    view = _view(
        _event("prompt", "prompt"),
        _event("call", "tool_call", parent="prompt"),
    )
    counts = view["reconciliation"]["terminal_outcomes"]["counts"]
    assert counts["CANCELLED"] == 0
    assert counts["TIMEOUT"] == 0
    assert counts["ABORTED"] == 0
    assert counts["UNOBSERVED"] == 1
