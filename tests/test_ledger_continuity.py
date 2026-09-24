"""Eternity evidence on the ledger anchor: a sequence that never goes back and
gaps that are recorded instead of left as silence."""

from __future__ import annotations

import json
from pathlib import Path

from hyodo.continuity import measure_continuity
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
from hyodo.ledger_origin import (
    GAP_CHANGED,
    GAP_RESTARTED,
    GAP_UNANCHORED,
    LEDGER_ORIGIN_SCHEMA,
    LEDGER_ORIGIN_STATE_NAME,
    ORIGIN_UNVERIFIED,
    ORIGIN_VERIFIED,
    anchored_append,
    ledger_continuity,
)
from hyodo.user_state import workspace_identity, workspace_state_path

LEDGER = Path(".hyodo/test-ledger.jsonl")


def _append(root: Path, n: int) -> None:
    for i in range(n):
        anchored_append(root, LEDGER, json.dumps({"i": i}) + "\n")


def test_sequence_counts_hyodo_appends_and_starts_unobserved(tmp_path: Path) -> None:
    assert ledger_continuity(tmp_path, LEDGER)["seq"] is None
    _append(tmp_path, 3)
    report = ledger_continuity(tmp_path, LEDGER)
    assert report["origin"] == ORIGIN_VERIFIED
    assert report["seq"] == 3
    assert report["gaps"] == []


def test_outside_edit_is_recorded_as_a_gap_at_the_break(tmp_path: Path) -> None:
    _append(tmp_path, 2)
    ledger = tmp_path / LEDGER
    ledger.write_text(ledger.read_text(encoding="utf-8") + '{"forged": true}\n')
    _append(tmp_path, 1)

    report = ledger_continuity(tmp_path, LEDGER)
    assert report["seq"] == 3
    assert report["gap_count"] == 1
    assert report["gaps"][0]["after_seq"] == 2
    assert report["gaps"][0]["reason"] == GAP_CHANGED
    # Recording the gap never launders the bytes: origin stays unverified.
    assert report["origin"] == ORIGIN_UNVERIFIED

    _append(tmp_path, 1)
    assert ledger_continuity(tmp_path, LEDGER)["gap_count"] == 1


def test_restarted_ledger_keeps_counting_and_names_the_restart(tmp_path: Path) -> None:
    _append(tmp_path, 2)
    (tmp_path / LEDGER).unlink()
    _append(tmp_path, 1)

    report = ledger_continuity(tmp_path, LEDGER)
    assert report["seq"] == 3
    assert [gap["reason"] for gap in report["gaps"]] == [GAP_RESTARTED]
    assert report["origin"] == ORIGIN_VERIFIED


def test_shipped_ledger_opens_with_an_unanchored_gap(tmp_path: Path) -> None:
    ledger = tmp_path / LEDGER
    ledger.parent.mkdir(parents=True)
    ledger.write_text('{"shipped": 1}\n{"shipped": 2}\n', encoding="utf-8")
    _append(tmp_path, 1)

    report = ledger_continuity(tmp_path, LEDGER)
    assert report["seq"] == 1
    assert report["gaps"][0] == {**report["gaps"][0], "after_seq": 0, "reason": GAP_UNANCHORED}
    assert report["origin"] == ORIGIN_UNVERIFIED


def test_anchor_from_before_sequences_counts_its_verified_lines(tmp_path: Path) -> None:
    _append(tmp_path, 3)
    state = workspace_state_path(tmp_path, LEDGER_ORIGIN_STATE_NAME)
    data = json.loads(state.read_text(encoding="utf-8"))
    for field in ("seq", "gap_count", "gaps"):
        del data["ledgers"][LEDGER.as_posix()][field]
    assert data["schema"] == LEDGER_ORIGIN_SCHEMA
    assert data["workspace_id"] == workspace_identity(tmp_path)
    state.write_text(json.dumps(data), encoding="utf-8")

    _append(tmp_path, 1)
    report = ledger_continuity(tmp_path, LEDGER)
    assert report["seq"] == 4
    assert report["gaps"] == []


def test_continuity_receipt_carries_sequence_and_gaps(tmp_path: Path) -> None:
    anchored_append(tmp_path, AGENT_EVENTS_RELATIVE_PATH, '{"not": "an event"}\n')
    receipt = measure_continuity(tmp_path)
    events = next(
        store
        for store in receipt["stores"].values()
        if store["path"] == str(AGENT_EVENTS_RELATIVE_PATH)
    )
    assert events["sequence"] == 1
    assert events["gaps"] == []
