"""Pure column/orb layout contracts for the local evidence-graph viewer.

Covers the event -> virtue mapping table, the unclassified gutter, the
structural Hyo chain check, column coverage counts, and the orb's three
signals — spec sections 2-4 of
`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`.
"""

from __future__ import annotations

from typing import Any

from hyodo.graph_view import (
    UNCLASSIFIED,
    VIRTUE_COLUMNS,
    assign_columns,
    build_actor_rows,
    column_coverage,
    hyo_chain,
    orb_state,
)


def _node(
    node_id: str,
    *,
    kind: str = "tool_call",
    actor: str = "agent",
    decision: str | None = None,
    rule_id: str | None = None,
    tool_name: str | None = None,
    run_id: str = "run-1",
    step_index: int = 0,
    ts: str | None = None,
) -> dict[str, Any]:
    return {
        "id": node_id,
        "type": "event",
        "run_id": run_id,
        "ts": ts if ts is not None else f"2026-09-06T00:00:{step_index:02d}+00:00",
        "kind": kind,
        "actor": actor,
        "step_index": step_index,
        "decision": decision,
        "policy": {"rule_id": rule_id, "reason": None, "evaluated_by": None},
        "tool": {"name": tool_name, "method": None, "paths": [], "urls": []},
    }


def _edge(source: str, target: str) -> dict[str, Any]:
    return {"type": "parent_event_id", "source": source, "target": target, "label": "result_of"}


# --- assign_columns: mapping table (spec section 3) -----------------------


def test_decision_allow_maps_to_goodness() -> None:
    node = _node("e1", kind="decision", decision="ALLOW")
    assert assign_columns(node) == ["seon"]


def test_decision_deny_maps_to_goodness() -> None:
    node = _node("e1", kind="decision", decision="DENY")
    assert assign_columns(node) == ["seon"]


def test_decision_unobserved_renders_under_goodness_not_the_gutter() -> None:
    node = _node("e1", kind="decision", decision="UNOBSERVED")
    assert assign_columns(node) == ["seon"]


def test_decision_ask_spans_goodness_and_the_rule_implied_column() -> None:
    # The spec's own example: a data_boundary ASK is both a Goodness event
    # (a decision was made) and a Hyo event (declared-boundary data).
    node = _node("e1", kind="decision", decision="ASK", rule_id="data_boundary")
    assert assign_columns(node) == ["seon", "hyo"]


def test_typecheck_and_lint_tool_calls_map_to_truth() -> None:
    for name in ("pyright", "ruff check"):
        assert assign_columns(_node("e1", tool_name=name)) == ["jin"]


def test_test_runner_tool_call_maps_to_goodness() -> None:
    assert assign_columns(_node("e1", tool_name="pytest -q")) == ["seon"]


def test_formatter_tool_call_maps_to_beauty() -> None:
    assert assign_columns(_node("e1", tool_name="ruff format")) == ["jin", "mi"]


def test_doc_tool_call_maps_to_benevolence() -> None:
    assert assign_columns(_node("e1", tool_name="update_docs")) == ["in"]


def test_error_kind_maps_to_truth() -> None:
    assert assign_columns(_node("e1", kind="error")) == ["jin"]


def test_data_boundary_rule_id_maps_to_hyo_regardless_of_kind() -> None:
    node = _node("e1", kind="tool_result", rule_id="data_boundary_undeclared")
    assert assign_columns(node) == ["hyo"]


def test_web_credential_rule_id_maps_to_goodness_and_hyo() -> None:
    node = _node("e1", kind="tool_call", rule_id="web_credential_path_denied")
    assert assign_columns(node) == ["seon", "hyo"]


def test_prompt_and_model_response_carry_no_column_and_are_not_unclassified() -> None:
    assert assign_columns(_node("e1", kind="prompt", actor="human")) == []
    assert assign_columns(_node("e1", kind="model_response")) == []


def test_unmatched_event_lands_in_the_unclassified_gutter() -> None:
    node = _node("e1", tool_name="mystery_internal_tool")
    assert assign_columns(node) == [UNCLASSIFIED]


def test_column_order_is_always_the_fixed_spec_order() -> None:
    # rule_id-based hyo plus a tool-name-based truth match on the same node.
    node = _node("e1", kind="tool_result", tool_name="pyright", rule_id="data_boundary")
    assert assign_columns(node) == ["jin", "hyo"]
    assert list(VIRTUE_COLUMNS) == ["jin", "seon", "mi", "in", "hyo"]


# --- hyo_chain (spec section 3, structural) --------------------------------


def test_mission_event_itself_is_chained() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    chain = hyo_chain([mission], [])
    assert chain["m1"] is True


def test_event_whose_parent_chain_reaches_the_mission_is_chained() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    child = _node("c1", step_index=1)
    grandchild = _node("g1", step_index=2)
    nodes = [mission, child, grandchild]
    edges = [_edge("m1", "c1"), _edge("c1", "g1")]
    chain = hyo_chain(nodes, edges)
    assert chain == {"m1": True, "c1": True, "g1": True}


def test_orphan_event_with_no_parent_is_not_chained() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    orphan = _node("o1", step_index=1)
    chain = hyo_chain([mission, orphan], [])
    assert chain["o1"] is False


def test_chain_that_terminates_before_the_mission_is_not_chained() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    dangling = _node("d1", step_index=1)
    unresolved = _node("d2", step_index=2)
    nodes = [mission, dangling, unresolved]
    # d2 -> d1 -> (missing parent, never reaches m1)
    edges = [_edge("missing", "d1"), _edge("d1", "d2")]
    chain = hyo_chain(nodes, edges)
    assert chain["d2"] is False


def test_run_with_no_observed_mission_marks_every_event_unchained() -> None:
    lone = _node("e1", step_index=0)
    chain = hyo_chain([lone], [])
    assert chain["e1"] is False


# --- column_coverage --------------------------------------------------------


def test_column_coverage_counts_observed_and_expected_per_column() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    typecheck = _node("t1", tool_name="pyright", step_index=1)
    allow = _node("a1", kind="decision", decision="ALLOW", step_index=2)
    unobserved_decision = _node("u1", kind="decision", decision="UNOBSERVED", step_index=3)
    unclassified = _node("x1", tool_name="mystery", step_index=4)
    nodes = [mission, typecheck, allow, unobserved_decision, unclassified]
    edges = [_edge("m1", "a1")]
    assignments = {node["id"]: assign_columns(node) for node in nodes}
    coverage = column_coverage(nodes, assignments, edges)

    assert coverage["jin"] == {"observed": 1, "expected": 1}
    # Goodness: ALLOW (observed) + UNOBSERVED tile (assigned, not observed).
    assert coverage["seon"] == {"observed": 1, "expected": 2}
    assert coverage["mi"] == {"observed": 0, "expected": 0}
    assert coverage["in"] == {"observed": 0, "expected": 0}
    # Hyo is structural: chained/all events in the run, not mapping-table membership.
    assert coverage["hyo"] == {"observed": 2, "expected": 5}


# --- orb_state (spec section 4) --------------------------------------------


def test_orb_state_for_empty_ledger_is_unobserved_with_zero_coverage() -> None:
    graph = {"status": "READY", "nodes": [], "edges": []}
    state = orb_state(graph)
    assert state == {
        "decision": "UNOBSERVED",
        "coverage": {"observed": 0, "expected": 0},
        "latest_ts": None,
    }


def test_orb_state_reflects_the_latest_allow_decision() -> None:
    mission = _node(
        "m1", kind="prompt", actor="human", step_index=0, ts="2026-09-06T00:00:00+00:00"
    )
    older = _node(
        "d0", kind="decision", decision="DENY", step_index=1, ts="2026-09-06T00:00:01+00:00"
    )
    latest = _node(
        "d1", kind="decision", decision="ALLOW", step_index=2, ts="2026-09-06T00:00:02+00:00"
    )
    graph = {"status": "READY", "nodes": [mission, older, latest], "edges": []}
    state = orb_state(graph)
    assert state["decision"] == "ALLOW"
    assert state["latest_ts"] == "2026-09-06T00:00:02+00:00"


def test_orb_state_reflects_the_latest_deny_decision() -> None:
    older = _node(
        "d0", kind="decision", decision="ALLOW", step_index=0, ts="2026-09-06T00:00:00+00:00"
    )
    latest = _node(
        "d1", kind="decision", decision="DENY", step_index=1, ts="2026-09-06T00:00:01+00:00"
    )
    graph = {"status": "READY", "nodes": [older, latest], "edges": []}
    assert orb_state(graph)["decision"] == "DENY"


def test_orb_state_is_unobserved_when_the_ledger_itself_is_unobserved() -> None:
    latest = _node("d1", kind="decision", decision="ALLOW", step_index=0)
    graph = {
        "status": "UNOBSERVED",
        "reason": "ledger_unreadable",
        "nodes": [latest],
        "edges": [],
    }
    # The ledger could not be read at all — the orb must not claim a green
    # ALLOW it never actually observed.
    assert orb_state(graph)["decision"] == "UNOBSERVED"


def test_orb_state_never_prints_a_number_absent_from_the_column_badges() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    typecheck = _node("t1", tool_name="pyright", step_index=1)
    graph = {"status": "READY", "nodes": [mission, typecheck], "edges": []}
    state = orb_state(graph)
    assignments = {node["id"]: assign_columns(node) for node in graph["nodes"]}
    coverage = column_coverage(graph["nodes"], assignments, graph["edges"])
    assert state["coverage"]["observed"] == sum(c["observed"] for c in coverage.values())
    assert state["coverage"]["expected"] == sum(c["expected"] for c in coverage.values())


# --- build_actor_rows (spec section 2) -------------------------------------


def test_top_level_rows_for_human_hyodo_and_generic_agent() -> None:
    nodes = [
        _node("h1", kind="prompt", actor="human", step_index=0),
        _node("y1", actor="hyodo", step_index=1),
        _node("a1", actor="agent", step_index=2),
    ]
    tree = build_actor_rows(nodes, [])
    assert tree["order"] == ["human", "hyodo", "agent"]
    assert all(row["parent_row"] is None for row in tree["rows"].values())


def test_agent_row_nests_under_the_actor_whose_tool_call_it_descends_from() -> None:
    parent_tool_call = _node("p1", actor="hyodo", kind="tool_call", step_index=0)
    sub_agent_first = _node("s1", actor="agent", tool_name="planner_step", step_index=1)
    nodes = [parent_tool_call, sub_agent_first]
    edges = [_edge("p1", "s1")]
    tree = build_actor_rows(nodes, edges)
    assert tree["rows"]["agent:planner_step"]["parent_row"] == "hyodo"


def test_agent_row_stays_top_level_without_a_cross_actor_parent() -> None:
    lone = _node("a1", actor="agent", tool_name="planner_step", step_index=0)
    tree = build_actor_rows([lone], [])
    assert tree["rows"]["agent:planner_step"]["parent_row"] is None
