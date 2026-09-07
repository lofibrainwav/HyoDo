"""Deterministic graph export for the local agent-event evidence ledger."""

from __future__ import annotations

import json
from collections import Counter
from typing import Any

GRAPH_SCHEMA_VERSION = "hyodo.evidence-graph/v1"


def _event_id(event: dict[str, Any]) -> str | None:
    value = event.get("event_id")
    return value if isinstance(value, str) and value.strip() else None


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _tool(event: dict[str, Any]) -> dict[str, Any]:
    block = event.get("tool")
    return block if isinstance(block, dict) else {}


def _policy(event: dict[str, Any]) -> dict[str, Any]:
    block = event.get("policy")
    return block if isinstance(block, dict) else {}


def _edge_issue(
    *, event_id: str | None, field: str, ref: str | None, reason: str
) -> dict[str, Any]:
    return {"event_id": event_id, "field": field, "ref": ref, "reason": reason}


def validate_event_edges(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return fail-closed edge issues for graph links in *events*.

    Event validation stays backward-compatible: ``parent_event_id`` and
    ``evidence_refs`` are optional. This graph validator is stricter because a
    graph edge that points nowhere must not be reported as a clean graph.
    """
    event_ids = [_event_id(event) for event in events]
    counts = Counter(event_id for event_id in event_ids if event_id is not None)
    id_set = {event_id for event_id, count in counts.items() if count == 1}
    issues: list[dict[str, Any]] = []

    for index, event in enumerate(events):
        event_id = event_ids[index]
        if event_id is None:
            issues.append(
                _edge_issue(
                    event_id=None,
                    field="event_id",
                    ref=None,
                    reason="missing_event_id",
                )
            )
            continue
        if counts[event_id] > 1:
            issues.append(
                _edge_issue(
                    event_id=event_id,
                    field="event_id",
                    ref=event_id,
                    reason="duplicate_event_id",
                )
            )

        parent = event.get("parent_event_id")
        if parent is not None:
            if not isinstance(parent, str) or not parent.strip():
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field="parent_event_id",
                        ref=None,
                        reason="invalid_ref",
                    )
                )
            elif parent == event_id:
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field="parent_event_id",
                        ref=parent,
                        reason="self_cycle",
                    )
                )
            elif parent not in id_set:
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field="parent_event_id",
                        ref=parent,
                        reason="unresolved_ref",
                    )
                )

        refs = event.get("evidence_refs", [])
        if refs is None:
            refs = []
        if not isinstance(refs, list):
            issues.append(
                _edge_issue(
                    event_id=event_id,
                    field="evidence_refs",
                    ref=None,
                    reason="invalid_ref_list",
                )
            )
            continue
        for ref in refs:
            if not isinstance(ref, str) or not ref.strip():
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field="evidence_refs",
                        ref=None,
                        reason="invalid_ref",
                    )
                )
            elif ref == event_id:
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field="evidence_refs",
                        ref=ref,
                        reason="self_ref",
                    )
                )
            elif ref not in id_set:
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field="evidence_refs",
                        ref=ref,
                        reason="unresolved_ref",
                    )
                )

    parent_map = {
        event_id: event.get("parent_event_id")
        for event_id, event in zip(event_ids, events, strict=False)
        if event_id in id_set and event.get("parent_event_id") in id_set
    }
    cycle_seen: set[tuple[str, str]] = set()
    for start in sorted(parent_map):
        path: list[str] = []
        current: str | None = start
        while current in parent_map:
            if current in path:
                cycle = path[path.index(current) :]
                for event_id in cycle:
                    parent = parent_map.get(event_id)
                    key = (event_id, parent or "")
                    if parent and key not in cycle_seen:
                        cycle_seen.add(key)
                        issues.append(
                            _edge_issue(
                                event_id=event_id,
                                field="parent_event_id",
                                ref=parent,
                                reason="cycle",
                            )
                        )
                break
            path.append(current)
            current = parent_map[current]
    return issues


def build_event_graph(
    events: list[dict[str, Any]], *, corrupt: int = 0, ledger_unreadable: bool = False
) -> dict[str, Any]:
    """Build the public JSON graph shape from observed ledger events."""
    edge_issues = validate_event_edges(events) if not ledger_unreadable else []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    event_ids = {_event_id(event) for event in events}
    event_ids.discard(None)

    for event in events:
        event_id = _event_id(event)
        tool = _tool(event)
        policy = _policy(event)
        node = {
            "id": event_id,
            "type": "event",
            "schema_version": event.get("schema_version"),
            "run_id": event.get("run_id"),
            "ts": event.get("ts"),
            "kind": event.get("kind"),
            "actor": event.get("actor"),
            "step_index": event.get("step_index"),
            "decision": policy.get("decision"),
            "policy": {
                "rule_id": policy.get("rule_id"),
                "reason": policy.get("reason"),
                "evaluated_by": policy.get("evaluated_by"),
            },
            "tool": {
                "name": tool.get("name"),
                "method": tool.get("method"),
                "paths": _string_list(tool.get("paths")),
                "urls": tool.get("urls") if isinstance(tool.get("urls"), list) else [],
            },
        }
        nodes.append(node)
        if event_id is None:
            continue

        parent = event.get("parent_event_id")
        if isinstance(parent, str) and parent in event_ids and parent != event_id:
            edges.append(
                {
                    "type": "parent_event_id",
                    "source": parent,
                    "target": event_id,
                    "label": "result_of",
                }
            )
        for ref in _string_list(event.get("evidence_refs")):
            if ref in event_ids and ref != event_id:
                edges.append(
                    {
                        "type": "evidence_ref",
                        "source": ref,
                        "target": event_id,
                        "label": "decided_from",
                    }
                )

    status = "READY"
    reason = None
    if ledger_unreadable:
        status = "UNOBSERVED"
        reason = "ledger_unreadable"
    elif corrupt:
        status = "UNOBSERVED"
        reason = "corrupt_event_lines"
    elif edge_issues:
        status = "UNOBSERVED"
        reason = "edge_validation_failed"

    return {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "status": status,
        "reason": reason,
        "nodes": nodes,
        "edges": edges,
        "unresolved_refs": edge_issues,
        "summary": {
            "events": len(events),
            "edges": len(edges),
            "parent_links": sum(edge["type"] == "parent_event_id" for edge in edges),
            "evidence_refs": sum(edge["type"] == "evidence_ref" for edge in edges),
            "unresolved_refs": len(edge_issues),
            "corrupt_event_lines": corrupt,
        },
    }


def render_event_graph_json(graph: dict[str, Any]) -> str:
    """Render graph JSON deterministically for hashing and diff review."""
    return json.dumps(graph, indent=2, sort_keys=True) + "\n"
