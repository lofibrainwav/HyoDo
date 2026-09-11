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
    """A ledger that cannot be fully read must not read as an empty one."""
    append_orchestration_observation(tmp_path, _observation(observation_id="a"))
    sidecar = tmp_path / ORCHESTRATION_OBSERVATIONS_RELATIVE_PATH
    with sidecar.open("a", encoding="utf-8") as handle:
        handle.write("{not json\n")
    append_orchestration_observation(tmp_path, _observation(observation_id="c"))

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
