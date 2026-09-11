from __future__ import annotations

import json
from pathlib import Path

import typer.testing

from hyodo.cli.main import app
from hyodo.orchestration_observation import (
    ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH,
    append_orchestration_observation,
    read_orchestration_observations,
)

_runner = typer.testing.CliRunner()


def _observation(**over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "schema": "hyodo.orchestration-observation/v1",
        "observation_id": "obs-1",
        "run_id": "run-1",
        "event_id": "evt-1",
        "ts": "2026-09-11T00:00:00Z",
        "node_id": "node-1",
        "execution": "serial",
        "depends_on": [],
        "join_policy": None,
        "state": "started",
    }
    base.update(over)
    return base


def test_an_observation_lands_in_its_own_file_not_the_event_ledger(tmp_path: Path) -> None:
    """The sidecar is a separate record. The agent ledger stays untouched."""
    assert append_orchestration_observation(tmp_path, _observation()) is True

    sidecar = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    assert sidecar.exists()
    assert not (tmp_path / ".hyodo" / "agent-events.jsonl").exists()


def test_the_sidecar_file_is_owner_only(tmp_path: Path) -> None:
    append_orchestration_observation(tmp_path, _observation())

    mode = (tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH).stat().st_mode
    assert mode & 0o777 == 0o600


def test_an_invalid_observation_is_refused_rather_than_written(tmp_path: Path) -> None:
    bad = _observation(execution="whatever-the-caller-felt-like")

    assert append_orchestration_observation(tmp_path, bad) is False
    assert not (tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH).exists()


def test_what_was_written_reads_back(tmp_path: Path) -> None:
    append_orchestration_observation(tmp_path, _observation(observation_id="a"))
    append_orchestration_observation(tmp_path, _observation(observation_id="b"))

    rows = read_orchestration_observations(tmp_path)

    assert [row["observation_id"] for row in rows] == ["a", "b"]


def test_a_corrupt_line_does_not_hide_the_rest(tmp_path: Path) -> None:
    """A ledger that cannot be fully read must not read as an empty one.

    The damage is applied to a line of an already-written file rather than
    appended between two writes, because appending past an unreadable line is
    now refused -- see :func:`check_observation_id`. Reading keeps the opposite
    attitude on purpose, and that is what this asserts.
    """
    for observation_id in ("a", "b", "c"):
        append_orchestration_observation(tmp_path, _observation(observation_id=observation_id))
    sidecar = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    written = sidecar.read_text(encoding="utf-8").splitlines()
    written[1] = "{not json"
    sidecar.write_text("\n".join(written) + "\n", encoding="utf-8")

    rows = read_orchestration_observations(tmp_path)

    assert [row["observation_id"] for row in rows] == ["a", "c"]


def test_reading_an_absent_file_is_empty_not_an_error(tmp_path: Path) -> None:
    assert read_orchestration_observations(tmp_path) == []


def test_the_stored_row_is_the_normalized_one(tmp_path: Path) -> None:
    """Storing the caller's dict verbatim would let unvalidated keys through."""
    append_orchestration_observation(tmp_path, _observation(extra_field="should not survive"))

    raw = (tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH).read_text(encoding="utf-8")
    stored = json.loads(raw.splitlines()[0])

    assert "extra_field" not in stored
    assert stored["schema"] == "hyodo.orchestration-observation/v1"


# --- CLI surface -----------------------------------------------------------
#
# KINGDOM's bridge hands events to HyoDo by spawning the CLI. Sidecar
# observations had no such door, so a producer could describe a DAG and have
# nowhere to put it. This is that door, and it is deliberately a separate
# command: recording a dependency is not recording an event.


def test_the_cli_records_an_observation_from_a_file(tmp_path: Path) -> None:
    src = tmp_path / "obs.json"
    src.write_text(json.dumps(_observation()), encoding="utf-8")

    result = _runner.invoke(
        app, ["observation", "record", "--file", str(src), "--root", str(tmp_path)]
    )

    assert result.exit_code == 0, result.output
    assert len(read_orchestration_observations(tmp_path)) == 1


def test_the_cli_reads_stdin_too(tmp_path: Path) -> None:
    result = _runner.invoke(
        app,
        ["observation", "record", "--stdin", "--root", str(tmp_path)],
        input=json.dumps(_observation()),
    )

    assert result.exit_code == 0, result.output
    assert len(read_orchestration_observations(tmp_path)) == 1


def test_the_cli_refuses_an_invalid_observation(tmp_path: Path) -> None:
    result = _runner.invoke(
        app,
        ["observation", "record", "--stdin", "--root", str(tmp_path)],
        input=json.dumps(_observation(state="whatever")),
    )

    assert result.exit_code != 0
    assert read_orchestration_observations(tmp_path) == []


def test_recording_an_observation_never_touches_the_event_ledger(tmp_path: Path) -> None:
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text('{"kind": "prompt"}\n', encoding="utf-8")
    before = ledger.read_text(encoding="utf-8")

    _runner.invoke(
        app,
        ["observation", "record", "--stdin", "--root", str(tmp_path)],
        input=json.dumps(_observation()),
    )

    assert ledger.read_text(encoding="utf-8") == before


# --- idempotency -----------------------------------------------------------
#
# The ledger already refuses to grow when the same event is replayed. The
# sidecar did not, so re-collecting a stream inflated the row count while the
# number of observations stayed the same. Anything later counting iterations
# off these rows would have counted re-collections instead.


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rows(root: Path) -> list[str]:
    path = root / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    return [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_replaying_the_same_observation_does_not_add_a_row(tmp_path: Path) -> None:
    assert append_orchestration_observation(tmp_path, _observation()) is True
    assert len(_rows(tmp_path)) == 1

    assert append_orchestration_observation(tmp_path, _observation()) is True
    assert len(_rows(tmp_path)) == 1


def test_replaying_the_same_observation_leaves_the_file_byte_identical(tmp_path: Path) -> None:
    """A no-op must be observably a no-op, not a rewrite that happens to match."""
    append_orchestration_observation(tmp_path, _observation())
    path = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    before = _sha256(path)

    append_orchestration_observation(tmp_path, _observation())

    assert _sha256(path) == before


def test_the_same_id_with_different_content_is_refused(tmp_path: Path) -> None:
    """Reusing an id with new content would let a producer rewrite its history."""
    append_orchestration_observation(tmp_path, _observation())
    path = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    before = _sha256(path)

    assert append_orchestration_observation(tmp_path, _observation(state="completed")) is False

    assert len(_rows(tmp_path)) == 1
    assert _sha256(path) == before


def test_input_that_normalizes_to_the_same_observation_is_the_same_observation(
    tmp_path: Path,
) -> None:
    """Order and repeats in depends_on are not content -- the normalizer removes
    both, so two spellings of one dependency set are one observation."""
    first = _observation(depends_on=["evt-b", "evt-a"], join_policy="all")
    again = _observation(depends_on=["evt-a", "evt-b", "evt-a"], join_policy="all")

    assert append_orchestration_observation(tmp_path, first) is True
    assert append_orchestration_observation(tmp_path, again) is True

    assert len(_rows(tmp_path)) == 1


def test_a_malformed_existing_row_stops_the_append(tmp_path: Path) -> None:
    """Uniqueness cannot be proven past a line nobody can read, and the read
    path's habit of skipping such a line must not become a licence to write."""
    path = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{not json at all\n", encoding="utf-8")
    before = _sha256(path)

    assert append_orchestration_observation(tmp_path, _observation()) is False

    assert _sha256(path) == before


def test_a_row_without_an_identifier_stops_the_append(tmp_path: Path) -> None:
    """A row that parses but names no observation is equally unprovable."""
    path = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema": "x"}) + "\n", encoding="utf-8")
    before = _sha256(path)

    assert append_orchestration_observation(tmp_path, _observation()) is False

    assert _sha256(path) == before


def test_blank_lines_are_not_malformed_rows(tmp_path: Path) -> None:
    """Whitespace is absence, not corruption -- it must not block a write."""
    append_orchestration_observation(tmp_path, _observation())
    path = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n   \n")

    assert append_orchestration_observation(tmp_path, _observation(observation_id="obs-2")) is True

    assert len(_rows(tmp_path)) == 2


def test_a_distinct_observation_still_appends(tmp_path: Path) -> None:
    append_orchestration_observation(tmp_path, _observation())

    assert append_orchestration_observation(tmp_path, _observation(observation_id="obs-2")) is True

    assert len(_rows(tmp_path)) == 2


def test_the_file_stays_owner_only_across_a_replay(tmp_path: Path) -> None:
    append_orchestration_observation(tmp_path, _observation())
    append_orchestration_observation(tmp_path, _observation())

    mode = (tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH).stat().st_mode
    assert mode & 0o777 == 0o600


def test_the_agent_ledger_is_untouched_by_sidecar_writes(tmp_path: Path) -> None:
    """Including the replay path, which must not write anywhere at all."""
    ledger = tmp_path / ".hyodo" / "agent-events.jsonl"
    ledger.parent.mkdir(parents=True, exist_ok=True)
    ledger.write_text('{"event_id": "evt-1", "kind": "prompt"}\n', encoding="utf-8")
    before = _sha256(ledger)

    append_orchestration_observation(tmp_path, _observation())
    append_orchestration_observation(tmp_path, _observation())
    append_orchestration_observation(tmp_path, _observation(state="completed"))

    assert _sha256(ledger) == before
