"""Contracts for the local, evidence-only FDE sign-off report."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.events import AGENT_EVENT_SCHEMA_VERSION, AGENT_EVENTS_RELATIVE_PATH, content_digest

runner = CliRunner()


def _write_evidence(root: Path) -> None:
    hyodo_dir = root / ".hyodo"
    hyodo_dir.mkdir()
    (hyodo_dir / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\nallowed_tools = ["safe"]\n', encoding="utf-8"
    )
    # ``evaluated_by`` is what makes a decision countable evidence. Without it an entry
    # is only a caller assertion — test_policy_self_report_boundary.py pins that an
    # unstamped ALLOW is reported as unevaluated instead of tallied.
    events = [
        {"policy": {"decision": "ALLOW", "evaluated_by": "hyodo.policy/v1"}},
        {"policy": {"decision": "DENY", "evaluated_by": "hyodo.policy/v1"}},
    ]
    (hyodo_dir / "agent-events.jsonl").write_text(
        "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
    )
    (hyodo_dir / "eval-runs.jsonl").write_text(
        json.dumps({"status": "PASS", "pass_rate": 0.75, "result_path": ".hyodo/eval-runs/a.json"})
        + "\n",
        encoding="utf-8",
    )


def test_report_is_hash_stable_and_never_marks_missing_schema_as_pass(tmp_path: Path) -> None:
    _write_evidence(tmp_path)
    first = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "md", "--json"])
    second = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "md", "--json"])

    assert first.exit_code == second.exit_code == 0
    first_summary = json.loads(first.output)
    assert first_summary["report_hash"] == json.loads(second.output)["report_hash"]
    report = (tmp_path / first_summary["result_path"]).read_text(encoding="utf-8")
    assert "Events: 2 (ALLOW: 1, DENY: 1)" in report
    assert "Eval pass rate: 75.0%" in report
    assert "Schema gate results: Not measured" in report
    assert "Schema gate results: PASS" not in report
    assert "## Human sign-off" in report


def test_report_renders_local_html_and_marks_all_missing_evidence_not_measured(
    tmp_path: Path,
) -> None:
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "html", "--json"])

    assert result.exit_code == 0
    summary = json.loads(result.output)
    html = (tmp_path / summary["result_path"]).read_text(encoding="utf-8")
    assert html.startswith("<!doctype html>")
    assert "Not measured" in html
    assert "Eval pass rate: Not measured" in html


def _graph_event(
    event_id: str,
    *,
    parent_event_id: str | None = None,
    evidence_refs: list[str] | None = None,
    step_index: int = 0,
    actor: str = "agent",
    actor_id: str | None = None,
    run_id: str = "run-graph-1",
    kind: str = "tool_call",
) -> dict:
    return {
        "schema_version": AGENT_EVENT_SCHEMA_VERSION,
        "event_id": event_id,
        "run_id": run_id,
        "ts": f"2026-09-06T20:00:0{step_index}+00:00",
        "kind": kind,
        "actor": actor,
        "actor_id": actor_id,
        "step_index": step_index,
        "parent_event_id": parent_event_id,
        "evidence_refs": evidence_refs or [],
        "tool": {
            "name": "web_fetch",
            "method": "GET",
            "paths": ["README.md"],
            "urls": [{"domain": "example.com", "path": "/docs"}],
        },
        "io": {
            "input_digest": None,
            "output_digest": None,
            "bytes_in": 0,
            "bytes_out": 0,
        },
        "policy": {
            "decision": "ALLOW",
            "rule_id": "test",
            "reason": "unit",
            "evaluated_by": "hyodo.policy/v1",
        },
        "meta": {"model": None, "tags": []},
    }


def test_report_graph_exports_edges_and_tool_urls(tmp_path: Path) -> None:
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    events = [
        _graph_event("parent", step_index=0),
        _graph_event("child", parent_event_id="parent", evidence_refs=["parent"], step_index=1),
    ]
    ledger.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"])

    assert result.exit_code == 0
    summary = json.loads(result.output)
    assert summary["status"] == "READY"
    assert summary["result_path"] == ".hyodo/reports/hyodo-report.graph.json"
    assert summary["parent_links"] == 1
    assert summary["evidence_refs"] == 1
    graph = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    assert graph["schema_version"] == "hyodo.evidence-graph/v1"
    assert graph["summary"]["events"] == 2
    assert graph["summary"]["edges"] == 2
    assert graph["unresolved_refs"] == []
    assert graph["nodes"][0]["tool"]["urls"] == [
        {"domain": "example.com", "digest": content_digest("/docs"), "credential_shaped": False}
    ]


def test_report_graph_nodes_carry_actor_id_field(tmp_path: Path) -> None:
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    events = [
        _graph_event("no-label", step_index=0),
        _graph_event("labelled", actor_id="planner", step_index=1),
    ]
    ledger.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"])

    assert result.exit_code == 0
    summary = json.loads(result.output)
    graph = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    assert nodes_by_id["no-label"]["actor_id"] is None
    assert nodes_by_id["labelled"]["actor_id"] == "planner"


def test_report_graph_rows_show_two_labelled_agents_and_orchestrator_nesting(
    tmp_path: Path,
) -> None:
    """Demo: mission -> agent A ("planner") tool_call -> agent B ("worker")
    whose first event's parent is A's tool_call. Two agent rows, B nests
    under A, and A is the orchestrator.
    """
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    events = [
        _graph_event("mission", actor="human", kind="prompt", step_index=0),
        _graph_event(
            "a-call",
            actor="agent",
            actor_id="planner",
            parent_event_id="mission",
            step_index=1,
        ),
        _graph_event(
            "b-first",
            actor="agent",
            actor_id="worker",
            parent_event_id="a-call",
            step_index=2,
        ),
    ]
    ledger.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")

    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"])

    assert result.exit_code == 0
    summary = json.loads(result.output)
    graph = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    rows = graph["rows"]["rows"]
    assert "agent:planner" in rows
    assert "agent:worker" in rows
    assert rows["agent:worker"]["parent_row"] == "agent:planner"
    assert rows["agent:worker"]["depth"] == rows["agent:planner"]["depth"] + 1
    assert rows["agent:planner"]["role"] == "orchestrator"
    assert rows["agent:worker"]["role"] == "worker"


def test_report_graph_fails_closed_on_broken_parent_ref(tmp_path: Path) -> None:
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger.parent.mkdir(parents=True, exist_ok=True)
    event = _graph_event("child", parent_event_id="missing", step_index=0)
    ledger.write_text(json.dumps(event) + "\n", encoding="utf-8")

    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"])

    assert result.exit_code == 2
    summary = json.loads(result.output)
    assert summary["status"] == "UNOBSERVED"
    assert summary["reason"] == "edge_validation_failed"
    graph = json.loads((tmp_path / summary["result_path"]).read_text(encoding="utf-8"))
    assert graph["unresolved_refs"] == [
        {
            "event_id": "child",
            "field": "parent_event_id",
            "ref": "missing",
            "reason": "unresolved_ref",
        }
    ]


@pytest.mark.parametrize(
    ("flag", "mission", "code"), [(False, False, 0), (True, False, 2), (True, True, 0)]
)
def test_graph_mission_policy(tmp_path, flag, mission, code):
    folder = tmp_path / ".hyodo"
    folder.mkdir()
    (folder / "policy.toml").write_text(
        'schema = "hyodo.policy/v1"\nrequire_mission_prompt = ' + str(flag).lower()
    )
    events = [_graph_event("tool", step_index=0)]
    if mission:
        for step in (3, 1, 2):
            event = _graph_event(f"prompt-{step}", step_index=step)
            event.update(kind="prompt", actor="human")
            events.append(event)
    (folder / "agent-events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in events))
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"])
    assert result.exit_code == code, result.output
    graph = json.loads((folder / "reports/hyodo-report.graph.json").read_text())
    assert graph["missions"] == {"run-graph-1": "prompt-1" if mission else None}
    assert graph["summary"]["intent_unobserved_runs"] == ([] if mission else ["run-graph-1"])
    assert graph["reason"] == ("mission_unobserved:run-graph-1" if code == 2 else None)


@pytest.mark.parametrize("config", [None, 'require_mission_prompt = "invalid"'])
def test_graph_missing_or_invalid_policy_keeps_existing_behavior(tmp_path, config):
    folder = tmp_path / ".hyodo"
    folder.mkdir()
    if config is not None:
        (folder / "policy.toml").write_text('schema = "hyodo.policy/v1"\n' + config)
    (folder / "agent-events.jsonl").write_text(json.dumps(_graph_event("tool")) + "\n")
    result = runner.invoke(app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"])
    assert result.exit_code == 0, result.output


def test_graph_missions_multiple_runs_and_event_target_kind():
    from hyodo.event_graph import build_event_graph

    first = _graph_event("first")
    second = _graph_event("second", evidence_refs=["first"])
    first["run_id"] = "z"
    second["run_id"] = "a"
    graph = build_event_graph([first, second])
    assert graph["missions"] == {"z": None, "a": None}
    assert graph["summary"]["intent_unobserved_runs"] == ["a", "z"]
    assert graph["edges"][0]["target_kind"] == "event"
    assert graph["summary"]["gate_refs"] == 0
