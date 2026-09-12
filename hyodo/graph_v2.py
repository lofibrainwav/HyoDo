"""Evidence Graph v2 contract and deterministic topology validation.

This module does not grant execution authority. It normalizes v1/v2 causal
parent references and reports graph structure as evidence only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hyodo.tarjan_scc import tarjan_scc

V1_SCHEMA = "hyodo.agent-event/v1"
V2_SCHEMA = "hyodo.agent-event/v2"


@dataclass(frozen=True)
class GraphV2Result:
    """Deterministic structural readback for a set of event rows."""

    acyclic: bool
    references_resolved: bool
    structurally_valid: bool
    normalized_events: list[dict[str, Any]]
    components: list[list[str]]
    cycles: list[dict[str, Any]]
    unresolved_refs: list[dict[str, str]]
    cross_run_refs: list[dict[str, str]]


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def causal_parents(event: dict[str, Any]) -> list[str]:
    """Return deterministic causal parents without reading evidence refs."""
    schema = event.get("schema_version")
    if schema == V1_SCHEMA:
        parent = _text(event.get("parent_event_id"))
        return [parent] if parent else []
    if schema == V2_SCHEMA:
        raw = event.get("parent_event_ids", [])
        if not isinstance(raw, list):
            return []
        parents: set[str] = set()
        for parent in raw:
            normalized_parent = _text(parent)
            if normalized_parent is not None:
                parents.add(normalized_parent)
        return sorted(parents)
    return []


def normalize_event(event: dict[str, Any]) -> dict[str, Any]:
    """Normalize v1 or v2 parent topology into the v2 graph view."""
    event_id = _text(event.get("event_id"))
    run_id = _text(event.get("run_id"))
    schema = event.get("schema_version")
    parents = causal_parents(event)
    legacy_parent = parents[0] if len(parents) == 1 else None
    return {
        "schema_version": schema,
        "event_id": event_id,
        "run_id": run_id,
        "parent_event_ids": parents,
        "legacy_parent_event_id": legacy_parent,
        "legacy_parent_representable": len(parents) <= 1,
    }


def validate_graph_v2(events: list[dict[str, Any]]) -> GraphV2Result:
    """Validate deterministic multi-parent topology for v1/v2 events.

    Missing parents and cross-run parents are excluded from SCC adjacency and
    reported separately. Therefore ``acyclic`` never implies that references
    are resolved or that the graph is structurally valid.
    """
    normalized = sorted(
        (normalize_event(event) for event in events),
        key=lambda row: (row.get("event_id") or "", row.get("run_id") or ""),
    )
    ids: dict[str, dict[str, Any]] = {}
    duplicate_ids: set[str] = set()
    malformed = False

    for row in normalized:
        event_id = row["event_id"]
        run_id = row["run_id"]
        schema = row["schema_version"]
        if event_id is None or run_id is None or schema not in {V1_SCHEMA, V2_SCHEMA}:
            malformed = True
            continue
        if event_id in ids:
            duplicate_ids.add(event_id)
        else:
            ids[event_id] = row

    unresolved: list[dict[str, str]] = []
    cross_run: list[dict[str, str]] = []
    edges: list[tuple[str, str]] = []

    for row in normalized:
        child = row["event_id"]
        run_id = row["run_id"]
        if child is None or child in duplicate_ids:
            continue
        for parent in row["parent_event_ids"]:
            parent_row = ids.get(parent)
            if parent_row is None or parent in duplicate_ids:
                unresolved.append({"event_id": child, "parent_event_id": parent})
                continue
            if parent_row["run_id"] != run_id:
                cross_run.append({"event_id": child, "parent_event_id": parent})
                continue
            edges.append((child, parent))

    unresolved.sort(key=lambda row: (row["event_id"], row["parent_event_id"]))
    cross_run.sort(key=lambda row: (row["event_id"], row["parent_event_id"]))
    scc = tarjan_scc(sorted(ids), sorted(set(edges)))
    references_resolved = not unresolved and not cross_run
    structurally_valid = not malformed and not duplicate_ids and references_resolved and scc.acyclic
    return GraphV2Result(
        acyclic=scc.acyclic,
        references_resolved=references_resolved,
        structurally_valid=structurally_valid,
        normalized_events=normalized,
        components=scc.components,
        cycles=scc.cycles,
        unresolved_refs=unresolved,
        cross_run_refs=cross_run,
    )
