"""Intent comparisons preserve provenance and never imply semantic approval."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from ledger_fixture import write_ledger

from hyodo.events import AGENT_EVENTS_RELATIVE_PATH, validate_event
from hyodo.intent_review import normalize_intent_review, project_intent_review
from hyodo.report import build_report_graph
from hyodo.verification_view import build_verification_view


def _review() -> dict[str, Any]:
    return {
        "schema_version": "hyodo.intent-review/v1",
        "intent_ref": "intent",
        "mode": "OBSERVED",
        "target": "outcome",
        "checks": [
            {
                "id": "budget",
                "dimension": "constraints",
                "basis": "DECLARED",
                "operator": "lte",
                "expected": 100,
                "actual": 130,
                "unit": "USD",
                "evidence_refs": ["result"],
            }
        ],
    }


def _nodes() -> dict[str, dict[str, Any]]:
    return {
        "intent": {
            "id": "intent",
            "kind": "prompt",
            "actor": "human",
            "ts": "2026-09-19T10:00:00+00:00",
        },
        "result": {
            "id": "result",
            "kind": "tool_result",
            "actor": "agent",
            "ts": "2026-09-19T10:01:00+00:00",
            "io": {"output_digest": "abcdef123456"},
        },
        "review": {
            "id": "review",
            "kind": "model_response",
            "actor": "agent",
            "actor_id": "reviewer",
            "ts": "2026-09-19T10:02:00+00:00",
            "intent_review": _review(),
        },
    }


def test_numeric_deviation_is_bounded_and_does_not_mutate_evidence() -> None:
    nodes = _nodes()
    before = copy.deepcopy(nodes)
    result = project_intent_review(nodes["review"], nodes)
    check = result["checks"][0]
    assert check["state"] == "DEVIATES"
    assert check["delta"] == 30
    assert check["unit"] == "USD"
    assert result["missing_dimensions"] == ["goal", "scope", "completion"]
    assert not {"score", "confidence", "authority", "approval", "total"} & result.keys()
    assert nodes == before


@pytest.mark.parametrize(
    "case",
    [
        "missing_intent",
        "not_human",
        "missing_result",
        "no_digest",
        "later_result",
        "later_intent",
        "unknown_time",
        "inferred",
        "projected",
        "no_actual",
        "self_ref",
        "no_refs",
        "invalid_graph",
    ],
)
def test_unsupported_alignment_stays_unobserved(case: str) -> None:
    nodes = _nodes()
    review = nodes["review"]["intent_review"]
    check = review["checks"][0]
    if case == "missing_intent":
        del nodes["intent"]
    elif case == "not_human":
        nodes["intent"]["actor"] = "agent"
    elif case == "missing_result":
        del nodes["result"]
    elif case == "no_digest":
        nodes["result"]["io"] = {}
    elif case == "later_result":
        nodes["result"]["ts"] = "2026-09-20T00:00:00+00:00"
    elif case == "later_intent":
        nodes["intent"]["ts"] = "2026-09-20T00:00:00+00:00"
    elif case == "unknown_time":
        nodes["review"]["ts"] = "not a timestamp"
    elif case == "inferred":
        check["basis"] = "INFERRED"
    elif case == "projected":
        review["mode"] = "PROJECTED"
    elif case == "no_actual":
        check["actual"] = None
    elif case == "self_ref":
        check["evidence_refs"] = ["review"]
    elif case == "no_refs":
        check["evidence_refs"] = []
    result = project_intent_review(nodes["review"], nodes, references_ready=case != "invalid_graph")
    assert result["checks"][0]["state"] == "UNOBSERVED"
    assert result["checks"][0]["missing"]


@pytest.mark.parametrize(
    "update",
    [
        {"actual": float("nan")},
        {"actual": float("inf")},
        {"actual": True},
        {"operator": "approximately"},
        {"dimension": "moral_total"},
        {"evidence_refs": "result"},
        {"basis": "APPROVED"},
        {"unit": ["USD"]},
        {"score": 99},
    ],
)
def test_malformed_comparison_is_rejected_at_event_ingestion(update: dict[str, Any]) -> None:
    review = _review()
    review["checks"][0].update(update)
    raw = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "review",
        "run_id": "r",
        "ts": "2026-09-19T00:00:00Z",
        "kind": "model_response",
        "actor": "agent",
        "step_index": 2,
        "meta": {"intent_review": review},
    }
    valid, reasons, normalized = validate_event(raw)
    assert not valid
    assert "invalid_field:meta.intent_review" in reasons
    assert normalized is None


def test_duplicate_requirements_cannot_inflate_counts() -> None:
    review = _review()
    review["checks"].append(dict(review["checks"][0]))
    assert normalize_intent_review(review) is None


def test_zero_and_boolean_checks_are_not_missing_values() -> None:
    nodes = _nodes()
    check = nodes["review"]["intent_review"]["checks"][0]
    check.update(expected=0, actual=0)
    assert project_intent_review(nodes["review"], nodes)["checks"][0]["state"] == "SATISFIED"
    check.update(expected=False, actual=False, operator="eq", unit=None)
    result = project_intent_review(nodes["review"], nodes)["checks"][0]
    assert result["state"] == "SATISFIED"
    assert result["delta"] is None


def test_real_ledger_projects_intent_review_without_rewriting_it(tmp_path: Path) -> None:
    events = []
    for index, (event_id, node) in enumerate(_nodes().items()):
        event = {
            "schema_version": "hyodo.agent-event/v1",
            "event_id": event_id,
            "run_id": "r",
            "ts": node["ts"],
            "kind": node["kind"],
            "actor": node["actor"],
            "step_index": index,
            "io": node.get("io", {}),
            "evidence_refs": ["result"] if event_id == "review" else [],
        }
        if event_id == "review":
            event["meta"] = {"intent_review": node["intent_review"]}
        events.append(event)
    path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    write_ledger(path, "\n".join(json.dumps(e) for e in events) + "\n")
    original = path.read_bytes()
    graph = build_report_graph(tmp_path)
    view = build_verification_view(graph, root=tmp_path)
    review = view["events"]["review"]["why"]["intent_review"]
    assert review["checks"][0]["state"] == "DEVIATES"
    assert review["checks"][0]["delta"] == 30
    assert view["authority"] == "UNOBSERVED"
    assert path.read_bytes() == original
    from hyodo.dashboard import render_graph_html

    html = render_graph_html(graph, root=tmp_path)
    assert "WHY / INTENT COMPARISON" in html
    assert "intentReview" in html
    assert "budget" in html


def test_history_locates_requirement_changes_without_overwriting_old_intent() -> None:
    nodes = _nodes()
    previous = copy.deepcopy(nodes["review"])
    previous.update(id="previous", ts="2026-09-19T10:01:30Z")
    nodes["previous"] = previous
    review = nodes["review"]["intent_review"]
    review["previous_review_ref"] = "previous"
    review["checks"][0]["expected"] = 200
    before = copy.deepcopy(nodes)
    history = project_intent_review(nodes["review"], nodes)["history"]
    assert history["state"] == "LINKED"
    assert history["intent_source_changed"] is False
    change = history["requirement_changes"][0]
    assert change["id"] == "budget"
    assert change["fields"] == ["expected"]
    assert change["before"]["expected"] == 100
    assert change["after"]["expected"] == 200
    check = project_intent_review(nodes["review"], nodes)["checks"][0]
    assert check["comparison"] == "SATISFIED"
    assert check["state"] == "UNOBSERVED"
    assert "requirement_changed_without_new_intent_source" in check["missing"]
    assert nodes == before


@pytest.mark.parametrize("reference", ["missing", "review", "future"])
def test_missing_self_or_future_history_is_not_a_past_fact(reference: str) -> None:
    nodes = _nodes()
    nodes["future"] = {
        **copy.deepcopy(nodes["review"]),
        "id": "future",
        "ts": "2026-09-20T00:00:00Z",
    }
    nodes["review"]["intent_review"]["previous_review_ref"] = reference
    history = project_intent_review(nodes["review"], nodes)["history"]
    assert history["state"] == "UNOBSERVED"
    assert history["requirement_changes"] == []


def test_equal_timestamps_require_recorded_same_run_order() -> None:
    nodes = _nodes()
    nodes["result"]["ts"] = nodes["review"]["ts"]
    assert project_intent_review(nodes["review"], nodes)["checks"][0]["state"] == "UNOBSERVED"
    nodes["result"].update(run_id="r", step_index=1)
    nodes["review"].update(run_id="r", step_index=2)
    assert project_intent_review(nodes["review"], nodes)["checks"][0]["state"] == "DEVIATES"
    nodes["result"]["step_index"] = 3
    assert project_intent_review(nodes["review"], nodes)["checks"][0]["state"] == "UNOBSERVED"


def test_run_comparison_summary_preserves_withheld_and_escapes_host_text() -> None:
    from hyodo.dashboard import _render_intent_comparisons, _scoped_verification_view

    nodes = _nodes()
    nodes["review"]["intent_review"]["mode"] = "PROJECTED"
    review = project_intent_review(nodes["review"], nodes)
    review["checks"][0]["id"] = "<script>bad</script>"
    view = {
        "events": {
            "review": {"why": {"run_id": "selected", "intent_review": review}},
            "other-secret": {"why": {"run_id": "other", "intent_review": review}},
        }
    }
    html = _render_intent_comparisons(_scoped_verification_view(view, "selected"))
    assert "PROJECTED" in html
    assert "hypothetical_comparison" in html
    assert "UNOBSERVED" in html
    assert "other-secret" not in html
    assert "<script>bad</script>" not in html
    assert "&lt;script&gt;bad&lt;/script&gt;" in html
    assert "constraints" in html
    assert "verified fulfillment or authorization" in html


def test_run_comparison_summary_does_not_infer_checks_from_activity() -> None:
    from hyodo.dashboard import _render_intent_comparisons

    html = _render_intent_comparisons({"events": {"call": {"what": {"kind": "tool_call"}}}})
    assert "No requirement comparison recorded for this run" in html


@pytest.mark.parametrize(
    ("mode", "basis", "expected_state"),
    [
        ("OBSERVED", "DECLARED", "DEVIATES"),
        ("OBSERVED", "INFERRED", "UNOBSERVED"),
        ("PROJECTED", "DECLARED", "UNOBSERVED"),
    ],
)
def test_host_cli_submission_preserves_comparison_boundaries(
    tmp_path: Path, mode: str, basis: str, expected_state: str
) -> None:
    from typer.testing import CliRunner

    from hyodo.cli.main import app
    from hyodo.dashboard import render_graph_html

    runner = CliRunner()
    nodes = _nodes()
    nodes["review"]["intent_review"]["mode"] = mode
    nodes["review"]["intent_review"]["checks"][0]["basis"] = basis
    for index, (event_id, node) in enumerate(nodes.items()):
        event = {
            "schema_version": "hyodo.agent-event/v1",
            "event_id": event_id,
            "run_id": "host-cli-fixture",
            "ts": node["ts"],
            "kind": node["kind"],
            "actor": node["actor"],
            "step_index": index,
            "io": node.get("io", {}),
            "evidence_refs": ["result"] if event_id == "review" else [],
        }
        if event_id == "review":
            event["meta"] = {"intent_review": node["intent_review"]}
        result = runner.invoke(
            app,
            ["event", "record", "--stdin", "--root", str(tmp_path), "--json"],
            input=json.dumps(event),
        )
        assert result.exit_code == 0, result.output
    ledger = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    before = ledger.read_bytes()
    graph = build_report_graph(tmp_path)
    view = build_verification_view(graph, root=tmp_path)
    review = view["events"]["review"]["why"]["intent_review"]
    assert review["checks"][0]["state"] == expected_state
    assert review["checks"][0]["evidence_refs"] == ["result"]
    assert view["authority"] == "UNOBSERVED"
    html = render_graph_html(graph, root=tmp_path)
    assert "Recorded requirement comparisons" in html
    assert basis in html
    assert ledger.read_bytes() == before


def test_host_cli_rejects_malformed_review_without_append(tmp_path: Path) -> None:
    from typer.testing import CliRunner

    from hyodo.cli.main import app

    review = _review()
    review["checks"][0]["basis"] = "AUTO_APPROVED"
    event = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": "invalid",
        "run_id": "host-cli-fixture",
        "ts": "2026-09-19T10:02:00+00:00",
        "kind": "model_response",
        "actor": "agent",
        "step_index": 0,
        "meta": {"intent_review": review},
    }
    result = CliRunner().invoke(
        app,
        ["event", "record", "--stdin", "--root", str(tmp_path), "--json"],
        input=json.dumps(event),
    )
    assert result.exit_code != 0
    assert "invalid_field:meta.intent_review" in result.output
    assert not (tmp_path / AGENT_EVENTS_RELATIVE_PATH).exists()
