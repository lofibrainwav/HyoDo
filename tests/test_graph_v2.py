from __future__ import annotations

from hyodo.graph_v2 import V1_SCHEMA, V2_SCHEMA, normalize_event, validate_graph_v2


def event(
    event_id: str,
    *,
    run_id: str = "r1",
    parent: str | None = None,
    parents: list[str] | None = None,
    schema: str = V1_SCHEMA,
) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": schema,
        "event_id": event_id,
        "run_id": run_id,
    }
    if schema == V1_SCHEMA and parent is not None:
        row["parent_event_id"] = parent
    if schema == V2_SCHEMA:
        row["parent_event_ids"] = list(parents or [])
    return row


def test_v1_normalizes_without_changing_single_parent_meaning() -> None:
    normalized = normalize_event(event("B", parent="A"))
    assert normalized["parent_event_ids"] == ["A"]
    assert normalized["legacy_parent_event_id"] == "A"
    assert normalized["legacy_parent_representable"] is True


def test_v2_join_never_silently_picks_a_legacy_parent() -> None:
    normalized = normalize_event(
        event("J", schema=V2_SCHEMA, parents=["B", "A", "A"])
    )
    assert normalized["parent_event_ids"] == ["A", "B"]
    assert normalized["legacy_parent_event_id"] is None
    assert normalized["legacy_parent_representable"] is False


def test_diamond_join_is_valid_and_deterministic() -> None:
    rows = [
        event("A"),
        event("B"),
        event("J", schema=V2_SCHEMA, parents=["B", "A"]),
        event("E", schema=V2_SCHEMA, parents=["J"]),
    ]
    forward = validate_graph_v2(rows)
    reverse = validate_graph_v2(list(reversed(rows)))
    assert forward.acyclic is True
    assert forward.references_resolved is True
    assert forward.structurally_valid is True
    assert forward.components == [["A"], ["B"], ["E"], ["J"]]
    assert forward == reverse


def test_unresolved_parent_is_not_cycle_evidence() -> None:
    result = validate_graph_v2(
        [event("A"), event("J", schema=V2_SCHEMA, parents=["A", "MISSING"])]
    )
    assert result.acyclic is True
    assert result.references_resolved is False
    assert result.structurally_valid is False
    assert result.unresolved_refs == [
        {"event_id": "J", "parent_event_id": "MISSING"}
    ]


def test_cross_run_parent_is_separate_from_unresolved() -> None:
    result = validate_graph_v2(
        [
            event("A", run_id="r1"),
            event("B", run_id="r2", schema=V2_SCHEMA, parents=["A"]),
        ]
    )
    assert result.acyclic is True
    assert result.unresolved_refs == []
    assert result.cross_run_refs == [{"event_id": "B", "parent_event_id": "A"}]
    assert result.structurally_valid is False


def test_self_cycle_is_reported_once_by_scc_oracle() -> None:
    result = validate_graph_v2(
        [event("A", schema=V2_SCHEMA, parents=["A"])]
    )
    assert result.acyclic is False
    assert result.structurally_valid is False
    assert result.cycles == [
        {"reason": "self_cycle", "component": ["A"], "edge": ["A", "A"]}
    ]


def test_join_only_cycle_is_detected() -> None:
    result = validate_graph_v2(
        [
            event("A", schema=V2_SCHEMA, parents=["J"]),
            event("B"),
            event("J", schema=V2_SCHEMA, parents=["A", "B"]),
        ]
    )
    assert result.acyclic is False
    assert ["A", "J"] in result.components
    assert any(item["reason"] == "join_cycle" for item in result.cycles)


def test_two_disjoint_cycles_are_distinct_components() -> None:
    result = validate_graph_v2(
        [
            event("A", schema=V2_SCHEMA, parents=["B"]),
            event("B", schema=V2_SCHEMA, parents=["A"]),
            event("C", schema=V2_SCHEMA, parents=["D"]),
            event("D", schema=V2_SCHEMA, parents=["C"]),
        ]
    )
    assert result.acyclic is False
    assert ["A", "B"] in result.components
    assert ["C", "D"] in result.components


def test_evidence_refs_do_not_become_causal_edges() -> None:
    row = event("B", schema=V2_SCHEMA, parents=[])
    row["evidence_refs"] = ["A"]
    result = validate_graph_v2([event("A"), row])
    assert result.acyclic is True
    assert result.structurally_valid is True
    assert normalize_event(row)["parent_event_ids"] == []


def test_duplicate_event_ids_fail_structure() -> None:
    result = validate_graph_v2([event("A"), event("A")])
    assert result.acyclic is True
    assert result.structurally_valid is False


def test_unknown_schema_fails_structure() -> None:
    result = validate_graph_v2([event("A", schema="hyodo.agent-event/v9")])
    assert result.structurally_valid is False
