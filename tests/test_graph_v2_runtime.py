from __future__ import annotations

from hyodo.event_graph import build_event_graph, validate_event_edges
from hyodo.graph_v2 import V1_SCHEMA, V2_SCHEMA


def event(
    event_id: str,
    *,
    run_id: str = "r1",
    step: int = 0,
    kind: str = "tool_call",
    actor: str = "agent",
    parent: str | None = None,
    parents: list[str] | None = None,
    schema: str = V1_SCHEMA,
) -> dict[str, object]:
    row: dict[str, object] = {
        "schema_version": schema,
        "event_id": event_id,
        "run_id": run_id,
        "ts": f"2026-09-12T00:00:{step:02d}Z",
        "kind": kind,
        "step_index": step,
        "actor": actor,
        "evidence_refs": [],
    }
    if schema == V1_SCHEMA and parent is not None:
        row["parent_event_id"] = parent
    if schema == V2_SCHEMA:
        row["parent_event_ids"] = list(parents or [])
    return row


def test_v1_parent_export_is_unchanged() -> None:
    rows = [
        event("mission", step=0, kind="prompt", actor="human"),
        event("work", step=1, parent="mission"),
    ]
    graph = build_event_graph(rows)
    assert graph["status"] == "READY"
    assert graph["edges"] == [
        {
            "type": "parent_event_id",
            "source": "mission",
            "target": "work",
            "label": "result_of",
        }
    ]
    assert graph["nodes"][1]["parent_event_ids"] == ["mission"]


def test_v2_diamond_join_exports_every_parent_deterministically() -> None:
    rows = [
        event("mission", step=0, kind="prompt", actor="human"),
        event("left", step=1, schema=V2_SCHEMA, parents=["mission"]),
        event("right", step=2, schema=V2_SCHEMA, parents=["mission"]),
        event("join", step=3, schema=V2_SCHEMA, parents=["right", "left", "left"]),
    ]
    graph = build_event_graph(rows)
    assert graph["status"] == "READY"
    join_edges = [edge for edge in graph["edges"] if edge["target"] == "join"]
    assert join_edges == [
        {
            "type": "parent_event_id",
            "source": "left",
            "target": "join",
            "label": "result_of",
        },
        {
            "type": "parent_event_id",
            "source": "right",
            "target": "join",
            "label": "result_of",
        },
    ]
    join_node = next(node for node in graph["nodes"] if node["id"] == "join")
    assert join_node["parent_event_ids"] == ["left", "right"]
    assert graph["topology"]["structurally_valid"] is True


def test_v2_cross_run_parent_never_becomes_a_graph_edge() -> None:
    rows = [
        event("a", run_id="r1"),
        event("b", run_id="r2", schema=V2_SCHEMA, parents=["a"]),
    ]
    graph = build_event_graph(rows)
    assert graph["status"] == "UNOBSERVED"
    assert graph["edges"] == []
    assert {
        "event_id": "b",
        "field": "parent_event_ids",
        "ref": "a",
        "reason": "cross_run_ref",
    } in graph["unresolved_refs"]
    assert graph["topology"]["cross_run_refs"] == [{"event_id": "b", "parent_event_id": "a"}]


def test_v2_join_cycle_is_fail_closed_by_tarjan_runtime() -> None:
    rows = [
        event("a", schema=V2_SCHEMA, parents=["join"]),
        event("b", schema=V2_SCHEMA),
        event("join", schema=V2_SCHEMA, parents=["a", "b"]),
    ]
    graph = build_event_graph(rows)
    assert graph["status"] == "UNOBSERVED"
    assert graph["topology"]["acyclic"] is False
    assert any(issue["reason"] == "cycle" for issue in graph["unresolved_refs"])


def test_v2_parent_list_is_validated_instead_of_silently_dropped() -> None:
    row = event("a", schema=V2_SCHEMA)
    row["parent_event_ids"] = "not-a-list"
    issues = validate_event_edges([row])
    assert {
        "event_id": "a",
        "field": "parent_event_ids",
        "ref": None,
        "reason": "invalid_ref_list",
    } in issues
