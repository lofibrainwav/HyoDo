"""Tests for the standalone HyoDo Tarjan SCC join-graph oracle."""

from __future__ import annotations

from hyodo.tarjan_scc import has_directed_cycle, hyodo_parent_edges, tarjan_scc


def test_empty_graph_is_acyclic() -> None:
    result = tarjan_scc([], [])
    assert result.acyclic is True
    assert result.components == []
    assert result.cycles == []


def test_singleton_without_self_edge_is_acyclic() -> None:
    result = tarjan_scc(["A"], [])
    assert result.acyclic is True
    assert result.components == [["A"]]


def test_chain_is_dag() -> None:
    result = tarjan_scc(["A", "B", "C"], [("C", "B"), ("B", "A")])
    assert result.acyclic is True
    assert result.components == [["A"], ["B"], ["C"]]


def test_self_loop_is_self_cycle() -> None:
    result = tarjan_scc(["A"], [("A", "A")])
    assert result.acyclic is False
    assert result.cycles == [{"reason": "self_cycle", "component": ["A"], "edge": ["A", "A"]}]


def test_two_node_join_cycle_has_summary_and_edges() -> None:
    result = tarjan_scc(["A", "J"], [("J", "A"), ("A", "J")])
    assert result.acyclic is False
    assert result.components == [["A", "J"]]
    assert [cycle["reason"] for cycle in result.cycles] == [
        "join_cycle",
        "join_cycle_edge",
        "join_cycle_edge",
    ]


def test_diamond_join_is_four_singleton_components() -> None:
    result = tarjan_scc(
        ["A", "B", "J", "E"],
        [("J", "A"), ("J", "B"), ("E", "J")],
    )
    assert result.acyclic is True
    assert result.components == [["A"], ["B"], ["E"], ["J"]]


def test_unresolved_edge_endpoint_is_ignored() -> None:
    result = tarjan_scc(["A"], [("A", "does-not-exist")])
    assert result.acyclic is True
    assert result.components == [["A"]]


def test_duplicate_edges_do_not_change_the_result() -> None:
    result = tarjan_scc(["A", "B"], [("B", "A"), ("B", "A")])
    assert result.acyclic is True
    assert result.components == [["A"], ["B"]]


def test_parent_edges_exclude_evidence_refs_and_skip_unresolved() -> None:
    nodes, edges = hyodo_parent_edges(
        [
            {"event_id": "A", "evidence_refs": ["B"]},
            {"event_id": "B", "parent_event_id": "A"},
            {"event_id": "C", "parent_event_id": "does-not-exist"},
        ]
    )
    assert nodes == ["A", "B", "C"]
    assert edges == [("B", "A")]


def test_multi_parent_adapter_keeps_child_to_parent_direction() -> None:
    nodes, edges = hyodo_parent_edges(
        [
            {"event_id": "A"},
            {"event_id": "B"},
            {"event_id": "J", "parent_event_ids": ["B", "A"]},
        ]
    )
    assert nodes == ["A", "B", "J"]
    assert edges == [("J", "A"), ("J", "B")]


def test_join_only_cycle_tarjan_catches() -> None:
    # A singular-pointer walk can stop at J -> A and miss the second parent
    # relation; SCC sees the complete directed cycle.
    result = tarjan_scc(["A", "J"], [("J", "A"), ("A", "J")])
    assert any(cycle["reason"] == "join_cycle" for cycle in result.cycles)
    assert has_directed_cycle(["A", "J"], [("J", "A"), ("A", "J")]) is True
