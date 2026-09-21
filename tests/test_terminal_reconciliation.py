"""Tests for the read-only terminal reconciliation projection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.terminal_reconciliation import build_terminal_reconciliation


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
        "meta": {"tags": ["host:codex"]},
        "tool": {"name": "Bash" if kind == "tool_call" else None},
    }
    event.update(extra)
    return event


def _write(root: Path, events: list[dict[str, Any]]) -> None:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n")


def test_report_preserves_unobserved_without_inventing_terminal_state(tmp_path: Path) -> None:
    _write(tmp_path, [_event("call", "tool_call")])
    report = build_terminal_reconciliation(tmp_path)
    assert report["status"] == "RECONCILIATION_REQUIRED"
    assert report["summary"]["calls_without_terminal_outcome"] == 1
    assert report["summary"]["by_tool_family"] == {"Bash": 1}
    assert report["summary"]["by_host"] == {"codex": 1}
    assert report["summary"]["by_producer_terminal_capability"] == {"UNSUPPORTED_BY_HOST": 1}
    assert report["summary"]["genuinely_missing_proven"] == 0
    assert report["records"][0]["termination_evidence"] == "UNOBSERVED"
    assert report["records"][0]["producer_terminal_capability"] == "UNSUPPORTED_BY_HOST"
    assert report["records"][0]["terminal_disposition"] == "UNOBSERVED"


def test_report_does_not_count_a_recorded_return_as_missing(tmp_path: Path) -> None:
    _write(
        tmp_path,
        [
            _event("call", "tool_call"),
            _event(
                "result",
                "tool_result",
                parent="call",
                io={"output_digest": "abc123456789"},
            ),
        ],
    )
    report = build_terminal_reconciliation(tmp_path)
    assert report["status"] == "OBSERVED"
    assert report["summary"]["calls_without_terminal_outcome"] == 0
    assert report["summary"]["terminal_counts"]["RETURNED"] == 1
    assert report["records"] == []
