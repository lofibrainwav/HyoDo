"""Contracts for MCP reader self-registration and the promotion cutover census."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from typer.testing import CliRunner

import hyodo
from hyodo import __version__, mcp_readers
from hyodo.access_ledger import read_access_log
from hyodo.cli.main import app
from hyodo.mcp_readers import (
    PROMOTION_COMPLETE,
    PROMOTION_INCOMPLETE,
    READER_SCHEMA_VERSION,
    STALE_RUNTIME_ERROR,
    UNOBSERVED,
    ReaderProcess,
    load_registrations,
    process_start,
    prune_retired_registrations,
    reader_transport,
    run_census,
)
from hyodo.mcp_server import create_server

runner = CliRunner()
_START = "Tue Sep 22 12:08:43 2026"


def _record(pid: int, root: Path, *, start: str = _START, **overrides: object) -> dict:
    record = {
        "schema_version": READER_SCHEMA_VERSION,
        "reader_pid": pid,
        "process_start": start,
        "parent_pid": 1,
        "parent_host": "claude",
        "transport": "stdio",
        "server_version": __version__,
        "python_version": "3.12.14",
        "resolved_root": str(root.resolve()),
        "runtime_commit": None,
    }
    record.update(overrides)
    return record


def _write(registry: Path, record: dict) -> None:
    registry.mkdir(parents=True, exist_ok=True)
    (registry / f"{record['reader_pid']}.json").write_text(json.dumps(record), encoding="utf-8")


def _slots(tmp_path: Path) -> tuple[Path, Path, Path]:
    old, new = tmp_path / "board-old", tmp_path / "board-new"
    old.mkdir()
    new.mkdir()
    current = tmp_path / "current"
    current.symlink_to(new)
    return old, new, current


def _census(current: Path, registry: Path, live: list[ReaderProcess], **kwargs):
    return run_census(
        current,
        directory=registry,
        processes=live,
        start_lookup=lambda pid: None,
        host_lookup=lambda ppid: "claude",
        **kwargs,
    )


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("/opt/Python -E /Users/u/.local/bin/hyodo mcp stdio --root /r/current", "stdio"),
        ("/usr/bin/python3 -m hyodo.cli.main mcp stdio --root .", "stdio"),
        ("hyodo mcp serve --port 8769", "serve"),
        ("hyodo mcp census --expect-root /r/current", None),
        ("/usr/bin/python3 -m other.tool mcp stdio", None),
        ("claude --resume abc", None),
    ],
)
def test_reader_transport_matches_only_hyodo_readers(command, expected):
    assert reader_transport(command) == expected


def test_reader_on_retired_slot_blocks_completion(tmp_path):
    old, _new, current = _slots(tmp_path)
    registry = tmp_path / "registry"
    _write(registry, _record(4101, old))

    receipt = _census(current, registry, [ReaderProcess(4101, 77, _START, "stdio")])

    assert receipt["cutover_status"] == PROMOTION_INCOMPLETE
    assert receipt["old_reader_count"] == 1
    assert receipt["fresh_reader_count"] == 0
    (reader,) = receipt["readers"]
    assert reader["reader_status"] == "STALE"
    assert reader["reasons"] == ["root_mismatch"]
    assert reader["resolved_root"] == str(old.resolve())


def test_unregistered_pre_gate_reader_counts_as_old(tmp_path):
    _old, _new, current = _slots(tmp_path)

    receipt = _census(current, tmp_path / "registry", [ReaderProcess(4102, 77, _START, "stdio")])

    assert receipt["cutover_status"] == PROMOTION_INCOMPLETE
    assert receipt["unknown_reader_count"] == 1
    assert receipt["old_reader_count"] == 1
    assert receipt["readers"][0]["registration_state"] == "UNREGISTERED"
    assert receipt["readers"][0]["parent_host"] == "claude"


def test_reused_pid_does_not_inherit_an_old_registration(tmp_path):
    _old, new, current = _slots(tmp_path)
    registry = tmp_path / "registry"
    # The record says CURRENT, but it belongs to an earlier process with this PID.
    _write(registry, _record(4103, new, start="Mon Sep 21 09:00:00 2026"))

    receipt = _census(current, registry, [ReaderProcess(4103, 77, _START, "stdio")])

    assert receipt["readers"][0]["reader_status"] == "UNKNOWN"
    assert receipt["cutover_status"] == PROMOTION_INCOMPLETE


def test_all_readers_on_promoted_slot_is_complete(tmp_path):
    _old, new, current = _slots(tmp_path)
    registry = tmp_path / "registry"
    _write(registry, _record(4104, new))
    _write(registry, _record(4105, new))

    receipt = _census(
        current,
        registry,
        [ReaderProcess(4104, 77, _START, "stdio"), ReaderProcess(4105, 78, _START, "stdio")],
        promotion_from=str(tmp_path / "board-old"),
        expect_version=__version__,
    )

    assert receipt["cutover_status"] == PROMOTION_COMPLETE
    assert receipt["fresh_reader_count"] == 2
    assert receipt["old_reader_count"] == 0
    assert receipt["promotion_to"] == str(new.resolve())
    assert receipt["promotion_from"] == str(tmp_path / "board-old")


def test_no_live_reader_is_an_observed_complete_cutover(tmp_path):
    _old, _new, current = _slots(tmp_path)

    empty = _census(current, tmp_path / "registry", [])

    assert empty["process_table"] == "OBSERVED"
    assert empty["cutover_status"] == PROMOTION_COMPLETE
    assert empty["fresh_reader_count"] == 0


def test_process_table_unobservable_is_not_complete(tmp_path, monkeypatch):
    _old, _new, current = _slots(tmp_path)
    monkeypatch.setattr(mcp_readers, "list_reader_processes", lambda: None)

    receipt = run_census(current, directory=tmp_path / "registry")

    assert receipt["cutover_status"] == UNOBSERVED
    assert receipt["old_reader_count"] is None


def test_version_and_commit_mismatch_are_stale(tmp_path):
    _old, new, current = _slots(tmp_path)
    subprocess.run(["git", "init", "-q", str(new)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(new),
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "slot",
        ],
        check=True,
    )
    registry = tmp_path / "registry"
    _write(registry, _record(4106, new, runtime_commit="0" * 40, server_version="4.0.0"))

    receipt = _census(
        current, registry, [ReaderProcess(4106, 77, _START, "stdio")], expect_version=__version__
    )

    assert receipt["commit_judged"] is True
    assert receipt["readers"][0]["reasons"] == ["commit_mismatch", "version_mismatch"]
    assert receipt["cutover_status"] == PROMOTION_INCOMPLETE


def test_registered_reader_missed_by_matcher_is_still_counted(tmp_path):
    old, _new, current = _slots(tmp_path)
    registry = tmp_path / "registry"
    _write(registry, _record(4107, old))
    _write(registry, _record(4108, old))  # its process has exited

    receipt = run_census(
        current,
        directory=registry,
        processes=[],
        start_lookup=lambda pid: _START if pid == 4107 else None,
        host_lookup=lambda ppid: None,
    )

    assert [reader["reader_pid"] for reader in receipt["readers"]] == [4107]
    assert receipt["retired_reader_count"] == 1
    assert receipt["registered_reader_count"] == 2
    assert receipt["cutover_status"] == PROMOTION_INCOMPLETE


def test_corrupt_registration_is_counted_not_trusted(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "1.json").write_text("{not json", encoding="utf-8")
    (registry / "2.json").write_text(json.dumps({"reader_pid": 2}), encoding="utf-8")

    records, corrupt = load_registrations(registry)

    assert records == []
    assert corrupt == 2


def test_census_cli_exit_codes_and_receipt(tmp_path, monkeypatch):
    old, new, current = _slots(tmp_path)
    registry = tmp_path / "registry"
    _write(registry, _record(4109, old))
    monkeypatch.setattr(
        mcp_readers,
        "list_reader_processes",
        lambda: [ReaderProcess(4109, 77, _START, "stdio")],
    )
    receipt_path = tmp_path / "out" / "census.json"
    args = ["mcp", "census", "--expect-root", str(current), "--registry", str(registry)]

    stale = runner.invoke(app, [*args, "--json", "--receipt", str(receipt_path)])
    assert stale.exit_code == 1
    assert json.loads(stale.output)["cutover_status"] == PROMOTION_INCOMPLETE
    assert json.loads(receipt_path.read_text())["old_reader_count"] == 1

    _write(registry, _record(4109, new))
    fresh = runner.invoke(app, args)
    assert fresh.exit_code == 0
    assert PROMOTION_COMPLETE in fresh.output

    monkeypatch.setattr(mcp_readers, "list_reader_processes", lambda: None)
    assert runner.invoke(app, args).exit_code == 2


def test_live_stdio_reader_registers_itself_and_unregisters_on_exit(tmp_path):
    """A real reader started through `current` is judged STALE after the swap."""
    old, new, _current = _slots(tmp_path)
    current = tmp_path / "current-live"
    current.symlink_to(old)
    registry = tmp_path / "registry"
    env = {**os.environ, mcp_readers.READER_DIR_ENV: str(registry)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "hyodo.cli.main", "mcp", "stdio", "--root", str(current)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        record_path = registry / f"{proc.pid}.json"
        deadline = time.monotonic() + 30
        while not record_path.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        record = json.loads(record_path.read_text(encoding="utf-8"))
        assert record["resolved_root"] == str(old.resolve())
        assert record["process_start"] == process_start(proc.pid)
        assert record["server_version"] == __version__
        assert record["root_arg"] == str(current)

        current.unlink()
        current.symlink_to(new)
        live = [ReaderProcess(proc.pid, os.getpid(), record["process_start"], "stdio")]
        receipt = _census(current, registry, live)
        assert receipt["readers"][0]["reader_status"] == "STALE"
        assert receipt["cutover_status"] == PROMOTION_INCOMPLETE
    finally:
        assert proc.stdin is not None
        proc.stdin.close()
        proc.wait(timeout=30)
    assert not (registry / f"{proc.pid}.json").exists()


def test_access_rows_name_the_reader_that_wrote_them(tmp_path):
    from hyodo.access_ledger import ACCESS_LEDGER_PATH, read_access_log
    from hyodo.mcp_server import _record_access

    ledger = tmp_path / ACCESS_LEDGER_PATH
    ledger.parent.mkdir(parents=True)
    # A row written before attribution existed must still read back.
    ledger.write_text(
        json.dumps(
            {
                "timestamp": "t0",
                "tool_name": "hyodo_check",
                "root": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 1,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    _record_access("get_local_context", tmp_path, 0, 5)

    legacy, current = read_access_log(tmp_path)
    assert (legacy.server_pid, legacy.server_version) == (None, None)
    assert (current.server_pid, current.server_version) == (os.getpid(), __version__)


async def _call(server: object, name: str, arguments: dict) -> dict:
    outcome = await server.call_tool(name, arguments)  # type: ignore[attr-defined]
    if isinstance(outcome, tuple):
        return outcome[1]
    for block in getattr(outcome, "content", []):
        text = getattr(block, "text", None)
        if text is not None:
            return json.loads(text)
    raise AssertionError(f"no text content block in {outcome!r}")


def _tool(server: object, name: str, arguments: dict | None = None) -> dict:
    import asyncio

    return asyncio.run(_call(server, name, arguments or {}))


def test_reader_refuses_to_measure_after_the_pointer_moves(tmp_path):
    old, new, _unused = _slots(tmp_path)
    current = tmp_path / "current-pin"
    current.symlink_to(old)
    server = create_server(current)

    before = _tool(server, "get_local_context")
    assert before["reader"]["state"] == "CURRENT"
    assert before["reader"]["pinned_root"] == str(old.resolve())

    current.unlink()
    current.symlink_to(new)

    context = _tool(server, "get_local_context")
    # The diagnostic still answers, from the pinned root, and names the drift.
    assert context["root"] == str(old.resolve())
    assert context["reader"]["state"] == "STALE"
    assert context["reader"]["reasons"] == ["root_moved"]
    assert context["reader"]["configured_root_now"] == str(new.resolve())
    assert context["reader"]["action"] == "RECONNECT_REQUIRED"

    for name, arguments in [
        ("hyodo_check", {}),
        ("hyodo_safe", {}),
        ("hyodo_agent_rules", {}),
        ("hyodo_policy_check", {"event": {}}),
        ("hyodo_event_record", {"event": {}}),
    ]:
        refused = _tool(server, name, arguments)
        assert refused["exit_code"] == 2, name
        assert refused["error"] == STALE_RUNTIME_ERROR, name


def test_reader_refuses_after_its_code_is_replaced(tmp_path, monkeypatch):
    server = create_server(tmp_path)
    monkeypatch.setattr(mcp_readers, "_version_on_disk", lambda: "99.0.0")

    refused = _tool(server, "hyodo_check")

    assert refused["error"] == STALE_RUNTIME_ERROR
    assert refused["reader"]["reasons"] == ["code_replaced"]
    assert refused["reader"]["code_version_on_disk"] == "99.0.0"


def test_reader_refuses_when_its_code_cannot_be_identified(tmp_path, monkeypatch):
    server = create_server(tmp_path)
    monkeypatch.setattr(mcp_readers, "_version_on_disk", lambda: None)

    refused = _tool(server, "hyodo_check")

    assert refused["error"] == STALE_RUNTIME_ERROR
    assert refused["reader"]["reasons"] == ["code_unobservable"]


def test_version_on_disk_reads_the_imported_package():
    assert mcp_readers._version_on_disk() == hyodo.__version__


def test_access_rows_identify_the_reader_instance(tmp_path):
    server = create_server(tmp_path)

    _tool(server, "get_local_context")

    (entry,) = read_access_log(tmp_path)
    assert entry.server_pid == os.getpid()
    assert entry.server_version == __version__
    assert entry.server_started_at == process_start(os.getpid())
    assert entry.root == str(tmp_path.resolve())


def test_pre_attribution_rows_read_back_as_none(tmp_path):
    ledger = tmp_path / ".hyodo" / "mcp-access.jsonl"
    ledger.parent.mkdir()
    ledger.write_text(
        json.dumps(
            {
                "timestamp": "2026-09-22T00:00:00+00:00",
                "tool_name": "hyodo_check",
                "root": str(tmp_path),
                "exit_code": 0,
                "duration_ms": 1,
                "caller_id": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    (entry,) = read_access_log(tmp_path)

    assert entry.server_pid is None
    assert entry.server_started_at is None
    assert entry.runtime_commit is None


def test_startup_gc_removes_only_provably_retired_records(tmp_path):
    _old, new, _current = _slots(tmp_path)
    registry = tmp_path / "registry"
    _write(registry, _record(4201, new, start="old-start"))
    _write(registry, _record(4202, new, start="live-start"))
    _write(registry, _record(4203, new, start="uncertain-start"))

    removed = prune_retired_registrations(
        directory=registry,
        exists_lookup=lambda pid: pid != 4201,
        start_lookup=lambda pid: "live-start" if pid == 4202 else None,
    )

    assert removed == 1
    assert not (registry / "4201.json").exists()
    assert (registry / "4202.json").exists()
    assert (registry / "4203.json").exists()


def test_startup_gc_removes_reused_pid_record(tmp_path):
    _old, new, _current = _slots(tmp_path)
    registry = tmp_path / "registry"
    _write(registry, _record(4301, new, start="previous-process"))

    removed = prune_retired_registrations(
        directory=registry,
        exists_lookup=lambda pid: True,
        start_lookup=lambda pid: "new-process",
    )

    assert removed == 1
    assert not (registry / "4301.json").exists()


def test_reader_start_prunes_dead_registration(tmp_path):
    _old, new, _current = _slots(tmp_path)
    current = tmp_path / "current-startup-gc"
    current.symlink_to(new)
    registry = tmp_path / "registry"
    _write(registry, _record(999999, new, start="dead-process"))
    env = {**os.environ, mcp_readers.READER_DIR_ENV: str(registry)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "hyodo.cli.main", "mcp", "stdio", "--root", str(current)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env,
    )
    try:
        live_path = registry / f"{proc.pid}.json"
        deadline = time.monotonic() + 30
        while not live_path.exists() and time.monotonic() < deadline:
            time.sleep(0.1)
        assert live_path.exists()
        assert not (registry / "999999.json").exists()
    finally:
        assert proc.stdin is not None
        proc.stdin.close()
        proc.wait(timeout=30)
