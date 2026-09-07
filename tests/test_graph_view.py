"""Pure column/orb layout contracts for the local evidence-graph viewer.

Covers the event -> virtue mapping table, the unclassified gutter, the
structural Hyo chain check, column coverage counts, and the orb's three
signals — spec sections 2-4 of
`docs/superpowers/specs/2026-09-06-hyodo-core-engine-monitor-design.md`.
"""

from __future__ import annotations

import json
from typing import Any

from hyodo.graph_view import (
    UNCLASSIFIED,
    VIRTUE_COLUMNS,
    assign_columns,
    build_actor_rings,
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
    actor_id: str | None = None,
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
        "actor_id": actor_id,
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
    assert [tree["rows"][key]["label"] for key in tree["order"]] == ["human", "hyodo", "agent"]
    assert all(row["parent_row"] is None for row in tree["rows"].values())


def test_agent_row_nests_under_the_actor_whose_tool_call_it_descends_from() -> None:
    parent_tool_call = _node("p1", actor="hyodo", kind="tool_call", step_index=0)
    sub_agent_first = _node("s1", actor="agent", tool_name="planner_step", step_index=1)
    nodes = [parent_tool_call, sub_agent_first]
    edges = [_edge("p1", "s1")]
    tree = build_actor_rows(nodes, edges)
    agent_row = tree["rows"]["agent:s1"]
    assert agent_row["label"] == "agent:planner_step"
    assert agent_row["parent_row"] == "hyodo"


def test_agent_row_stays_top_level_without_a_cross_actor_parent() -> None:
    lone = _node("a1", actor="agent", tool_name="planner_step", step_index=0)
    tree = build_actor_rows([lone], [])
    assert tree["rows"]["agent:a1"]["parent_row"] is None


def test_one_agent_lineage_calling_different_tools_stays_a_single_unnested_row() -> None:
    # Regression: a real sub-agent calling pyright then pytest in sequence
    # must render as one row, never fragment into a fabricated nested row
    # keyed by each event's own tool.name.
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    first_call = _node("s1", actor="agent", kind="tool_call", tool_name="pyright", step_index=1)
    second_call = _node(
        "s2", actor="agent", kind="tool_result", tool_name="pytest -q", step_index=2
    )
    nodes = [mission, first_call, second_call]
    edges = [_edge("m1", "s1"), _edge("s1", "s2")]
    tree = build_actor_rows(nodes, edges)

    agent_rows = [key for key in tree["order"] if key.startswith("agent:")]
    assert len(agent_rows) == 1
    row = tree["rows"][agent_rows[0]]
    assert row["events"] == ["s1", "s2"]
    assert row["label"] == "agent:pyright"
    # m1 is a prompt, not a tool_call, so the lineage stays top-level.
    assert row["parent_row"] is None


def test_true_sub_agent_gets_exactly_one_nested_row_under_its_parent() -> None:
    parent_tool_call = _node("p1", actor="hyodo", kind="tool_call", step_index=0)
    sub_first = _node("s1", actor="agent", kind="tool_call", tool_name="planner", step_index=1)
    sub_second = _node(
        "s2", actor="agent", kind="tool_result", tool_name="different_tool", step_index=2
    )
    nodes = [parent_tool_call, sub_first, sub_second]
    edges = [_edge("p1", "s1"), _edge("s1", "s2")]
    tree = build_actor_rows(nodes, edges)

    nested_rows = [key for key in tree["order"] if tree["rows"][key]["parent_row"] == "hyodo"]
    assert len(nested_rows) == 1
    row = tree["rows"][nested_rows[0]]
    assert row["events"] == ["s1", "s2"]


# --- role / hyo_hierarchy (coordinator ruling, additive) -------------------


def _evidence_edge(cited: str, citing: str) -> dict[str, Any]:
    """One non-broken `evidence_refs` edge: *citing* cites *cited*."""
    return {
        "type": "evidence_ref",
        "kind": "evidence",
        "target_kind": "event",
        "source": cited,
        "target": citing,
        "label": "decided_from",
    }


def test_human_row_role_is_always_human() -> None:
    nodes = [_node("h1", kind="prompt", actor="human", step_index=0)]
    tree = build_actor_rows(nodes, [])
    assert tree["rows"]["human"]["role"] == "human"


def test_orchestrator_role_detected_via_parent_event_id_across_actors() -> None:
    # The `hyodo` actor's own event `p1` is the `parent_event_id` of the
    # `agent` lineage's first event `s1` — `hyodo` spawned a child lane.
    parent_call = _node("p1", actor="hyodo", kind="tool_call", step_index=0)
    child_first = _node("s1", actor="agent", tool_name="planner", step_index=1)
    nodes = [parent_call, child_first]
    edges = [_edge("p1", "s1")]
    tree = build_actor_rows(nodes, edges)
    assert tree["rows"]["hyodo"]["role"] == "orchestrator"
    assert tree["rows"]["agent:s1"]["role"] == "worker"


def test_reviewer_role_detected_when_citing_another_actor_with_no_write_tool_calls() -> None:
    # `hyodo` cites the agent's tool_call `t1` via evidence_refs and has no
    # write-shaped tool call of its own -> reviewer, not worker.
    tool_call = _node("t1", actor="agent", kind="tool_call", tool_name="pytest", step_index=0)
    decision = _node("d1", actor="hyodo", kind="decision", decision="ALLOW", step_index=1)
    nodes = [tool_call, decision]
    edges = [_edge("t1", "d1"), _evidence_edge("t1", "d1")]
    tree = build_actor_rows(nodes, edges)
    assert tree["rows"]["hyodo"]["role"] == "reviewer"


def test_citing_actor_with_a_write_shaped_tool_call_is_not_a_reviewer() -> None:
    tool_call = _node("t1", actor="agent", kind="tool_call", tool_name="pytest", step_index=0)
    writer_call = _node("w1", actor="hyodo", kind="tool_call", tool_name="file.write", step_index=1)
    decision = _node("d1", actor="hyodo", kind="decision", decision="ALLOW", step_index=2)
    nodes = [tool_call, writer_call, decision]
    edges = [_evidence_edge("t1", "d1")]
    tree = build_actor_rows(nodes, edges)
    assert tree["rows"]["hyodo"]["role"] == "worker"


def test_worker_with_a_disconnected_event_bumps_its_orchestrator_children_disconnected() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    parent_call = _node("p1", actor="hyodo", kind="tool_call", step_index=1)
    child_first = _node("s1", actor="agent", tool_name="planner", step_index=2)
    nodes = [mission, parent_call, child_first]
    # `s1` has no `parent_event_id` chain reaching the mission `m1` at all
    # (only `p1 -> s1` is linked, and `p1` itself has no parent), so the
    # child lane's `own_connected` is False.
    edges = [_edge("p1", "s1")]
    tree = build_actor_rows(nodes, edges)

    child_row = tree["rows"]["agent:s1"]
    assert child_row["role"] == "worker"
    assert child_row["hyo_hierarchy"]["own_connected"] is False

    orchestrator_row = tree["rows"]["hyodo"]
    assert orchestrator_row["role"] == "orchestrator"
    assert orchestrator_row["hyo_hierarchy"]["children"] == 1
    assert orchestrator_row["hyo_hierarchy"]["children_disconnected"] == 1


def test_hyo_hierarchy_own_connected_true_when_the_row_reaches_the_mission() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    call = _node("t1", actor="agent", tool_name="pytest", step_index=1)
    nodes = [mission, call]
    edges = [_edge("m1", "t1")]
    tree = build_actor_rows(nodes, edges)
    assert tree["rows"]["agent:t1"]["hyo_hierarchy"]["own_connected"] is True
    assert tree["rows"]["agent:t1"]["hyo_hierarchy"] == {
        "own_connected": True,
        "children": 0,
        "children_disconnected": 0,
    }


# --- build_actor_rings (Package 2-C, spec section 5) -----------------------


def _graph(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    return {"nodes": nodes, "edges": edges}


def test_actor_rings_empty_root_yields_unobserved_rings_for_every_row(tmp_path) -> None:
    nodes = [_node("h1", kind="prompt", actor="human", step_index=0)]
    graph = _graph(nodes, [])
    rings = build_actor_rings(graph, tmp_path)

    assert set(rings.keys()) == {"human"}
    row_rings = rings["human"]
    assert row_rings["skills"] == {"status": "unobserved", "skills": []}
    assert row_rings["memory"]["status"] == "unobserved"
    assert row_rings["routines"]["status"] == "unobserved"
    assert row_rings["tools"]["status"] == "unobserved"


def test_actor_rings_reads_skills_manifest_and_computes_pillar_profile(tmp_path) -> None:
    skill_path = tmp_path / "SKILL.md"
    skill_path.write_text(
        "## Rules\n- require test coverage for every public function\n", encoding="utf-8"
    )
    manifest_dir = tmp_path / ".hyodo" / "skills"
    manifest_dir.mkdir(parents=True)
    manifest = {
        "schema": "hyodo.skills-manifest/v1",
        "skills": [
            {
                "name": "demo-skill",
                "source": "path:SKILL.md",
                "content_digest": "digest",
                "status": "ok",
                "pillars": ["truth"],
                "compiled_rule_ids": [],
                "ingested_at": None,
                "body_stored": False,
            }
        ],
    }
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    # A parseable but non-mechanical rule never gets a `compiled_rule_ids`
    # entry, so re-derive the real rule id/compiled state the same way
    # `hyodo.skills.parse_skill_rules` would, and patch the manifest to
    # match, rather than hand-inventing an id the parser would never emit.
    from hyodo.skills import parse_skill_rules

    rules = parse_skill_rules("demo-skill", skill_path.read_text(encoding="utf-8"))
    compiled_ids = [rule.rule_id for rule in rules if rule.compiled is not None]
    manifest["skills"][0]["compiled_rule_ids"] = compiled_ids
    (manifest_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    nodes = [_node("h1", kind="prompt", actor="human", step_index=0)]
    rings = build_actor_rings(_graph(nodes, []), tmp_path)

    skills_ring = rings["human"]["skills"]
    assert skills_ring["status"] == "ok"
    assert len(skills_ring["skills"]) == 1
    entry = skills_ring["skills"][0]
    assert entry["name"] == "demo-skill"
    assert set(entry["pillar_profile"]) == {
        "truth",
        "goodness",
        "beauty",
        "benevolence",
        "hyo",
        "eternity",
    }


def test_actor_rings_memory_and_tools_reflect_this_row_only(tmp_path) -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    call = _node("t1", actor="agent", kind="tool_call", tool_name="pytest", step_index=1)
    decision = _node("d1", actor="hyodo", kind="decision", decision="ALLOW", step_index=2)
    nodes = [mission, call, decision]
    edges = [
        _edge("m1", "t1"),
        _edge("t1", "d1"),
        _evidence_edge("t1", "d1"),
    ]
    rings = build_actor_rings(_graph(nodes, edges), tmp_path)

    hyodo_memory = rings["hyodo"]["memory"]
    assert hyodo_memory["status"] == "ok"
    assert hyodo_memory["events"] == ["t1"]

    agent_tools = rings["agent:t1"]["tools"]
    assert agent_tools["status"] == "ok"
    assert agent_tools["tools"] == [{"name": "pytest", "decision": "ALLOW"}]


def test_actor_rings_unknown_key_absent_from_the_returned_dict(tmp_path) -> None:
    nodes = [_node("h1", kind="prompt", actor="human", step_index=0)]
    rings = build_actor_rings(_graph(nodes, []), tmp_path)
    assert "does-not-exist" not in rings


# --- build_actor_rows: actor_id row identity and nesting (owner ruling 2026-09-07) ---


def test_two_labelled_agents_in_one_run_are_two_rows() -> None:
    planner = _node("e1", actor="agent", actor_id="planner", step_index=0)
    worker = _node("e2", actor="agent", actor_id="worker", step_index=1)
    tree = build_actor_rows([planner, worker], [])
    assert "agent:planner" in tree["rows"]
    assert "agent:worker" in tree["rows"]
    assert tree["rows"]["agent:planner"]["events"] == ["e1"]
    assert tree["rows"]["agent:worker"]["events"] == ["e2"]
    assert tree["rows"]["agent:planner"]["label"] == "agent planner"


def test_labelled_agent_events_stay_one_row_regardless_of_topology() -> None:
    first = _node("e1", actor="agent", actor_id="worker", kind="tool_call", step_index=0)
    second = _node("e2", actor="agent", actor_id="worker", kind="tool_result", step_index=1)
    tree = build_actor_rows([first, second], [_edge("e1", "e2")])
    assert len(tree["order"]) == 1
    assert tree["rows"]["agent:worker"]["events"] == ["e1", "e2"]


def test_lane_root_stops_walking_at_a_differing_actor_id_boundary() -> None:
    # `p1` (actor_id "planner") is the parent_event_id of `w1` (actor_id
    # "worker") -- the walk must not merge them into one lineage even
    # though both are agent-actor and directly linked.
    planner_first = _node("p1", actor="agent", actor_id="planner", step_index=0)
    worker_first = _node("w1", actor="agent", actor_id="worker", step_index=1)
    tree = build_actor_rows([planner_first, worker_first], [_edge("p1", "w1")])
    assert set(tree["order"]) == {"agent:planner", "agent:worker"}


def test_child_row_nesting_sets_parent_row_and_depth() -> None:
    mission = _node("m1", kind="prompt", actor="human", step_index=0)
    planner_call = _node("p1", actor="agent", actor_id="planner", kind="tool_call", step_index=1)
    worker_first = _node("w1", actor="agent", actor_id="worker", step_index=2)
    nodes = [mission, planner_call, worker_first]
    edges = [_edge("m1", "p1"), _edge("p1", "w1")]
    tree = build_actor_rows(nodes, edges)

    assert tree["rows"]["human"]["depth"] == 0
    assert tree["rows"]["agent:planner"]["parent_row"] is None
    assert tree["rows"]["agent:planner"]["depth"] == 0
    assert tree["rows"]["agent:worker"]["parent_row"] == "agent:planner"
    assert tree["rows"]["agent:worker"]["depth"] == 1


def test_orchestrator_role_detected_across_two_labelled_agent_rows() -> None:
    planner_call = _node("p1", actor="agent", actor_id="planner", kind="tool_call", step_index=0)
    worker_first = _node("w1", actor="agent", actor_id="worker", step_index=1)
    nodes = [planner_call, worker_first]
    edges = [_edge("p1", "w1")]
    tree = build_actor_rows(nodes, edges)
    assert tree["rows"]["agent:planner"]["role"] == "orchestrator"
    assert tree["rows"]["agent:worker"]["role"] == "worker"
    assert tree["rows"]["agent:planner"]["hyo_hierarchy"]["children"] == 1


def test_backward_compatibility_without_actor_id_matches_existing_fixture() -> None:
    # Same fixture as
    # test_true_sub_agent_gets_exactly_one_nested_row_under_its_parent --
    # no actor_id anywhere, so rows/labels/nesting must be unchanged.
    parent_tool_call = _node("p1", actor="hyodo", kind="tool_call", step_index=0)
    sub_first = _node("s1", actor="agent", kind="tool_call", tool_name="planner", step_index=1)
    sub_second = _node(
        "s2", actor="agent", kind="tool_result", tool_name="different_tool", step_index=2
    )
    nodes = [parent_tool_call, sub_first, sub_second]
    edges = [_edge("p1", "s1"), _edge("s1", "s2")]
    tree = build_actor_rows(nodes, edges)

    assert tree["order"] == ["hyodo", "agent:s1"]
    assert tree["rows"]["hyodo"]["parent_row"] is None
    assert tree["rows"]["hyodo"]["depth"] == 0
    assert tree["rows"]["agent:s1"]["parent_row"] == "hyodo"
    assert tree["rows"]["agent:s1"]["depth"] == 1
    assert tree["rows"]["agent:s1"]["events"] == ["s1", "s2"]
    assert tree["rows"]["agent:s1"]["label"] == "agent:planner"
