from __future__ import annotations

from pathlib import Path
from typing import Any

from hyodo.graph_view import build_actor_rings, build_actor_rows, hyo_chain


def node(
    event_id: str,
    *,
    run_id: str = "run-1",
    step: int,
    kind: str = "tool_call",
    actor: str = "agent",
    actor_id: str | None = None,
    tool_name: str | None = None,
    decision: str | None = None,
) -> dict[str, Any]:
    return {
        "id": event_id,
        "type": "event",
        "run_id": run_id,
        "ts": f"2026-09-12T00:00:{step:02d}Z",
        "kind": kind,
        "actor": actor,
        "actor_id": actor_id,
        "step_index": step,
        "decision": decision,
        "tool": {"name": tool_name, "paths": [], "urls": []},
        "policy": {"rule_id": None, "reason": None, "evaluated_by": None},
        "io": {"output_digest": None},
    }


def parent(source: str, target: str) -> dict[str, str]:
    return {
        "type": "parent_event_id",
        "source": source,
        "target": target,
        "label": "result_of",
    }


def test_hyo_chain_requires_every_parent_lineage() -> None:
    nodes = [
        node("mission", step=0, kind="prompt", actor="human"),
        node("left", step=1, actor_id="left"),
        node("right", step=2, actor_id="right"),
        node("join", step=3, actor_id="join"),
        node("orphan", step=4, actor_id="orphan"),
    ]
    all_good = [
        parent("mission", "left"),
        parent("mission", "right"),
        parent("left", "join"),
        parent("right", "join"),
    ]
    chain = hyo_chain(nodes, all_good)
    assert chain["left"] is True
    assert chain["right"] is True
    assert chain["join"] is True

    mixed = [
        parent("mission", "left"),
        parent("left", "join"),
        parent("orphan", "join"),
    ]
    chain = hyo_chain(nodes, mixed)
    assert chain["left"] is True
    assert chain["orphan"] is False
    assert chain["join"] is False


def test_multi_parent_join_never_gets_arbitrary_parent_row() -> None:
    nodes = [
        node("mission", step=0, kind="prompt", actor="human"),
        node("left", step=1, actor_id="left", tool_name="left_worker"),
        node("right", step=2, actor_id="right", tool_name="right_worker"),
        node("join", step=3, actor_id="join", tool_name="join_worker"),
    ]
    edges = [
        parent("mission", "left"),
        parent("mission", "right"),
        parent("left", "join"),
        parent("right", "join"),
    ]
    rows = build_actor_rows(nodes, edges)["rows"]

    assert rows["agent:join"]["parent_row"] is None
    assert rows["agent:join"]["hyo_hierarchy"]["own_connected"] is True
    assert rows["agent:left"]["role"] == "orchestrator"
    assert rows["agent:right"]["role"] == "orchestrator"


def test_multi_parent_decision_does_not_borrow_one_tool_parent(tmp_path: Path) -> None:
    nodes = [
        node("mission", step=0, kind="prompt", actor="human"),
        node("call-a", step=1, actor_id="worker-a", tool_name="read_file"),
        node("call-b", step=2, actor_id="worker-b", tool_name="write_file"),
        node("decision", step=3, kind="decision", actor="hyodo", decision="ALLOW"),
    ]
    edges = [
        parent("mission", "call-a"),
        parent("mission", "call-b"),
        parent("call-a", "decision"),
        parent("call-b", "decision"),
    ]
    graph = {"nodes": nodes, "edges": edges}
    rings = build_actor_rings(graph, tmp_path)

    assert rings["agent:worker-a"]["tools"]["tools"] == [
        {"name": "read_file", "decision": "UNOBSERVED"}
    ]
    assert rings["agent:worker-b"]["tools"]["tools"] == [
        {"name": "write_file", "decision": "UNOBSERVED"}
    ]
