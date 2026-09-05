"""Property-based durability tests for JSONL append-only ledgers.

Philosophy mapping:
  - Hyo (孝): Reciprocal continuity — the ledger must survive crashes,
    corruption, and concurrent writes without silent data loss.
  - Yeong (永): Eternity of measurement — an unreadable ledger must never be
    reported as empty (that would be fake green).  None ≠ 0.

These are *properties*, not examples.  Hypothesis generates arbitrary malformed
lines, interleavings, and edge cases that examples would miss.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from hyodo.events import (
    append_agent_event,
    count_run_events,
    read_agent_events,
)

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# A well-formed agent event — minimal valid structure
valid_event = st.builds(
    lambda run_id, kind, ts: {"run_id": run_id, "kind": kind, "timestamp": ts},
    run_id=st.uuids(version=4).map(str),
    kind=st.sampled_from(["tool_call", "tool_result", "llm_call", "llm_response"]),
    ts=st.just("2026-09-05T00:00:00Z"),
)

# Arbitrary text that may or may not be valid JSON — designed to produce
# *non-empty, non-parseable* lines when we want corruption.  We avoid generating
# valid JSON dicts (like {}) because those parse as dicts and count as events
# rather than corrupt lines.
arbitrary_corrupt_line = st.one_of(
    st.text(min_size=1, max_size=40, alphabet=st.characters(whitelist_categories=("L", "P", "S"))),
    st.from_regex(r"[0-9]+\.[0-9]+", fullmatch=True),  # looks like a number, not a JSON dict
    st.just("null"),
    st.just("true"),
    st.just("[1,2,3]"),  # valid JSON array — not a dict, so counted as corrupt
    st.just('"just a string"'),  # valid JSON string — not a dict, so corrupt
)


# ---------------------------------------------------------------------------
# 1. Append-only durability: valid events survive any mix of corrupt lines
# ---------------------------------------------------------------------------


@given(
    good_events=st.lists(valid_event, min_size=1, max_size=5),
    corrupt_lines=st.lists(arbitrary_corrupt_line, min_size=0, max_size=3),
    corrupt_position=st.integers(min_value=0, max_value=5),
)
@settings(
    deadline=None,
    suppress_health_check=[HealthCheck.filter_too_much, HealthCheck.function_scoped_fixture],
    max_examples=80,
)
def test_valid_events_survive_corrupt_neighbors(
    tmp_path: Path,
    good_events: list[dict],
    corrupt_lines: list[str],
    corrupt_position: int,
) -> None:
    """Valid JSONL events must be recoverable even when surrounded by corrupt lines.

    This is Yeong (永): corrupt data is counted but never silently absorbed.
    Valid events are never lost.
    """
    # Reset tmp_path for each hypothesis example — function-scoped fixture.
    ledger_dir = tmp_path / ".hyodo"
    if ledger_dir.exists():
        for f in ledger_dir.iterdir():
            f.unlink()
        ledger_dir.rmdir()

    # Write corrupt lines interleaved with valid events
    lines: list[str] = []
    for i, evt in enumerate(good_events):
        lines.append(json.dumps(evt, sort_keys=True))
        # Optionally inject corrupt lines after this event
        if i == corrupt_position % max(len(good_events), 1):
            lines.extend(corrupt_lines)

    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")

    events, corrupt_count = read_agent_events(tmp_path)

    # All valid events must be recovered
    assert len(events) == len(good_events), f"Expected {len(good_events)} events, got {len(events)}"

    # Corrupt lines must be counted (never hidden).
    # Note: blank/whitespace-only lines are silently skipped (not counted as
    # corrupt) per read_agent_events design — only non-empty, non-parseable
    # lines increment the corrupt counter.
    non_blank_corrupt = [line for line in corrupt_lines if line.strip()]
    assert corrupt_count == len(non_blank_corrupt), (
        f"Expected {len(non_blank_corrupt)} corrupt lines (excluding blanks), got {corrupt_count}"
    )


# ---------------------------------------------------------------------------
# 2. count_run_events: unobserved ledger returns None, not 0
# ---------------------------------------------------------------------------


@given(run_id=st.uuids(version=4).map(str))
@settings(
    deadline=None, max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture]
)
def test_count_unobserved_ledger_returns_none_not_zero(
    tmp_path: Path,
    run_id: str,
) -> None:
    """An unreadable ledger must return None, never 0.

    This is the fail-closed contract: None ≠ 0.  Returning 0 for an unreadable
    ledger would hand out a free ALLOW — a fake green signal.
    """
    # Reset for each hypothesis example
    ledger_dir = tmp_path / ".hyodo"
    if ledger_dir.exists():
        for f in ledger_dir.iterdir():
            f.unlink()
    ledger_dir.mkdir(parents=True, exist_ok=True)

    ledger = ledger_dir / "agent-events.jsonl"

    # Unreadable file (permissions) → None
    if os.name != "nt":  # skip on Windows (no chmod)
        ledger.write_text('{"run_id": "x", "kind": "tool_call"}\n', encoding="utf-8")
        os.chmod(ledger, 0o000)
        try:
            result = count_run_events(tmp_path, run_id)
            assert result is None, f"Unreadable ledger returned {result}, expected None"
        finally:
            os.chmod(ledger, 0o600)  # restore for cleanup


# ---------------------------------------------------------------------------
# 3. Concurrent appends never corrupt the JSONL structure
# ---------------------------------------------------------------------------


def test_concurrent_appends_no_data_loss(tmp_path: Path) -> None:
    """Multiple threads appending simultaneously must not lose events.

    This is Hyo (孝): reciprocal continuity requires that concurrent writes
    produce a ledger where every valid event is recoverable.
    """
    n_events = 50
    n_threads = 5
    events_per_thread = n_events // n_threads

    errors: list[Exception] = []

    def writer(thread_id: int) -> None:
        try:
            for i in range(events_per_thread):
                evt = {
                    "run_id": f"thread-{thread_id}",
                    "kind": "tool_call",
                    "timestamp": f"2026-09-05T00:{thread_id:02d}:{i:02d}Z",
                }
                append_agent_event(tmp_path, evt)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=writer, args=(t,)) for t in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert not errors, f"Concurrent append errors: {errors}"

    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0, f"Corrupt lines after concurrent writes: {corrupt}"
    assert len(events) == n_events, (
        f"Expected {n_events} events after concurrent writes, got {len(events)}"
    )


# ---------------------------------------------------------------------------
# 4. Empty ledger vs missing ledger: different truths
# ---------------------------------------------------------------------------


def test_missing_ledger_is_honest_empty(tmp_path: Path) -> None:
    """A missing ledger file returns ([], 0) — honest zero, not fake green."""
    events, corrupt = read_agent_events(tmp_path)
    assert events == []
    assert corrupt == 0


def test_empty_file_ledger_is_honest_empty(tmp_path: Path) -> None:
    """An empty file also returns ([], 0) — no corruption, no events."""
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("", encoding="utf-8")

    events, corrupt = read_agent_events(tmp_path)
    assert events == []
    assert corrupt == 0


def test_whitespace_only_ledger_is_corrupt_zero_events(tmp_path: Path) -> None:
    """A file with only whitespace lines is corrupt with zero events."""
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text("   \n\n  \n", encoding="utf-8")

    events, corrupt = read_agent_events(tmp_path)
    assert events == []
    assert corrupt == 0  # blank lines are skipped, not counted as corrupt
