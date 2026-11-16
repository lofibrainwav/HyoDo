"""Regression tests connecting HYOJA Technical Debt Wave 1-2 lessons to HyoDo contracts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
from typer.testing import CliRunner

from hyodo.cli.dispatch import app
from hyodo.gates import UserGate, _run_one_gate
from hyodo.human_friction import (
    HUMAN_FRICTION_EVENT_SCHEMA,
    HUMAN_FRICTION_OBSERVATION_SCHEMA,
    score_events,
    validate_event,
)

runner = CliRunner()


def _obs_envelope(event_count: int, **overrides: object) -> dict[str, object]:
    env: dict[str, object] = {
        "schema": HUMAN_FRICTION_OBSERVATION_SCHEMA,
        "observed_by": "observer:friction-merge",
        "window_start": "2026-11-14T01:36:45Z",
        "window_end": "2026-11-15T01:36:28Z",
        "sources_scanned": ["project-chat", "github:train:ready"],
        "event_count": event_count,
    }
    env.update(overrides)
    return env


def _abandon_event(last_at: str, obs_at: str, threshold_seconds: int = 14400) -> dict[str, object]:
    return {
        "schema": HUMAN_FRICTION_EVENT_SCHEMA,
        "type": "runtime_abandon",
        "observed_by": "observer:local-github",
        "actor": "tree-keeper",
        "evidence": {
            "item_ref": "lofibrainwav/kingdom#2263",
            "last_change_at": last_at,
            "observed_at": obs_at,
            "threshold_seconds": threshold_seconds,
        },
    }


def test_false_green_unobserved_zero_events_without_envelope_is_never_clean(tmp_path: Path) -> None:
    """Zero events with no observation envelope must stay UNOBSERVED (exit 2), never CLEAN."""
    no_env = score_events([])
    assert no_env["state"] == "UNOBSERVED"

    empty_file = tmp_path / "empty.jsonl"
    empty_file.write_text("", encoding="utf-8")
    res = runner.invoke(app, ["friction", "score", str(empty_file), "--types", "re_explanation,context_loss"])
    assert res.exit_code == 2
    assert json.loads(res.stdout)["state"] == "UNOBSERVED"


def test_partial_observation_loss_corrupt_line_is_flagged_partial(tmp_path: Path) -> None:
    """A malformed event line alongside valid events must mark partial=True, never silent CLEAN."""
    chat_ev = {
        "schema": HUMAN_FRICTION_EVENT_SCHEMA,
        "type": "re_explanation",
        "observed_by": "observer:friction-routine",
        "actor": "coordinator",
        "evidence": {"message_ref": "cmsg_2", "repeats_ref": "cmsg_1"},
    }
    p = tmp_path / "partial.jsonl"
    p.write_text(
        json.dumps(_obs_envelope(2)) + "\n" + json.dumps(chat_ev) + "\n{corrupt_json\n",
        encoding="utf-8",
    )
    res = runner.invoke(app, ["friction", "score", str(p)])
    assert res.exit_code == 1
    body = json.loads(res.stdout)
    assert body["state"] == "FRICTION"
    assert body["partial"] is True
    assert body["counts"]["re_explanation"] == 1


def test_stale_timestamp_envelope_future_window_is_rejected() -> None:
    """Invalid/unparseable or reversed observation window must reject to UNOBSERVED."""
    reversed_win = _obs_envelope(
        0,
        window_start="2026-11-16T00:00:00Z",
        window_end="2026-11-15T00:00:00Z",
    )
    res = score_events([], envelope=reversed_win)
    assert res["state"] == "UNOBSERVED"
    assert res["rejected"][0]["reason"] == "envelope_window_invalid"


def test_recursive_fallback_timeout_or_nonzero_exit_never_becomes_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A timed-out or unobserved subprocess gate must stay FAIL/SKIP, never coerced to PASS."""
    import shutil
    import subprocess

    monkeypatch.setattr(shutil, "which", lambda *_a, **_k: "/usr/bin/node")
    gate_due = UserGate(
        name="order-due",
        pillar="truth",
        command=("node", "scripts/order-receipt.mjs", "due"),
        timeout=20,
    )

    def fake_timeout(*_args: object, **_kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd=gate_due.command, timeout=20)

    monkeypatch.setattr(subprocess, "run", fake_timeout)
    timeout_res = _run_one_gate(gate_due, tmp_path, verbose=False)
    assert timeout_res.status == "FAIL"
    assert timeout_res.message == "timeout"

    gate_friction = UserGate(
        name="friction-in",
        pillar="benevolence",
        command=("hyodo", "friction", "score", "missing.jsonl"),
        timeout=10,
        unobserved_exit_codes=(2,),
    )
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(returncode=2, stdout="", stderr="unobserved"),
    )
    skip_res = _run_one_gate(gate_friction, tmp_path, verbose=False)
    assert skip_res.status == "SKIP"
    assert "UNOBSERVED (exit code 2)" in skip_res.message


def test_work_lifecycle_abandonment_threshold_and_observer_separation() -> None:
    """Work lifecycle abandonment is only valid past threshold_seconds and when observer != actor."""
    too_early = _abandon_event("2026-11-15T10:00:00Z", "2026-11-15T12:00:00Z", threshold_seconds=14400)
    _, err = validate_event(too_early)
    assert err == "below_threshold"

    past_threshold = _abandon_event("2026-11-15T07:34:42Z", "2026-11-15T15:15:00Z", threshold_seconds=14400)
    key, ok_err = validate_event(past_threshold)
    assert ok_err is None
    assert key is not None

    self_judged = {**past_threshold, "observed_by": "tree-keeper", "actor": "tree-keeper"}
    _, self_err = validate_event(self_judged)
    assert self_err == "observer_is_actor"

    t0 = datetime(2026, 11, 15, 1, 36, 28, tzinfo=timezone.utc)
    assert t0.isoformat().startswith("2026-11-15T01:36:28")
