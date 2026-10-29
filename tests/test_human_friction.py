"""Tests for human-side friction events and the deterministic friction score."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.dispatch import app
from hyodo.human_friction import (
    DEFAULT_WEIGHTS,
    HUMAN_FRICTION_EVENT_SCHEMA,
    HUMAN_FRICTION_OBSERVATION_SCHEMA,
    score_events,
    validate_envelope,
    validate_event,
)

runner = CliRunner()


def _event(kind: str, **evidence: object) -> dict[str, object]:
    defaults: dict[str, dict[str, object]] = {
        "re_explanation": {"message_ref": "msg-2", "repeats_ref": "msg-1"},
        "duplicate_approval": {
            "request_ref": "req-2",
            "prior_request_ref": "req-1",
            "covering_approval_ref": "approval-1",
        },
        "context_loss": {"message_ref": "msg-3", "lost_canon_ref": "docs/rule.md#identity"},
        "runtime_abandon": {
            "item_ref": "pr-7",
            "last_change_at": "2026-10-21T10:00:00Z",
            "observed_at": "2026-10-21T16:00:00Z",
            "threshold_seconds": 3600,
        },
    }
    return {
        "schema": HUMAN_FRICTION_EVENT_SCHEMA,
        "type": kind,
        "observed_by": "observer-seat",
        "actor": "executor-seat",
        "evidence": {**defaults[kind], **evidence},
    }


def _envelope(event_count: int, **fields: object) -> dict[str, object]:
    return {
        "schema": HUMAN_FRICTION_OBSERVATION_SCHEMA,
        "observed_by": "observer-seat",
        "window_start": "2026-10-21T00:00:00Z",
        "window_end": "2026-10-21T23:59:59Z",
        "sources_scanned": ["project-chat", "thread:a"],
        "event_count": event_count,
        **fields,
    }


def test_formula_matches_the_spec_weights() -> None:
    events = [
        _event("re_explanation"),
        _event("duplicate_approval"),
        _event("context_loss"),
        _event("runtime_abandon"),
    ]
    result = score_events(events)
    assert result["counts"] == {
        "re_explanation": 1,
        "duplicate_approval": 1,
        "context_loss": 1,
        "runtime_abandon": 1,
    }
    assert result["score"] == 2 + 1.5 + 3 + 2.5
    assert result["state"] == "FRICTION"
    assert result["authority"]["grants_execution"] is False


def test_no_events_is_clean_only_with_an_observation_envelope() -> None:
    result = score_events([], envelope=_envelope(0))
    assert result["state"] == "CLEAN"
    assert result["score"] == 0
    assert result["partial"] is False

    result = score_events([])
    assert result["state"] == "UNOBSERVED"
    assert result["rejected"] == [{"envelope": True, "reason": "no_observation_envelope"}]


@pytest.mark.parametrize(
    ("fields", "reason"),
    [
        ({"observed_by": " "}, "envelope_observer_missing"),
        ({"window_end": "2026-10-20T00:00:00Z"}, "envelope_window_invalid"),
        ({"window_start": "2026-10-21T00:00:00"}, "envelope_window_invalid"),
        ({"sources_scanned": []}, "envelope_sources_invalid"),
        ({"event_count": -1}, "envelope_count_invalid"),
        ({"extra": "x"}, "envelope_fields_mismatch"),
    ],
)
def test_invalid_envelopes_are_rejected(fields: dict[str, object], reason: str) -> None:
    envelope = {**_envelope(0), **fields}
    assert validate_envelope(envelope) == reason
    assert score_events([], envelope=envelope)["state"] == "UNOBSERVED"


def test_envelope_count_must_match_the_events() -> None:
    result = score_events([], envelope=_envelope(2))
    assert result["state"] == "UNOBSERVED"
    assert {"envelope": True, "reason": "envelope_count_mismatch"} in result["rejected"]


def test_observer_cannot_be_the_actor() -> None:
    event = _event("re_explanation")
    event["observed_by"] = event["actor"]
    assert validate_event(event) == (None, "observer_is_actor")
    event["observed_by"] = "  Executor-Seat "
    assert validate_event(event) == (None, "observer_is_actor")


def test_observer_that_is_an_actor_elsewhere_in_the_file_is_rejected() -> None:
    blamed = _event("re_explanation")
    blamed["observed_by"] = "second-observer"
    blamed["actor"] = "Observer-Seat"
    other = _event("context_loss")
    result = score_events([blamed, other], envelope=_envelope(2))
    assert result["counts"]["re_explanation"] == 1
    assert result["counts"]["context_loss"] == 0
    assert {"index": 1, "reason": "observer_is_actor_elsewhere"} in result["rejected"]
    assert {"envelope": True, "reason": "envelope_observer_is_actor"} in result["rejected"]


@pytest.mark.parametrize(
    ("kind", "evidence", "reason"),
    [
        ("re_explanation", {"repeats_ref": "msg-2"}, "evidence_refs_not_distinct"),
        ("re_explanation", {"repeats_ref": ""}, "evidence_ref_invalid"),
        ("context_loss", {"lost_canon_ref": None}, "evidence_ref_invalid"),
        ("runtime_abandon", {"observed_at": "2026-10-21T10:30:00Z"}, "below_threshold"),
        ("runtime_abandon", {"last_change_at": "yesterday"}, "timestamp_invalid"),
        ("runtime_abandon", {"last_change_at": "2026-10-21T10:00:00"}, "timestamp_invalid"),
        ("runtime_abandon", {"threshold_seconds": 0}, "threshold_invalid"),
        ("runtime_abandon", {"threshold_seconds": True}, "threshold_invalid"),
    ],
)
def test_events_without_checkable_evidence_are_rejected(
    kind: str, evidence: dict[str, object], reason: str
) -> None:
    assert validate_event(_event(kind, **evidence)) == (None, reason)


def test_missing_or_extra_evidence_fields_are_rejected() -> None:
    event = _event("duplicate_approval")
    del event["evidence"]["covering_approval_ref"]  # type: ignore[attr-defined]
    assert validate_event(event) == (None, "evidence_fields_mismatch")
    event = _event("context_loss")
    event["evidence"]["raw_text"] = "prompt body"  # type: ignore[index]
    assert validate_event(event) == (None, "evidence_fields_mismatch")
    event = _event("context_loss")
    event["message_body"] = "prompt body"
    assert validate_event(event) == (None, "unsupported_field")


def test_unknown_type_and_schema_are_rejected() -> None:
    event = _event("context_loss")
    event["type"] = "vibes"
    assert validate_event(event) == (None, "unknown_type")
    event = _event("context_loss")
    event["schema"] = "hyodo.friction-event/v0"
    assert validate_event(event) == (None, "schema_mismatch")


def test_same_event_counts_once() -> None:
    events = [_event("re_explanation"), _event("re_explanation")]
    result = score_events(events, envelope=_envelope(2))
    assert result["counts"]["re_explanation"] == 1
    assert result["rejected"] == [{"index": 1, "reason": "duplicate_event"}]
    assert result["state"] == "FRICTION"
    assert result["partial"] is False


def test_any_invalid_event_makes_the_state_unobserved_never_clean() -> None:
    bad = _event("re_explanation", repeats_ref="msg-2")
    result = score_events([bad], envelope=_envelope(1))
    assert result["score"] == 0
    assert result["state"] == "UNOBSERVED"


def test_friction_with_bad_lines_stays_friction_and_is_marked_partial() -> None:
    bad = _event("re_explanation", repeats_ref="msg-2")
    result = score_events([_event("context_loss"), bad], envelope=_envelope(2))
    assert result["state"] == "FRICTION"
    assert result["score"] == 3.0
    assert result["partial"] is True


def test_weights_must_cover_all_four_types() -> None:
    with pytest.raises(ValueError, match="four types"):
        score_events([], weights={"re_explanation": 1.0})
    custom = dict.fromkeys(DEFAULT_WEIGHTS, 1.0)
    assert score_events([_event("context_loss")], weights=custom)["score"] == 1.0


def _write(tmp_path: Path, lines: list[str]) -> Path:
    path = tmp_path / "events.jsonl"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_cli_score_exit_codes(tmp_path: Path) -> None:
    clean = _write(tmp_path, [json.dumps(_envelope(0))])
    result = runner.invoke(app, ["friction", "score", str(clean)])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["state"] == "CLEAN"

    empty = _write(tmp_path, [])
    result = runner.invoke(app, ["friction", "score", str(empty)])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["state"] == "UNOBSERVED"

    twice = _write(tmp_path, [json.dumps(_envelope(0)), json.dumps(_envelope(0))])
    result = runner.invoke(app, ["friction", "score", str(twice)])
    assert result.exit_code == 2

    friction = _write(tmp_path, [json.dumps(_event("runtime_abandon"))])
    result = runner.invoke(app, ["friction", "score", str(friction)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["score"] == 2.5
    assert payload["accepted"][0]["evidence"]["item_ref"] == "pr-7"

    broken = _write(tmp_path, [json.dumps(_envelope(1)), "{not json"])
    result = runner.invoke(app, ["friction", "score", str(broken)])
    assert result.exit_code == 2
    assert json.loads(result.stdout)["state"] == "UNOBSERVED"

    partial = _write(
        tmp_path, [json.dumps(_envelope(2)), json.dumps(_event("context_loss")), "{not json"]
    )
    result = runner.invoke(app, ["friction", "score", str(partial)])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["state"] == "FRICTION"
    assert payload["partial"] is True

    result = runner.invoke(app, ["friction", "score", str(tmp_path / "missing.jsonl")])
    assert result.exit_code == 2


def test_cli_score_types_scores_only_the_named_types(tmp_path: Path) -> None:
    events = _write(tmp_path, [json.dumps(_envelope(1)), json.dumps(_event("runtime_abandon"))])

    other = runner.invoke(
        app, ["friction", "score", str(events), "--types", "re_explanation,context_loss"]
    )
    assert other.exit_code == 0
    assert json.loads(other.stdout)["state"] == "CLEAN"

    named = runner.invoke(
        app, ["friction", "score", str(events), "--types", "duplicate_approval,runtime_abandon"]
    )
    assert named.exit_code == 1
    assert json.loads(named.stdout)["score"] == 2.5


def test_cli_score_types_never_cleans_an_unobserved_window(tmp_path: Path) -> None:
    empty = _write(tmp_path, [])
    result = runner.invoke(app, ["friction", "score", str(empty), "--types", "re_explanation"])
    assert result.exit_code == 2

    missing = tmp_path / "missing.jsonl"
    result = runner.invoke(app, ["friction", "score", str(missing), "--types", "re_explanation"])
    assert result.exit_code == 2


def test_cli_score_types_rejects_unknown_type(tmp_path: Path) -> None:
    events = _write(tmp_path, [json.dumps(_envelope(0))])
    result = runner.invoke(app, ["friction", "score", str(events), "--types", "mood"])
    assert result.exit_code == 2
