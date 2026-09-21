"""Evidence-bounded reconciliation tests for the verification projection."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.report import build_report_graph
from hyodo.verification_view import build_verification_view


def _event(**overrides: Any) -> str:
    base: dict[str, Any] = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e0",
        "run_id": "run-1",
        "ts": "2026-09-20T00:00:00+00:00",
        "kind": "prompt",
        "actor": "human",
        "step_index": 0,
        "tool": {},
        "policy": {},
        "evidence_refs": [],
    }
    base.update(overrides)
    return json.dumps(base)


def _view(root: Path, lines: list[str]) -> dict[str, Any]:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return build_verification_view(build_report_graph(root), root=root)


def test_output_digest_without_semantics_stays_semantics_unobserved(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="p", kind="prompt", actor="human"),
            _event(
                event_id="c",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="p",
                tool={"name": "Bash"},
            ),
            _event(
                event_id="r",
                kind="tool_result",
                actor="agent",
                step_index=2,
                parent_event_id="c",
                tool={"name": "Bash"},
                io={"output_digest": "abc123456789"},
            ),
        ],
    )
    assert view["events"]["c"]["lens_mapping_disposition"] == "INSUFFICIENT_MEASUREMENT"
    assert view["events"]["r"]["lens_mapping_disposition"] == "SEMANTICS_UNOBSERVED"
    assert view["reconciliation"]["lens_mapping"]["mapping_gaps"] == 0


def test_legacy_tool_name_mapping_does_not_become_reconciliation_evidence(
    tmp_path: Path,
) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="p", kind="prompt", actor="human"),
            _event(
                event_id="r",
                kind="tool_result",
                actor="agent",
                step_index=1,
                parent_event_id="p",
                tool={"name": "pytest"},
                io={"output_digest": "abc123456789"},
            ),
        ],
    )
    # The legacy compatibility column still recognizes the tool label.
    assert view["events"]["r"]["columns"] == ["jin"]
    # Reconciliation refuses to treat that label as measured lens semantics.
    assert view["events"]["r"]["lens_mapping_disposition"] == "SEMANTICS_UNOBSERVED"
    assert view["reconciliation"]["lens_mapping"]["mapping_gaps"] == 0


def test_explicit_unmapped_semantics_are_a_mapping_gap(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="p", kind="prompt", actor="human"),
            _event(
                event_id="r",
                kind="tool_result",
                actor="agent",
                step_index=1,
                parent_event_id="p",
                tool={"name": "opaque", "method": "POST"},
                io={"output_digest": "abc123456789"},
            ),
        ],
    )
    assert view["events"]["r"]["lens_mapping_disposition"] == "MAPPING_GAP"
    assert view["reconciliation"]["lens_mapping"]["mapping_gaps"] == 1


def test_tool_call_can_be_intentionally_minimal_without_becoming_measured(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="p", kind="prompt", actor="human"),
            _event(
                event_id="c",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="p",
                tool={"name": "Bash"},
            ),
        ],
    )
    assert view["events"]["c"]["recording_disposition"] == "INTENTIONALLY_MINIMAL"
    assert view["reconciliation"]["recording"]["unexplained_required_gaps"] == 0


def test_missing_result_measurement_stays_unobserved(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="p", kind="prompt", actor="human"),
            _event(
                event_id="c", kind="tool_call", actor="agent", step_index=1, parent_event_id="p"
            ),
            _event(
                event_id="r", kind="tool_result", actor="agent", step_index=2, parent_event_id="c"
            ),
        ],
    )
    assert view["events"]["r"]["recording_disposition"] == "MEASUREMENT_UNOBSERVED"


def test_missing_intent_receipt_is_not_unauthorized_execution(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [_event(event_id="c", run_id="run-no-intent", kind="tool_call", actor="agent")],
    )
    intent = view["reconciliation"]["intent_provenance"]
    assert intent["by_run"]["run-no-intent"] == "ADMISSION_UNOBSERVED"
    assert intent["unauthorized_executions"] == "NOT_PROVEN"
    assert intent["undispositioned_runs"] == 0


def test_recorded_intent_is_distinct_from_authority(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="p", run_id="run-with-intent", kind="prompt", actor="human"),
            _event(
                event_id="c",
                run_id="run-with-intent",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="p",
            ),
        ],
    )
    intent = view["reconciliation"]["intent_provenance"]
    assert intent["by_run"]["run-with-intent"] == "RECORDED_INTENT"
    assert view["authority"] == "UNOBSERVED"


def test_reconciliation_projection_does_not_mutate_ledger(tmp_path: Path) -> None:
    path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _event(event_id="p", kind="prompt", actor="human") + "\n",
        encoding="utf-8",
    )
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    build_verification_view(build_report_graph(tmp_path), root=tmp_path)
    after = hashlib.sha256(path.read_bytes()).hexdigest()
    assert after == before
