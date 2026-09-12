"""Deterministic parent-set helpers for Graph v1/v2 consumers.

These helpers consume the public event-graph edge shape. A multi-parent join
never becomes a singular parent implicitly. Hyo lineage is fail-closed: every
causal parent lineage must resolve to the same run's observed mission.
"""

from __future__ import annotations

from typing import Any


def parent_sets(edges: list[dict[str, Any]]) -> dict[str, tuple[str, ...]]:
    """Return sorted, deduplicated parent ids for each child event."""
    gathered: dict[str, set[str]] = {}
    for edge in edges:
        if edge.get("type") != "parent_event_id":
            continue
        target = edge.get("target")
        source = edge.get("source")
        if isinstance(target, str) and target and isinstance(source, str) and source:
            gathered.setdefault(target, set()).add(source)
    return {target: tuple(sorted(parents)) for target, parents in sorted(gathered.items())}


def single_parent_map(edges: list[dict[str, Any]]) -> dict[str, str]:
    """Return only unambiguous singular parents.

    Legacy row nesting / decision attribution may consume this mapping. A join
    with two or more parents is intentionally absent instead of choosing the
    first or last parent.
    """
    return {
        target: parents[0]
        for target, parents in parent_sets(edges).items()
        if len(parents) == 1
    }


def hyo_chain_all_parents(
    nodes: list[dict[str, Any]], edges: list[dict[str, Any]]
) -> dict[str, bool]:
    """Return fail-closed Hyo lineage for singular and multi-parent graphs.

    Missions are the lowest-step human prompt in each run. A non-mission event
    is filial only if it has at least one causal parent and *all* parents are
    observed events in the same run whose own lineage is filial. Missing
    parents, cross-run parents, disconnected roots and cycles resolve False.
    """
    node_by_id = {
        node_id: node
        for node in nodes
        if isinstance((node_id := node.get("id")), str) and node_id
    }
    parents_by_child = parent_sets(edges)

    mission_by_run: dict[str, str] = {}
    mission_step: dict[str, int] = {}
    for node_id, node in node_by_id.items():
        run_id = node.get("run_id")
        step = node.get("step_index")
        if (
            isinstance(run_id, str)
            and node.get("kind") == "prompt"
            and node.get("actor") == "human"
            and isinstance(step, int)
            and not isinstance(step, bool)
            and (run_id not in mission_step or step < mission_step[run_id])
        ):
            mission_by_run[run_id] = node_id
            mission_step[run_id] = step

    result: dict[str, bool] = {}
    pending: set[str] = set(node_by_id)
    for run_id, mission_id in mission_by_run.items():
        if node_by_id.get(mission_id, {}).get("run_id") == run_id:
            result[mission_id] = True
            pending.discard(mission_id)

    changed = True
    while changed and pending:
        changed = False
        for node_id in sorted(tuple(pending)):
            node = node_by_id[node_id]
            run_id = node.get("run_id")
            mission_id = mission_by_run.get(run_id) if isinstance(run_id, str) else None
            if mission_id is None:
                result[node_id] = False
                pending.remove(node_id)
                changed = True
                continue

            parents = parents_by_child.get(node_id, ())
            if not parents:
                result[node_id] = False
                pending.remove(node_id)
                changed = True
                continue

            invalid_parent = False
            for parent_id in parents:
                parent = node_by_id.get(parent_id)
                if parent is None or parent.get("run_id") != run_id:
                    invalid_parent = True
                    break
            if invalid_parent:
                result[node_id] = False
                pending.remove(node_id)
                changed = True
                continue

            if any(result.get(parent_id) is False for parent_id in parents):
                result[node_id] = False
                pending.remove(node_id)
                changed = True
                continue
            if all(result.get(parent_id) is True for parent_id in parents):
                result[node_id] = True
                pending.remove(node_id)
                changed = True

    # Any nodes left pending are in, or depend on, an unresolved cycle.
    for node_id in pending:
        result[node_id] = False
    return result


__all__ = ["hyo_chain_all_parents", "parent_sets", "single_parent_map"]
