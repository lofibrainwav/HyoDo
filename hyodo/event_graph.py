"""Deterministic graph export for the local agent-event evidence ledger."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from hyodo.events import content_digest, credential_shaped_path
from hyodo.graph_v2 import V1_SCHEMA, V2_SCHEMA, causal_parents, validate_graph_v2

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


def _io(event: dict[str, Any]) -> dict[str, Any]:
    block = event.get("io")
    return block if isinstance(block, dict) else {}


def _edge_issue(
    *, event_id: str | None, field: str, ref: str | None, reason: str
) -> dict[str, Any]:
    return {"event_id": event_id, "field": field, "ref": ref, "reason": reason}


def _parent_refs(event: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]]]:
    """Return validated causal parent ids plus field-level issues.

    v1 remains singular. v2 uses ``parent_event_ids`` and never falls back to
    ``parent_event_id``; silently mixing the two would recreate first-parent
    ambiguity at the schema boundary.
    """
    event_id = _event_id(event)
    schema = event.get("schema_version")
    issues: list[dict[str, Any]] = []

    if schema == V1_SCHEMA:
        raw = event.get("parent_event_id")
        if raw is None:
            return [], issues
        if not isinstance(raw, str) or not raw.strip():
            issues.append(
                _edge_issue(
                    event_id=event_id,
                    field="parent_event_id",
                    ref=None,
                    reason="invalid_ref",
                )
            )
            return [], issues
        return [raw.strip()], issues

    if schema == V2_SCHEMA:
        raw = event.get("parent_event_ids", [])
        if raw is None:
            raw = []
        if not isinstance(raw, list):
            issues.append(
                _edge_issue(
                    event_id=event_id,
                    field="parent_event_ids",
                    ref=None,
                    reason="invalid_ref_list",
                )
            )
            return [], issues
        invalid = [ref for ref in raw if not isinstance(ref, str) or not ref.strip()]
        if invalid:
            issues.append(
                _edge_issue(
                    event_id=event_id,
                    field="parent_event_ids",
                    ref=None,
                    reason="invalid_ref",
                )
            )
            return [], issues
        return causal_parents(event), issues

    issues.append(
        _edge_issue(
            event_id=event_id,
            field="schema_version",
            ref=str(schema) if schema is not None else None,
            reason="unsupported_schema",
        )
    )
    return [], issues


def validate_event_edges(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return fail-closed edge issues for v1/v2 graph links in *events*.

    Causal parents, citation refs, reference resolution, run boundaries and
    directed-cycle truth remain separate facts. Multi-parent topology is
    checked by the canonical Graph-v2 Tarjan oracle; no parent is selected as
    a legacy representative for a join.

    The Graph-v2 same-run parent boundary is additive. Historical v1 events
    keep their shipped cross-run-parent semantics so reading or recording v1
    ledgers does not change merely because a v2 consumer is installed.
    """
    event_ids = [_event_id(event) for event in events]
    counts = Counter(event_id for event_id in event_ids if event_id is not None)
    id_set = {event_id for event_id, count in counts.items() if count == 1}
    event_by_id = {
        event_id: event
        for event_id, event in zip(event_ids, events, strict=False)
        if event_id in id_set
    }
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

        parents, parent_issues = _parent_refs(event)
        issues.extend(parent_issues)
        field = (
            "parent_event_ids" if event.get("schema_version") == V2_SCHEMA else "parent_event_id"
        )
        for parent in parents:
            if parent == event_id:
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field=field,
                        ref=parent,
                        reason="self_cycle",
                    )
                )
                continue
            parent_event = event_by_id.get(parent)
            if parent_event is None:
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field=field,
                        ref=parent,
                        reason="unresolved_ref",
                    )
                )
                continue
            child_run = event.get("run_id")
            parent_run = parent_event.get("run_id")
            if (
                event.get("schema_version") == V2_SCHEMA
                and isinstance(child_run, str)
                and isinstance(parent_run, str)
                and child_run != parent_run
            ):
                issues.append(
                    _edge_issue(
                        event_id=event_id,
                        field=field,
                        ref=parent,
                        reason="cross_run_ref",
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
            elif ref.startswith("gate:"):
                continue
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

    topology = validate_graph_v2(events)
    for cycle in topology.cycles:
        if cycle.get("reason") != "join_cycle_edge":
            continue
        edge = cycle.get("edge")
        if not isinstance(edge, list) or len(edge) != 2:
            continue
        child, parent = edge
        if not isinstance(child, str) or not isinstance(parent, str):
            continue
        child_event = event_by_id.get(child, {})
        field = (
            "parent_event_ids"
            if child_event.get("schema_version") == V2_SCHEMA
            else "parent_event_id"
        )
        issues.append(
            _edge_issue(
                event_id=child,
                field=field,
                ref=parent,
                reason="cycle",
            )
        )

    # Preserve the shipped v1 field ordering: parent issues precede evidence
    # issues for the same event. V2 parent lists are already normalized and
    # deterministic by causal_parents(), so no global alphabetical reorder is
    # necessary (and doing one would silently change v1 CLI reason ordering).
    return issues


def build_event_graph(
    events: list[dict[str, Any]],
    *,
    corrupt: int = 0,
    ledger_unreadable: bool = False,
    root: Path | None = None,
) -> dict[str, Any]:
    """Build the public JSON graph shape from observed v1/v2 ledger events.

    The public graph schema remains additive ``hyodo.evidence-graph/v1`` so
    existing readers keep working. A v2 join is represented by multiple
    ``parent_event_id`` edges with the same target; no singular parent is
    invented. ``parent_event_ids`` is also copied onto each node as a
    deterministic readback aid.
    """
    edge_issues = validate_event_edges(events) if not ledger_unreadable else []
    topology = validate_graph_v2(events) if not ledger_unreadable else None
    contains_v2 = any(event.get("schema_version") == V2_SCHEMA for event in events)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    event_ids = {_event_id(event) for event in events}
    event_ids.discard(None)
    event_by_id = {
        event_id: event for event in events if (event_id := _event_id(event)) is not None
    }

    missions: dict[str, str | None] = {}
    mission_steps: dict[str, int] = {}
    for event in events:
        run_id = event.get("run_id")
        step = event.get("step_index")
        if isinstance(run_id, str):
            missions.setdefault(run_id, None)
            if (
                event.get("kind") == "prompt"
                and event.get("actor") == "human"
                and isinstance(step, int)
                and not isinstance(step, bool)
                and (run_id not in mission_steps or step < mission_steps[run_id])
            ):
                missions[run_id] = _event_id(event)
                mission_steps[run_id] = step
        event_id = _event_id(event)
        tool = _tool(event)
        policy = _policy(event)
        io = _io(event)
        urls = tool.get("urls")
        urls = urls if isinstance(urls, list) else []
        node_io: dict[str, Any] = {"output_digest": io.get("output_digest")}
        if isinstance(io.get("duration_ms"), int) and not isinstance(io.get("duration_ms"), bool):
            node_io["duration_ms"] = io["duration_ms"]
        parents, _ = _parent_refs(event)
        node = {
            "id": event_id,
            "type": "event",
            "schema_version": event.get("schema_version"),
            "run_id": event.get("run_id"),
            "ts": event.get("ts"),
            "kind": event.get("kind"),
            "actor": event.get("actor"),
            "actor_id": event.get("actor_id"),
            "step_index": event.get("step_index"),
            "parent_event_ids": parents,
            "decision": policy.get("decision"),
            "io": node_io,
            "policy": {
                "rule_id": policy.get("rule_id"),
                "reason": policy.get("reason"),
                "evaluated_by": policy.get("evaluated_by"),
            },
            "tool": {
                "name": tool.get("name"),
                "method": tool.get("method"),
                "paths": _string_list(tool.get("paths")),
                "urls": [
                    {
                        "domain": entry.get("domain"),
                        "digest": entry.get("digest") or content_digest(entry.get("path")),
                        "credential_shaped": credential_shaped_path(entry["path"])
                        if isinstance(entry.get("path"), str)
                        else entry.get("credential_shaped")
                        if isinstance(entry.get("credential_shaped"), bool)
                        else None,
                    }
                    for entry in urls
                    if isinstance(entry, dict)
                ],
            },
        }
        nodes.append(node)
        if event_id is None:
            continue

        for parent in parents:
            parent_event = event_by_id.get(parent)
            if (
                parent_event is not None
                and parent != event_id
                and (
                    event.get("schema_version") != V2_SCHEMA
                    or parent_event.get("run_id") == event.get("run_id")
                )
            ):
                edges.append(
                    {
                        "type": "parent_event_id",
                        "source": parent,
                        "target": event_id,
                        "label": "result_of",
                    }
                )
        for ref in _string_list(event.get("evidence_refs")):
            if ref.startswith("gate:") or (ref in event_ids and ref != event_id):
                edges.append(
                    {
                        "type": "evidence_ref",
                        "kind": "evidence",
                        "target_kind": "gate" if ref.startswith("gate:") else "event",
                        "source": ref,
                        "target": event_id,
                        "label": "decided_from",
                    }
                )

    # V1 graph order is a shipped readback contract. Only graphs containing
    # Graph-v2 rows need canonicalized multi-parent edge ordering.
    if contains_v2:
        edges.sort(
            key=lambda edge: (
                str(edge.get("target")),
                str(edge.get("type")),
                str(edge.get("source")),
            )
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

    topology_payload = None
    if topology is not None:
        topology_payload = {
            "acyclic": topology.acyclic,
            "references_resolved": topology.references_resolved,
            "structurally_valid": topology.structurally_valid,
            "components": topology.components,
            "cycles": topology.cycles,
            "cross_run_refs": topology.cross_run_refs,
        }

    return {
        "schema_version": GRAPH_SCHEMA_VERSION,
        "status": status,
        "reason": reason,
        "root": str(root.resolve()) if root is not None else None,
        "nodes": nodes,
        "edges": edges,
        "unresolved_refs": edge_issues,
        "missions": missions,
        "topology": topology_payload,
        "summary": {
            "intent_unobserved_runs": sorted(
                run for run, mission in missions.items() if mission is None
            ),
            "gate_refs": sum(edge.get("target_kind") == "gate" for edge in edges),
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
