"""Tests for `hyodo graph export` (Package 2-C) and the pure `graph_export` module.

Covers the three 2-C test-plan rows
(`docs/superpowers/specs/2026-09-06-hyodo-agent-os-stage2-design.md:833-835`):
a pre-1-B ledger exports with empty `edges`/`backlinks`; every
`evidence_refs` entry appears as a `backlinks` entry keyed by the event it
cites; a claim with no `evidence_refs` is advisory, never a failure. Also
covers the confirmation/write/exit contract and the `clusters` shape.
"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.graph_export import (
    CLUSTER_PILLAR_KEYS,
    GRAPH_EXPORT_SCHEMA_VERSION,
    build_graph_export,
    compute_backlinks,
    compute_clusters,
)
from hyodo.report import build_report_graph

runner = CliRunner()


def _write_ledger(root: Path, events: list[dict[str, object]]) -> None:
    path = root / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(event) for event in events) + "\n", encoding="utf-8")


def _event(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "e0",
        "run_id": "run-1",
        "ts": "2026-09-06T00:00:00+00:00",
        "kind": "prompt",
        "actor": "human",
        "step_index": 0,
        "tool": {},
        "policy": {},
    }
    base.update(overrides)
    return base


# --------------------------------------------------------------------------
# Pure module: compute_backlinks / compute_clusters / build_graph_export
# --------------------------------------------------------------------------


def test_pre_1b_ledger_exports_with_empty_edges_and_backlinks(tmp_path: Path) -> None:
    # No parent_event_id/evidence_refs anywhere - an honestly empty graph.
    _write_ledger(tmp_path, [_event(event_id="m1")])
    graph = build_report_graph(tmp_path)
    export = build_graph_export(graph)

    assert export["schema"] == GRAPH_EXPORT_SCHEMA_VERSION
    assert export["edges"] == []
    assert export["backlinks"] == {}
    assert set(export["clusters"]) == set(CLUSTER_PILLAR_KEYS) | {"unclassified"}
    assert all(ids == [] for ids in export["clusters"].values())


def test_every_evidence_refs_entry_appears_as_a_backlink_keyed_by_its_target(
    tmp_path: Path,
) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
                tool={"name": "pytest"},
            ),
            _event(
                event_id="d1",
                kind="decision",
                actor="hyodo",
                step_index=2,
                parent_event_id="t1",
                evidence_refs=["t1"],
                policy={"decision": "ALLOW", "rule_id": None, "evaluated_by": "hyodo.policy/v1"},
            ),
        ],
    )
    graph = build_report_graph(tmp_path)
    export = build_graph_export(graph)

    # t1 is cited by d1's evidence_refs -> backlinks keyed by the cited
    # event (t1), listing the citing event (d1).
    assert export["backlinks"] == {"t1": ["d1"]}


def test_claim_with_no_evidence_refs_is_advisory_not_a_failure(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1", kind="prompt", actor="human", step_index=0),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
            ),
            _event(
                event_id="d1",
                kind="decision",
                actor="hyodo",
                step_index=2,
                parent_event_id="t1",
                # No evidence_refs at all - a claim (policy.reason) with no
                # backing evidence.
                policy={
                    "decision": "ALLOW",
                    "rule_id": None,
                    "evaluated_by": "hyodo.policy/v1",
                    "reason": "looks fine",
                },
            ),
        ],
    )
    graph = build_report_graph(tmp_path)
    export = build_graph_export(graph)

    assert graph["status"] == "READY"
    # d1 is never a backlinks key (nothing cites it) and is never a value
    # either (it cited nothing) - advisory, not surfaced as a failure.
    assert "d1" not in export["backlinks"]
    assert all("d1" not in citing for citing in export["backlinks"].values())
    # The decision itself still lands in a cluster (Goodness, at minimum).
    assert "d1" in export["clusters"]["goodness"]


def test_compute_backlinks_ignores_gate_references() -> None:
    edges = [
        {
            "type": "evidence_ref",
            "target_kind": "gate",
            "source": "gate:pytest",
            "target": "d1",
        },
        {
            "type": "evidence_ref",
            "target_kind": "event",
            "source": "t1",
            "target": "d1",
        },
    ]
    assert compute_backlinks(edges) == {"t1": ["d1"]}


def test_compute_clusters_keeps_all_six_spec_keys_plus_unclassified() -> None:
    nodes = [
        {"id": "d1", "kind": "decision", "decision": "ALLOW", "policy": {"rule_id": None}},
    ]
    clusters = compute_clusters(nodes)
    assert set(clusters) == set(CLUSTER_PILLAR_KEYS) | {"unclassified"}
    assert clusters["eternity"] == []
    assert clusters["goodness"] == ["d1"]


# --------------------------------------------------------------------------
# CLI: `hyodo graph export`
# --------------------------------------------------------------------------


def test_export_without_yes_is_refused_when_not_interactive(tmp_path: Path) -> None:
    _write_ledger(tmp_path, [_event()])
    result = runner.invoke(app, ["graph", "export", "--root", str(tmp_path)])
    assert result.exit_code == 1, result.output
    assert "confirmation_required" in result.output
    assert not (tmp_path / ".hyodo" / "graph.json").exists()


def test_export_with_yes_writes_the_artifact(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1"),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                step_index=1,
                parent_event_id="m1",
            ),
        ],
    )
    result = runner.invoke(app, ["graph", "export", "--yes", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output

    out_path = tmp_path / ".hyodo" / "graph.json"
    assert out_path.exists()
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema"] == GRAPH_EXPORT_SCHEMA_VERSION
    assert len(payload["nodes"]) == 2


def test_export_nodes_mirror_report_actor_id_field(tmp_path: Path) -> None:
    _write_ledger(
        tmp_path,
        [
            _event(event_id="m1"),
            _event(
                event_id="t1",
                kind="tool_call",
                actor="agent",
                actor_id="worker",
                step_index=1,
                parent_event_id="m1",
            ),
        ],
    )
    result = runner.invoke(app, ["graph", "export", "--yes", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output

    out_path = tmp_path / ".hyodo" / "graph.json"
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in payload["nodes"]}
    assert nodes_by_id["m1"]["actor_id"] is None
    assert nodes_by_id["t1"]["actor_id"] == "worker"


def test_export_custom_out_path_is_honoured(tmp_path: Path) -> None:
    _write_ledger(tmp_path, [_event()])
    result = runner.invoke(
        app, ["graph", "export", "--yes", "--out", "custom/bridge.json", "--root", str(tmp_path)]
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "custom" / "bridge.json").exists()


def test_export_ledger_unreadable_exits_2(tmp_path: Path) -> None:
    path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("irrelevant", encoding="utf-8")
    path.chmod(0o000)
    try:
        result = runner.invoke(app, ["graph", "export", "--yes", "--root", str(tmp_path)])
    finally:
        path.chmod(0o644)
    assert result.exit_code == 2, result.output


def test_export_write_failure_exits_2(tmp_path: Path) -> None:
    _write_ledger(tmp_path, [_event()])
    # `--out` names an existing directory, so writing to it raises OSError.
    (tmp_path / "graph.json").mkdir()
    result = runner.invoke(
        app, ["graph", "export", "--yes", "--out", "graph.json", "--root", str(tmp_path)]
    )
    assert result.exit_code == 2, result.output


def test_export_succeeds_with_no_ledger_file_at_all(tmp_path: Path) -> None:
    # No `.hyodo/agent-events.jsonl` at all is an honest empty ledger, not
    # "unreadable" - export still succeeds.
    result = runner.invoke(app, ["graph", "export", "--yes", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    payload = json.loads((tmp_path / ".hyodo" / "graph.json").read_text(encoding="utf-8"))
    assert payload["nodes"] == []
    assert payload["edges"] == []
    assert payload["backlinks"] == {}
