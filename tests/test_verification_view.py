"""Contract for `hyodo.verification_view` — the investigation projection.

Every fixture here is written as real agent events and read back through
`hyodo.report.build_report_graph`, the same producer the dashboard uses. Hand
building a graph dict would let this test drift away from the producer without
anything noticing, which is the failure mode the module itself exists to stop.

The six fixtures cover the situations the view has to stay honest about: a run
that closes cleanly, a call with no recorded effect, two decisions that
disagree, a multi-parent join, a citation pointing at nothing, and evidence
recorded after the decision that cites it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.report import build_report_graph
from hyodo.verification_view import (
    VERIFICATION_VIEW_SCHEMA_VERSION,
    build_verification_view,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Fields that would turn this projection into a judgement. None may appear.
FORBIDDEN_TOP_LEVEL_KEYS = frozenset({"score", "confidence", "aggregate", "total", "rank"})


def _event(**overrides: Any) -> str:
    """One `hyodo.agent-event/v1` line with the fixture defaults filled in."""
    base: dict[str, Any] = {
        "schema_version": "hyodo.agent-event/v1",
        "run_id": "run-1",
        "ts": "2026-09-06T00:00:00+00:00",
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
    """Write a ledger under *root* and project it through the real producer."""
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return build_verification_view(build_report_graph(root), root=root)


def _normal_close() -> list[str]:
    """A run that states its intent, does work, records it, and decides."""
    return [
        _event(event_id="e0", kind="prompt", actor="human", step_index=0),
        _event(
            event_id="e1",
            kind="tool_call",
            actor="agent",
            actor_id="a1",
            step_index=1,
            parent_event_id="e0",
            tool={"name": "pytest", "paths": ["tests/"], "urls": [], "method": None},
        ),
        _event(
            event_id="e2",
            kind="tool_result",
            actor="agent",
            actor_id="a1",
            step_index=2,
            parent_event_id="e1",
            tool={"name": "pytest", "paths": ["tests/"], "urls": [], "method": None},
            io={"output_digest": "abc123"},
        ),
        _event(
            event_id="e3",
            kind="decision",
            actor="hyodo",
            step_index=3,
            parent_event_id="e2",
            evidence_refs=["e2"],
            policy={
                "decision": "ALLOW",
                "rule_id": "r1",
                "reason": "tests passed",
                "evaluated_by": "hyodo",
            },
        ),
    ]


def test_schema_pin_matches_public_verification_view_schema() -> None:
    schema = REPO_ROOT / "schemas/verification-view-v0.schema.json"
    pin = json.loads((REPO_ROOT / "schemas/verification-view-v0.pin.json").read_text())
    assert hashlib.sha256(schema.read_bytes()).hexdigest() == pin["digest"]
    assert pin["schema_version"] == VERIFICATION_VIEW_SCHEMA_VERSION


def test_projection_grants_no_authority_and_carries_no_score(tmp_path: Path) -> None:
    view = _view(tmp_path, _normal_close())
    assert view["schema_version"] == VERIFICATION_VIEW_SCHEMA_VERSION
    assert view["authority"] == "UNOBSERVED"
    assert not FORBIDDEN_TOP_LEVEL_KEYS & set(view)
    serialized = json.dumps(view)
    for banned in ("harmony_aggregate", "integrity_score"):
        assert banned not in serialized


def test_time_axis_is_fixed_and_eternity_is_the_axis_not_a_column(tmp_path: Path) -> None:
    view = _view(tmp_path, _normal_close())
    assert view["time_axis"]["direction"] == "left_to_right"
    assert view["time_axis"]["continuity_lens"] == "eternity"
    # The five measured columns are the viewer's columns; Eternity is not one.
    assert set(view["coverage"]) == {"jin", "seon", "mi", "in", "hyo"}


def test_lanes_reuse_the_graph_role_instead_of_guessing(tmp_path: Path) -> None:
    view = _view(tmp_path, _normal_close())
    roles = [lane["role"] for lane in view["lanes"]]
    # `hyodo` cites another actor's event and writes nothing, so the producer
    # already calls it a reviewer. The projection must not relabel it.
    assert "human" in roles
    assert "reviewer" in roles
    assert "worker" in roles
    assert sum(len(lane["events"]) for lane in view["lanes"]) == len(view["events"])


def test_causal_and_evidence_edges_stay_in_separate_lists(tmp_path: Path) -> None:
    view = _view(tmp_path, _normal_close())
    assert {(edge["source"], edge["target"]) for edge in view["edges_causal"]} == {
        ("e0", "e1"),
        ("e1", "e2"),
        ("e2", "e3"),
    }
    assert [(edge["source"], edge["target"]) for edge in view["edges_evidence"]] == [("e2", "e3")]
    assert view["edges_evidence"][0]["source_after_target"] is False


def test_normal_close_reports_nothing_missing(tmp_path: Path) -> None:
    view = _view(tmp_path, _normal_close())
    assert all(not bucket for bucket in view["missing"].values())
    assert all(event["hyo_chained"] for event in view["events"].values())


def test_a_call_with_no_recorded_result_is_named(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="e0", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="e1",
                kind="tool_call",
                actor="agent",
                actor_id="a1",
                step_index=1,
                parent_event_id="e0",
                tool={"name": "deploy", "paths": [], "urls": [], "method": None},
            ),
        ],
    )
    assert view["missing"]["calls_without_result"] == ["e1"]
    # Recording nothing is a recording gap, not a mapping gap.
    assert view["missing"]["unmeasured_events"] == ["e1"]
    assert view["missing"]["unclassified_events"] == []


def test_two_disagreeing_decisions_are_both_reported(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="e0", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="e1",
                kind="decision",
                actor="hyodo",
                step_index=1,
                parent_event_id="e0",
                policy={
                    "decision": "ALLOW",
                    "rule_id": "r1",
                    "reason": "receipt ok",
                    "evaluated_by": "hyodo",
                },
            ),
            _event(
                event_id="e2",
                kind="decision",
                actor="hyodo",
                step_index=2,
                parent_event_id="e0",
                policy={
                    "decision": "DENY",
                    "rule_id": "r1",
                    "reason": "no observed effect",
                    "evaluated_by": "hyodo",
                },
            ),
        ],
    )
    recorded = view["decisions_by_run"]["run-1"]
    assert [entry["decision"] for entry in recorded] == ["ALLOW", "DENY"]
    # The later decision must not replace or average away the earlier one.
    assert {"e1", "e2"} <= set(view["events"])


def test_a_multi_parent_join_keeps_every_parent(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="e0", kind="prompt", actor="human", step_index=0),
            _event(
                schema_version="hyodo.agent-event/v2",
                event_id="e1",
                kind="tool_call",
                actor="agent",
                actor_id="a1",
                step_index=1,
                parent_event_ids=["e0"],
            ),
            _event(
                schema_version="hyodo.agent-event/v2",
                event_id="e2",
                kind="tool_call",
                actor="agent",
                actor_id="a2",
                step_index=1,
                parent_event_ids=["e0"],
            ),
            _event(
                schema_version="hyodo.agent-event/v2",
                event_id="e3",
                kind="tool_result",
                actor="agent",
                actor_id="a1",
                step_index=2,
                parent_event_ids=["e1", "e2"],
            ),
        ],
    )
    assert sorted(view["events"]["e3"]["causal_parents"]) == ["e1", "e2"]
    joined = [edge for edge in view["edges_causal"] if edge["target"] == "e3"]
    assert sorted(edge["source"] for edge in joined) == ["e1", "e2"]
    assert view["topology"]["acyclic"] is True


def test_a_citation_pointing_at_nothing_never_becomes_an_edge(tmp_path: Path) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="e0", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="e1",
                kind="decision",
                actor="hyodo",
                step_index=1,
                parent_event_id="e0",
                evidence_refs=["does-not-exist"],
                policy={
                    "decision": "ALLOW",
                    "rule_id": "r1",
                    "reason": "cited",
                    "evaluated_by": "hyodo",
                },
            ),
        ],
    )
    assert view["edges_evidence"] == []
    unresolved = view["missing"]["unresolved_refs"]
    assert [entry["ref"] for entry in unresolved] == ["does-not-exist"]
    # A graph that cites something it cannot resolve is not a clean graph.
    assert view["status"] == "UNOBSERVED"


def test_evidence_recorded_after_the_decision_is_flagged_not_reordered(
    tmp_path: Path,
) -> None:
    view = _view(
        tmp_path,
        [
            _event(event_id="e0", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="e1",
                kind="decision",
                actor="hyodo",
                step_index=1,
                parent_event_id="e0",
                evidence_refs=["e2"],
                policy={
                    "decision": "ALLOW",
                    "rule_id": "r1",
                    "reason": "cited later evidence",
                    "evaluated_by": "hyodo",
                },
            ),
            _event(
                event_id="e2",
                kind="tool_result",
                actor="agent",
                actor_id="a1",
                step_index=2,
                parent_event_id="e0",
                io={"output_digest": "late9"},
            ),
        ],
    )
    late = [edge for edge in view["edges_evidence"] if edge["target"] == "e1"]
    assert len(late) == 1
    assert late[0]["source_after_target"] is True
    # The recorded order is preserved; nothing is silently resequenced.
    assert view["event_order"] == ["e0", "e1", "e2"]


def test_five_w_one_h_only_regroups_recorded_fields(tmp_path: Path) -> None:
    view = _view(tmp_path, _normal_close())
    call = view["events"]["e1"]
    assert call["who"] == {"actor": "agent", "actor_id": "a1"}
    assert call["what"]["kind"] == "tool_call"
    assert call["what"]["tool_name"] == "pytest"
    assert call["when"]["step_index"] == 1
    assert call["where"]["paths"] == ["tests/"]
    decision = view["events"]["e3"]
    assert decision["what"]["decision"] == "ALLOW"
    assert decision["why"]["reason"] == "tests passed"
    assert decision["how"]["rule_id"] == "r1"
    # An unrecorded heading stays empty rather than being filled in.
    assert call["how"]["rule_id"] is None


def test_an_empty_ledger_projects_without_inventing_lanes(tmp_path: Path) -> None:
    path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")
    view = build_verification_view(build_report_graph(tmp_path), root=tmp_path)
    assert view["lanes"] == []
    assert view["events"] == {}
    assert view["edges_causal"] == []
    assert view["authority"] == "UNOBSERVED"


def test_projected_payload_validates_against_the_public_schema(tmp_path: Path) -> None:
    import jsonschema

    schema = json.loads((REPO_ROOT / "schemas/verification-view-v0.schema.json").read_text())
    jsonschema.validate(_view(tmp_path, _normal_close()), schema)


def test_the_schema_actually_rejects_an_invented_field(tmp_path: Path) -> None:
    """A schema that accepts anything documents nothing."""
    import jsonschema

    schema = json.loads((REPO_ROOT / "schemas/verification-view-v0.schema.json").read_text())
    payload = _view(tmp_path, _normal_close())
    payload["score"] = 0.99
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError("the schema accepted a score field it must refuse")


def test_the_payload_is_json_serializable_for_an_http_route(tmp_path: Path) -> None:
    payload = _view(tmp_path, _normal_close())
    assert json.loads(json.dumps(payload, sort_keys=True)) == payload
