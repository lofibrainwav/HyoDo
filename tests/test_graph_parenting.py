from __future__ import annotations

from hyodo.graph_parenting import hyo_chain_all_parents, parent_sets, single_parent_map


def node(
    event_id: str,
    *,
    run_id: str = "r1",
    kind: str = "tool_call",
    actor: str = "agent",
    step: int = 1,
) -> dict[str, object]:
    return {
        "id": event_id,
        "run_id": run_id,
        "kind": kind,
        "actor": actor,
        "step_index": step,
    }


def edge(parent: str, child: str) -> dict[str, str]:
    return {"type": "parent_event_id", "source": parent, "target": child}


def test_parent_sets_preserve_join_and_legacy_map_refuses_to_choose() -> None:
    edges = [edge("right", "join"), edge("left", "join"), edge("left", "join")]
    assert parent_sets(edges) == {"join": ("left", "right")}
    assert single_parent_map(edges) == {}


def test_single_parent_map_keeps_v1_semantics() -> None:
    assert single_parent_map([edge("mission", "work")]) == {"work": "mission"}


def test_join_is_filial_only_when_every_parent_is_filial() -> None:
    nodes = [
        node("mission", kind="prompt", actor="human", step=0),
        node("left"),
        node("right"),
        node("join", step=2),
    ]
    edges = [
        edge("mission", "left"),
        edge("mission", "right"),
        edge("left", "join"),
        edge("right", "join"),
    ]
    chain = hyo_chain_all_parents(nodes, edges)
    assert chain == {"mission": True, "left": True, "right": True, "join": True}


def test_one_connected_and_one_orphan_parent_never_false_greens_join() -> None:
    nodes = [
        node("mission", kind="prompt", actor="human", step=0),
        node("left"),
        node("orphan"),
        node("join", step=2),
    ]
    edges = [edge("mission", "left"), edge("left", "join"), edge("orphan", "join")]
    chain = hyo_chain_all_parents(nodes, edges)
    assert chain["left"] is True
    assert chain["orphan"] is False
    assert chain["join"] is False


def test_cross_run_parent_is_not_filial() -> None:
    nodes = [
        node("mission", kind="prompt", actor="human", step=0),
        node("foreign", run_id="r2", kind="prompt", actor="human", step=0),
        node("join"),
    ]
    chain = hyo_chain_all_parents(nodes, [edge("mission", "join"), edge("foreign", "join")])
    assert chain["join"] is False


def test_cycle_is_fail_closed_without_recursion() -> None:
    nodes = [
        node("mission", kind="prompt", actor="human", step=0),
        node("a"),
        node("b"),
    ]
    chain = hyo_chain_all_parents(nodes, [edge("b", "a"), edge("a", "b")])
    assert chain["a"] is False
    assert chain["b"] is False
