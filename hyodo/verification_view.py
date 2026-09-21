"""Read-only presentation projection of one evidence graph.

This module answers two questions about an already-built
``hyodo.evidence-graph/v1`` payload: *what is proven* and *what is missing*.
It is a projection, not a measurement. Evidence fields are copied, filtered,
or re-grouped from the graph. Optional intent reviews delegate bounded scalar
comparisons to ``intent_review``; those compare host-supplied values, not the
meaning of a person's intent. No score, confidence, aggregate, or execution
authority is introduced.

Why this module exists
----------------------
``hyodo/report.py`` already ships ``rows`` (from
:func:`hyodo.graph_view.build_actor_rows`) on every graph payload, and those
rows already carry a lineage-derived ``role``. Two consumers ignored it and
re-derived participant lanes locally with weaker heuristics, so the same event
could land in different lanes on different surfaces. A single serialized
contract removes the room for that drift rather than asking each consumer to
remember not to guess.

Presentation contract
---------------------
The horizontal axis places recorded events in time; the vertical axis is
participants. Temporal placement is not an Eternity assessment. ``graph_view``'s
``VIRTUE_COLUMNS`` holds five measured columns; independent continuity assessment
remains separate from chronological ordering.

Causal edges and evidence edges are kept in two separate lists because they
mean different things. ``build_event_graph`` already emits them as distinct
edge types; collapsing them into one list here would destroy a distinction the
producer took care to record.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hyodo.graph_parenting import parent_sets
from hyodo.graph_view import (
    UNCLASSIFIED,
    UNMEASURED,
    assign_columns,
    carries_measured_evidence,
    column_coverage,
    hyo_chain,
)
from hyodo.intent_review import load_acceptance_join, project_intent_review

VERIFICATION_VIEW_SCHEMA_VERSION = "hyodo.verification-view/v0"

#: The horizontal axis is always time. Consumers must not re-map it.
TIME_DIRECTION = "left_to_right"

#: Compatibility metadata naming the related continuity lens. This association
#: does not equate chronology with a measured Eternity assessment.
CONTINUITY_LENS = "eternity"

#: A graph that could not resolve its own references has not earned an ALLOW.
#: Only ALLOW is withheld: withholding a DENY or an ASK would hide a problem
#: rather than avoid a false one. The recorded decision is never erased, so a
#: reader can always see what the ledger actually holds.
_READY_STATUS = "READY"
_WITHHELD_DECISION = "UNOBSERVED"

#: Field ordering for a node's causal position. ``step_index`` is the producer's
#: own ordinal; ``ts`` breaks ties without becoming a second time axis.
_ORDER_FIELDS = ("step_index", "ts")


def _text(value: Any) -> str | None:
    """Return a non-empty stripped string, or ``None``."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    return value or None


def _field(node: dict[str, Any], key: str) -> dict[str, Any]:
    """Return ``node[key]`` when it is a mapping, else an empty mapping."""
    value = node.get(key)
    return value if isinstance(value, dict) else {}


def _order_key(node: dict[str, Any]) -> tuple[int, str, str]:
    """Deterministic ordering for one node: step index, then timestamp, then id."""
    step = node.get("step_index")
    step_value = step if isinstance(step, int) and not isinstance(step, bool) else 0
    return (step_value, str(node.get("ts") or ""), str(node.get("id") or ""))


def _edges_of_type(edges: list[dict[str, Any]], edge_type: str) -> list[dict[str, Any]]:
    """Return the edges whose ``type`` matches, preserving producer order."""
    return [edge for edge in edges if isinstance(edge, dict) and edge.get("type") == edge_type]


def _five_w_one_h(node: dict[str, Any], *, allow_withheld: bool) -> dict[str, Any]:
    """Regroup one node's already-recorded fields under investigation headings.

    Nothing is derived here. Each heading names where an existing field is
    read from, so a reader can trace any cell back to the ledger. A heading
    with no recorded evidence stays ``None`` rather than being filled with a
    plausible-looking label.

    ``what.decision`` is always the recorded value.
    ``what.decision_presentable`` is what a viewer may show: the same value,
    except that an ``ALLOW`` recorded under a graph that did not resolve its
    own references is withheld as ``UNOBSERVED``. Presentation may compress
    toward unknown; it may not erase what the ledger recorded, so both fields
    are emitted side by side.
    """
    tool = _field(node, "tool")
    policy = _field(node, "policy")
    io = _field(node, "io")
    recorded_decision = _text(node.get("decision"))
    return {
        "who": {
            "actor": _text(node.get("actor")),
            "actor_id": _text(node.get("actor_id")),
            "from": _field(node, "participants").get("from"),
            "to": _field(node, "participants").get("to"),
        },
        "what": {
            "kind": _text(node.get("kind")),
            "tool_name": _text(tool.get("name")),
            "decision": recorded_decision,
            "decision_presentable": (
                _WITHHELD_DECISION
                if allow_withheld and recorded_decision == "ALLOW"
                else recorded_decision
            ),
        },
        "when": {
            "ts": _text(node.get("ts")),
            "step_index": node.get("step_index"),
        },
        "where": {
            "paths": list(tool.get("paths") or []),
            "urls": list(tool.get("urls") or []),
            "method": _text(tool.get("method")),
        },
        "why": {
            "reason": _text(policy.get("reason")),
            "run_id": _text(node.get("run_id")),
        },
        "how": {
            "tool_name": _text(tool.get("name")),
            "method": _text(tool.get("method")),
            "rule_id": _text(policy.get("rule_id")),
            "evaluated_by": _text(policy.get("evaluated_by")),
            "input_digest": _text(io.get("input_digest")),
            "output_digest": _text(io.get("output_digest")),
            "output_observation": _text(io.get("output_observation")) or "UNOBSERVED",
        },
    }


def _build_lanes(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Reshape the graph's own ``rows`` into ordered participant lanes.

    ``rows`` is ``build_actor_rows`` output and already carries the lineage
    ``role``. This function only changes the container shape; it never
    recomputes membership or role. When a graph payload has no ``rows`` (an
    older producer, or a hand-built fixture), the result is an empty lane list
    rather than a locally invented one.
    """
    rows = graph.get("rows")
    if not isinstance(rows, dict):
        return []
    order = rows.get("order")
    table = rows.get("rows")
    if not isinstance(order, list) or not isinstance(table, dict):
        return []
    lanes: list[dict[str, Any]] = []
    for lane_id in order:
        row = table.get(lane_id)
        if not isinstance(row, dict):
            continue
        lanes.append(
            {
                "lane_id": lane_id,
                "label": row.get("label"),
                "actor": row.get("actor"),
                "role": row.get("role"),
                "depth": row.get("depth"),
                "parent_lane": row.get("parent_row"),
                "events": list(row.get("events") or []),
                "hyo_hierarchy": row.get("hyo_hierarchy"),
            }
        )
    return lanes


def _decisions_by_run(
    nodes: list[dict[str, Any]], *, allow_withheld: bool
) -> dict[str, list[dict[str, Any]]]:
    """Group every recorded decision by run, without judging the group.

    Two decisions that disagree inside one run are both reported, in recorded
    order. This module does not label the pair a contradiction, average them,
    or let the later one hide the earlier one; that reading belongs to whoever
    reads the group.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        if node.get("kind") != "decision":
            continue
        run_id = _text(node.get("run_id"))
        if run_id is None:
            continue
        recorded = _text(node.get("decision"))
        grouped.setdefault(run_id, []).append(
            {
                "event_id": node.get("id"),
                "decision": recorded,
                "decision_presentable": (
                    _WITHHELD_DECISION if allow_withheld and recorded == "ALLOW" else recorded
                ),
                "ts": _text(node.get("ts")),
                "step_index": node.get("step_index"),
            }
        )
    for entries in grouped.values():
        entries.sort(key=lambda entry: (entry["step_index"] or 0, entry["ts"] or ""))
    return grouped


_TERMINAL_STATES = (
    "RETURNED",
    "ERROR",
    "CANCELLED",
    "TIMEOUT",
    "ABORTED",
    "UNOBSERVED",
    "CONTRADICTED",
)


def _terminal_dispositions(
    nodes: list[dict[str, Any]], causal_edges: list[dict[str, Any]]
) -> dict[str, dict[str, Any]]:
    """Derive one evidence-bounded terminal disposition per tool call.

    A recorded ``tool_result`` proves only that a terminal callback returned;
    it does not prove semantic success. Explicit error/cancel/timeout/abort
    states require direct host evidence. The current Codex producer exposes no
    such structured terminal fields, so missing callbacks remain UNOBSERVED.
    """
    node_by_id = {str(node["id"]): node for node in nodes if isinstance(node.get("id"), str)}
    observed_by_call: dict[str, list[tuple[str, str]]] = {}
    for edge in causal_edges:
        source = edge.get("source")
        target = edge.get("target")
        if not isinstance(source, str) or not isinstance(target, str):
            continue
        child = node_by_id.get(target)
        if child is None:
            continue
        state = "RETURNED" if child.get("kind") == "tool_result" else None
        if child.get("kind") == "error":
            state = "ERROR"
        if state is not None:
            observed_by_call.setdefault(source, []).append((target, state))

    dispositions: dict[str, dict[str, Any]] = {}
    for node in nodes:
        call_id = node.get("id")
        if node.get("kind") != "tool_call" or not isinstance(call_id, str):
            continue
        observed = sorted(observed_by_call.get(call_id, []))
        if not observed:
            state = "UNOBSERVED"
            source = None
        elif len(observed) == 1:
            state = observed[0][1]
            source = "tool_result" if state == "RETURNED" else "error_event"
        else:
            state = "CONTRADICTED"
            source = "duplicate_terminal"
        dispositions[call_id] = {
            "state": state,
            "cardinality": len(observed),
            "evidence_source": source,
            "event_ids": [event_id for event_id, _ in observed],
        }
    return dispositions


def _calls_without_result(
    nodes: list[dict[str, Any]], causal_edges: list[dict[str, Any]]
) -> list[str]:
    """Compatibility alias for tool calls with no observed terminal child."""
    terminal = _terminal_dispositions(nodes, causal_edges)
    return sorted(call_id for call_id, row in terminal.items() if row["state"] == "UNOBSERVED")


def _recording_disposition(node: dict[str, Any]) -> str:
    """Describe recording sufficiency without manufacturing payload fields."""
    if carries_measured_evidence(node):
        return "MEASURED"
    kind = node.get("kind")
    if kind == "decision" and _text(node.get("decision")):
        return "MEASURED"
    if kind == "error":
        return "MEASURED"
    if kind == "tool_call":
        return "INTENTIONALLY_MINIMAL"
    if kind == "prompt":
        return "STRUCTURAL_CONTEXT"
    return "MEASUREMENT_UNOBSERVED"


def _lens_mapping_disposition(node: dict[str, Any], columns: list[str]) -> str:
    """Separate semantic mapping gaps from absent measurement."""
    if node.get("kind") in ("tool_call", "tool_result") and not carries_measured_evidence(node):
        return "INSUFFICIENT_MEASUREMENT"
    if columns == [UNMEASURED]:
        return "INSUFFICIENT_MEASUREMENT"
    if columns == [UNCLASSIFIED]:
        tool = _field(node, "tool")
        policy = _field(node, "policy")
        if tool.get("paths") or tool.get("urls") or tool.get("method") or policy.get("rule_id"):
            return "MAPPING_GAP"
        return "SEMANTICS_UNOBSERVED"
    if not columns:
        return "NOT_APPLICABLE"
    return "MAPPED"


def _count_states(values: list[str], vocabulary: tuple[str, ...]) -> dict[str, int]:
    counts = dict.fromkeys(vocabulary, 0)
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _intent_provenance(missions: dict[str, Any]) -> dict[str, str]:
    """Classify recorded intent presence without inferring authorization."""
    return {
        run_id: "RECORDED_INTENT" if mission else "ADMISSION_UNOBSERVED"
        for run_id, mission in sorted(missions.items())
    }


def _evidence_edges(
    evidence_edges: list[dict[str, Any]], node_by_id: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    """Copy evidence edges and flag the ones recorded after what they support.

    ``source_after_target`` compares two values the ledger already holds. It is
    an ordering observation inside the single recorded time axis, not a second
    "when we learned it" axis; the event schema records no ingestion time, so
    no such axis can be reconstructed without inventing it.
    """
    projected: list[dict[str, Any]] = []
    for edge in evidence_edges:
        source = edge.get("source")
        target = edge.get("target")
        source_node = node_by_id.get(str(source)) if source is not None else None
        target_node = node_by_id.get(str(target)) if target is not None else None
        after: bool | None = None
        if source_node is not None and target_node is not None:
            after = _order_key(source_node)[:2] > _order_key(target_node)[:2]
        projected.append(
            {
                "source": source,
                "target": target,
                "target_kind": edge.get("target_kind"),
                "source_resolved": source_node is not None,
                "source_after_target": after,
            }
        )
    return projected


def build_verification_view(graph: dict[str, Any], *, root: Path | None = None) -> dict[str, Any]:
    """Project one ``hyodo.evidence-graph/v1`` payload for investigation.

    *graph* is a full graph payload as ``hyodo.report.build_report_graph`` or
    ``hyodo.event_graph.build_event_graph`` returns it. Passing the report
    variant is preferred because it already carries ``rows`` and ``backlinks``.

    *root* is forwarded unchanged to :func:`hyodo.graph_view.assign_columns`
    so the file-tool column split resolves paths against the same checkout the
    ledger was read with. Omitting it does not make this function guess; the
    affected events simply land in the unclassified gutter, exactly as they do
    everywhere else.

    The result grants no authority. ``authority`` is the literal
    ``"UNOBSERVED"``, matching every other HyoDo evidence surface, and the
    payload deliberately contains no score, confidence, or aggregate field.
    """
    nodes = [node for node in (graph.get("nodes") or []) if isinstance(node, dict)]
    edges = [edge for edge in (graph.get("edges") or []) if isinstance(edge, dict)]
    ordered_nodes = sorted(nodes, key=_order_key)
    node_by_id = {
        str(node["id"]): node for node in ordered_nodes if isinstance(node.get("id"), str)
    }

    causal_edges = _edges_of_type(edges, "parent_event_id")
    evidence_edges = _edges_of_type(edges, "evidence_ref")

    assignments = {node_id: assign_columns(node, root) for node_id, node in node_by_id.items()}
    chained = hyo_chain(ordered_nodes, edges)
    parents = parent_sets(edges)
    terminal_by_call = _terminal_dispositions(ordered_nodes, causal_edges)
    recording_by_event = {
        node_id: _recording_disposition(node) for node_id, node in node_by_id.items()
    }
    lens_by_event = {
        node_id: _lens_mapping_disposition(node, assignments[node_id])
        for node_id, node in node_by_id.items()
    }

    status = _text(graph.get("status"))
    # A graph that could not resolve its own references has not earned an
    # ALLOW. The flag is computed once, here, so every consumer reads the same
    # answer instead of each re-deciding it in its own language.
    allow_withheld = status != _READY_STATUS

    events: dict[str, Any] = {}
    unclassified: list[str] = []
    unmeasured: list[str] = []
    for node_id, node in node_by_id.items():
        columns = assignments[node_id]
        if columns == [UNCLASSIFIED]:
            unclassified.append(node_id)
        elif columns == [UNMEASURED]:
            unmeasured.append(node_id)
        entry = _five_w_one_h(node, allow_withheld=allow_withheld)
        entry["why"]["intent_review"] = project_intent_review(
            node, node_by_id, references_ready=not allow_withheld
        )
        entry["columns"] = [
            column for column in columns if column not in {UNCLASSIFIED, UNMEASURED}
        ]
        entry["gutter"] = (
            columns[0] if columns and columns[0] in {UNCLASSIFIED, UNMEASURED} else None
        )
        entry["hyo_chained"] = bool(chained.get(node_id))
        entry["causal_parents"] = list(parents.get(node_id, ()))
        entry["terminal"] = terminal_by_call.get(node_id)
        entry["recording_disposition"] = recording_by_event[node_id]
        entry["lens_mapping_disposition"] = lens_by_event[node_id]
        events[node_id] = entry

    topology = _field(graph, "topology")
    missions = _field(graph, "missions")
    intent_by_run = _intent_provenance(missions)
    terminal_counts = _count_states(
        [row["state"] for row in terminal_by_call.values()], _TERMINAL_STATES
    )
    recording_counts = _count_states(
        list(recording_by_event.values()),
        ("MEASURED", "INTENTIONALLY_MINIMAL", "STRUCTURAL_CONTEXT", "MEASUREMENT_UNOBSERVED"),
    )
    lens_counts = _count_states(
        list(lens_by_event.values()),
        (
            "MAPPED",
            "NOT_APPLICABLE",
            "INSUFFICIENT_MEASUREMENT",
            "SEMANTICS_UNOBSERVED",
            "MAPPING_GAP",
        ),
    )
    intent_counts = _count_states(
        list(intent_by_run.values()),
        ("RECORDED_INTENT", "ADMISSION_UNOBSERVED", "EXPLICIT_NO_INTENT"),
    )

    return {
        "schema_version": VERIFICATION_VIEW_SCHEMA_VERSION,
        "acceptance_join": load_acceptance_join(root),
        "status": graph.get("status"),
        "presentation": {
            "allow_withheld": allow_withheld,
            "reason": None if not allow_withheld else f"graph_status:{status or 'UNOBSERVED'}",
        },
        "reason": graph.get("reason"),
        "root": graph.get("root"),
        "authority": "UNOBSERVED",
        "reconciliation": {
            "terminal_outcomes": {
                "counts": terminal_counts,
                "terminal_outcome_unobserved": terminal_counts["UNOBSERVED"],
                "duplicate_terminal": terminal_counts["CONTRADICTED"],
                "undispositioned_calls": 0,
            },
            "recording": {
                "counts": recording_counts,
                "unexplained_required_gaps": 0,
            },
            "lens_mapping": {
                "counts": lens_counts,
                "mapping_gaps": lens_counts["MAPPING_GAP"],
            },
            "intent_provenance": {
                "counts": intent_counts,
                "by_run": intent_by_run,
                "undispositioned_runs": 0,
                "unauthorized_executions": "NOT_PROVEN",
            },
        },
        "time_axis": {
            "direction": TIME_DIRECTION,
            "continuity_lens": CONTINUITY_LENS,
            "order_fields": list(_ORDER_FIELDS),
        },
        "lanes": _build_lanes(graph),
        "event_order": [
            str(node["id"]) for node in ordered_nodes if isinstance(node.get("id"), str)
        ],
        "events": events,
        "edges_causal": [
            {"source": edge.get("source"), "target": edge.get("target")} for edge in causal_edges
        ],
        "edges_evidence": _evidence_edges(evidence_edges, node_by_id),
        "decisions_by_run": _decisions_by_run(ordered_nodes, allow_withheld=allow_withheld),
        "missing": {
            "unresolved_refs": list(graph.get("unresolved_refs") or []),
            "cross_run_refs": list(topology.get("cross_run_refs") or []),
            "unclassified_events": sorted(unclassified),
            "unmeasured_events": sorted(unmeasured),
            "calls_without_terminal_outcome": sorted(
                call_id for call_id, row in terminal_by_call.items() if row["state"] == "UNOBSERVED"
            ),
            "duplicate_terminal_outcomes": sorted(
                call_id
                for call_id, row in terminal_by_call.items()
                if row["state"] == "CONTRADICTED"
            ),
            "calls_without_result": _calls_without_result(ordered_nodes, causal_edges),
            "runs_without_intent": sorted(
                run_id for run_id, mission in missions.items() if not mission
            ),
        },
        "coverage": column_coverage(ordered_nodes, assignments, edges),
        "topology": {
            "acyclic": topology.get("acyclic"),
            "references_resolved": topology.get("references_resolved"),
            "structurally_valid": topology.get("structurally_valid"),
            "components": list(topology.get("components") or []),
            "cycles": list(topology.get("cycles") or []),
        },
    }
