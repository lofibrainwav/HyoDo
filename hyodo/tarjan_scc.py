"""Deterministic Tarjan SCC oracle for HyoDo parent/join graphs.

The graph direction used here is ``child -> parent``.  This module is a pure
graph helper: it does not read the ledger, interpret ``evidence_refs``, make a
policy decision, or change the friction preview's actor/step calculation.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

Node = str
Edge = tuple[Node, Node]


@dataclass(frozen=True)
class SCCResult:
    """One deterministic SCC decomposition and its cycle findings."""

    acyclic: bool
    components: list[list[Node]]
    cycles: list[dict[str, Any]]


def _normalise_nodes(nodes: Iterable[object]) -> list[Node]:
    return sorted({node.strip() for node in nodes if isinstance(node, str) and node.strip()})


def _normalise_edges(nodes: set[Node], edges: Iterable[object]) -> list[Edge]:
    normalised: set[Edge] = set()
    for edge in edges:
        if not isinstance(edge, (tuple, list)) or len(edge) != 2:
            continue
        child, parent = edge
        if (
            isinstance(child, str)
            and isinstance(parent, str)
            and child.strip() in nodes
            and parent.strip() in nodes
        ):
            normalised.add((child.strip(), parent.strip()))
    return sorted(normalised)


def tarjan_scc(nodes: Iterable[object], edges: Iterable[object]) -> SCCResult:
    """Return sorted strongly connected components using Tarjan's algorithm.

    Edges whose endpoints are not in ``nodes`` are ignored.  This keeps an
    unresolved parent reference outside the SCC result; callers can report it
    separately as ``unresolved_ref``.  The DFS uses explicit frames rather
    than Python recursion, so a long parent chain cannot exhaust the call
    stack.
    """

    ordered_nodes = _normalise_nodes(nodes)
    node_set = set(ordered_nodes)
    ordered_edges = _normalise_edges(node_set, edges)
    adjacency: dict[Node, list[Node]] = {node: [] for node in ordered_nodes}
    for child, parent in ordered_edges:
        adjacency[child].append(parent)

    indices: dict[Node, int] = {}
    lowlinks: dict[Node, int] = {}
    stack: list[Node] = []
    on_stack: set[Node] = set()
    components: list[list[Node]] = []
    next_index = 0

    for root in ordered_nodes:
        if root in indices:
            continue

        indices[root] = next_index
        lowlinks[root] = next_index
        next_index += 1
        stack.append(root)
        on_stack.add(root)
        frames: list[tuple[Node, int]] = [(root, 0)]

        while frames:
            node, offset = frames[-1]
            if offset < len(adjacency[node]):
                neighbour = adjacency[node][offset]
                frames[-1] = (node, offset + 1)
                if neighbour not in indices:
                    indices[neighbour] = next_index
                    lowlinks[neighbour] = next_index
                    next_index += 1
                    stack.append(neighbour)
                    on_stack.add(neighbour)
                    frames.append((neighbour, 0))
                elif neighbour in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[neighbour])
                continue

            frames.pop()
            if lowlinks[node] == indices[node]:
                component: list[Node] = []
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(sorted(component))

            if frames:
                parent, _ = frames[-1]
                lowlinks[parent] = min(lowlinks[parent], lowlinks[node])

    components.sort()
    component_by_node = {node: component for component in components for node in component}
    cycles: list[dict[str, Any]] = []
    for component in components:
        if len(component) == 1:
            node = component[0]
            if (node, node) in ordered_edges:
                cycles.append(
                    {"reason": "self_cycle", "component": component, "edge": [node, node]}
                )
            continue

        cycles.append({"reason": "join_cycle", "component": component})
        internal_edges = [
            [child, parent]
            for child, parent in ordered_edges
            if child in component_by_node
            and parent in component_by_node
            and component_by_node[child] == component
            and component_by_node[parent] == component
        ]
        cycles.extend(
            {
                "reason": "join_cycle_edge",
                "component": component,
                "edge": edge,
            }
            for edge in internal_edges
        )

    return SCCResult(acyclic=not cycles, components=components, cycles=cycles)


def has_directed_cycle(nodes: Iterable[object], edges: Iterable[object]) -> bool:
    """Return only whether the directed graph contains a cycle."""

    return not tarjan_scc(nodes, edges).acyclic


def _parent_refs(event: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    parent_event_id = event.get("parent_event_id")
    if isinstance(parent_event_id, str) and parent_event_id.strip():
        refs.append(parent_event_id.strip())

    # `parent_event_ids` is an additive adapter shape for multi-parent join
    # inputs. The v1 event schema remains singular; normal v1 events use the
    # field above.
    parent_event_ids = event.get("parent_event_ids")
    if isinstance(parent_event_ids, list):
        refs.extend(ref.strip() for ref in parent_event_ids if isinstance(ref, str) and ref.strip())
    return sorted(set(refs))


def hyodo_parent_edges(events: Iterable[object]) -> tuple[list[Node], list[Edge]]:
    """Extract resolved HyoDo parent edges as ``child -> parent``.

    Only event ids and parent pointers participate.  ``evidence_refs`` are
    intentionally ignored.  Parent ids that do not exist in the event-id set
    are skipped and therefore remain unresolved references, not SCC nodes.
    """

    event_rows = [event for event in events if isinstance(event, Mapping)]
    nodes = _normalise_nodes(event.get("event_id") for event in event_rows)
    node_set = set(nodes)
    edges = sorted(
        {
            (child, parent)
            for event in event_rows
            for child in [event.get("event_id")]
            if isinstance(child, str) and child.strip() in node_set
            for parent in _parent_refs(event)
            if parent in node_set
        }
    )
    return nodes, edges


__all__ = ["SCCResult", "has_directed_cycle", "hyodo_parent_edges", "tarjan_scc"]
