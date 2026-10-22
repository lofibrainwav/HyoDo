"""Regression fixtures for the root-locked local MCP read surface."""

import asyncio
import os
from pathlib import Path

import pytest
from test_mcp_stdio import call_hyodo_tool

from hyodo import mcp_readers
from hyodo.access_ledger import AccessEntry, record_access_result
from hyodo.agent_rules import load_agent_rules
from hyodo.ledger_origin import anchored_append
from hyodo.mcp_server import create_server
from hyodo.safety import collect_scan_corpus

RULES = (
    'schema = "hyodo.agent-rules/v1"\n'
    '[[rule]]\nname = "inside_fixture_marker"\n'
    'description = "inside"\nscope = "global"\nenabled = true\n'
)


def test_agent_rules_rejects_external_symlink(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    outside.mkdir()
    target = outside / "agent-rules.toml"
    target.write_text(
        'schema = "hyodo.agent-rules/v1"\n'
        '[[rule]]\nname = "outside_fixture_marker"\n'
        'description = "outside"\nscope = "global"\nenabled = true\n'
    )
    (root / ".hyodo" / "agent-rules.toml").symlink_to(target)

    with pytest.raises(ValueError, match="escapes the locked workspace"):
        load_agent_rules(root)


def test_safety_scan_skips_external_file_symlink(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "private.txt").write_text("outside_fixture_marker")
    (root / "linked.txt").symlink_to(outside / "private.txt")

    corpus, _source = collect_scan_corpus(str(root), cwd=root)
    assert "outside_fixture_marker" not in corpus


def test_agent_rules_accepts_inside_symlink_and_missing_file(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    (root / ".hyodo").mkdir(parents=True)
    assert load_agent_rules(root) == []
    (root / "rules.toml").write_text(RULES)
    (root / ".hyodo" / "agent-rules.toml").symlink_to(root / "rules.toml")
    assert [rule.name for rule in load_agent_rules(root)] == ["inside_fixture_marker"]


def test_agent_rules_rejects_external_parent_symlink(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "agent-rules.toml").write_text(RULES)
    (root / ".hyodo").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes the locked workspace"):
        load_agent_rules(root)


def test_agent_rules_permission_error_is_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    (root / ".hyodo").mkdir(parents=True)
    (root / ".hyodo" / "agent-rules.toml").write_text(RULES)
    original_open = os.open

    def denied(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == "agent-rules.toml":
            raise PermissionError("fixture denial")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", denied)
    with pytest.raises(ValueError, match="unreadable"):
        load_agent_rules(root)


def test_agent_rules_refuses_symlink_swap_before_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    outside.mkdir()
    target = root / ".hyodo" / "agent-rules.toml"
    target.write_text(RULES)
    (outside / "agent-rules.toml").write_text(RULES)
    original_open = os.open

    def swap(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == "agent-rules.toml":
            target.unlink()
            target.symlink_to(outside / "agent-rules.toml")
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap)
    with pytest.raises(ValueError, match="unreadable"):
        load_agent_rules(root)


def test_mcp_boundary_error_records_failed_audit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    outside.mkdir()
    (outside / "agent-rules.toml").write_text(RULES)
    (root / ".hyodo" / "agent-rules.toml").symlink_to(outside / "agent-rules.toml")
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    result = asyncio.run(call_hyodo_tool(create_server(root), "hyodo_agent_rules", {}))
    assert result["exit_code"] == 2
    assert "escapes the locked workspace" in result["error"]
    assert result["audit"]["state"] == "OBSERVED"
    ledger = root / ".hyodo" / "mcp-access.jsonl"
    assert '"exit_code": 2' in ledger.read_text()


def test_server_does_not_accept_replaced_project_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    (root / ".hyodo").mkdir(parents=True)
    (root / ".hyodo" / "agent-rules.toml").write_text(RULES)
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(mcp_readers, "process_start", lambda _pid: "synthetic-start")
    server = create_server(root)
    root.rename(tmp_path / "original-workspace")
    (root / ".hyodo").mkdir(parents=True)
    (root / ".hyodo" / "agent-rules.toml").write_text(
        RULES.replace("inside_fixture_marker", "outside_fixture_marker")
    )

    result = asyncio.run(call_hyodo_tool(server, "hyodo_agent_rules", {}))
    assert "outside_fixture_marker" not in str(result)
    assert not (root / ".hyodo" / "mcp-access.jsonl").exists()


def test_server_rejects_external_project_symlink_at_startup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "approved"
    outside = tmp_path / "outside"
    (outside / ".hyodo").mkdir(parents=True)
    (outside / ".hyodo" / "agent-rules.toml").write_text(
        RULES.replace("inside_fixture_marker", "outside_fixture_marker")
    )
    root.symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(mcp_readers, "process_start", lambda _pid: "synthetic-start")

    with pytest.raises(ValueError, match="workspace root"):
        create_server(root)
    assert not (outside / ".hyodo" / "mcp-access.jsonl").exists()


def test_server_rejects_project_link_swapped_during_root_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "approved"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    (outside / ".hyodo").mkdir(parents=True)
    (outside / ".hyodo" / "agent-rules.toml").write_text(
        RULES.replace("inside_fixture_marker", "outside_fixture_marker")
    )
    original_open = os.open

    def swap(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == "approved" and not root.is_symlink():
            root.rename(tmp_path / "original-approved")
            root.symlink_to(outside, target_is_directory=True)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap)
    with pytest.raises(ValueError, match="workspace root"):
        create_server(root)
    assert not (outside / ".hyodo" / "mcp-access.jsonl").exists()


def test_server_keeps_pinned_root_when_parent_swaps_during_call(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hyodo import agent_rules

    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    (root / ".hyodo" / "agent-rules.toml").write_text(RULES)
    (outside / ".hyodo").mkdir(parents=True)
    (outside / ".hyodo" / "agent-rules.toml").write_text(
        RULES.replace("inside_fixture_marker", "outside_fixture_marker")
    )
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(mcp_readers, "process_start", lambda _pid: "synthetic-start")
    server = create_server(root)
    original_read = agent_rules.read_workspace_bytes

    def swap_before_read(path: Path, relative: Path, *, root_fd: int | None = None) -> bytes:
        root.rename(tmp_path / "original-workspace")
        root.symlink_to(outside, target_is_directory=True)
        return original_read(path, relative, root_fd=root_fd)

    monkeypatch.setattr(agent_rules, "read_workspace_bytes", swap_before_read)
    result = asyncio.run(call_hyodo_tool(server, "hyodo_agent_rules", {}))
    assert "inside_fixture_marker" in str(result)
    assert "outside_fixture_marker" not in str(result)
    assert result["audit"]["state"] == "OBSERVED"
    assert (tmp_path / "original-workspace" / ".hyodo" / "mcp-access.jsonl").exists()
    assert not (outside / ".hyodo" / "mcp-access.jsonl").exists()


def test_mcp_audit_never_writes_through_external_hyodo_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / ".hyodo").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    result = asyncio.run(call_hyodo_tool(create_server(root), "hyodo_agent_rules", {}))
    assert result["exit_code"] == 2
    assert result["audit"]["state"] == "UNOBSERVED"
    assert not (outside / "mcp-access.jsonl").exists()


def test_mcp_event_record_rejects_external_ledger_symlink(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    outside.mkdir()
    (root / ".hyodo" / "agent-events.jsonl").symlink_to(outside / "agent-events.jsonl")
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    result = asyncio.run(call_hyodo_tool(create_server(root), "hyodo_event_record", {"event": {}}))
    assert result["exit_code"] == 2
    assert "escapes the locked workspace" in result["error"]
    assert result["audit"]["state"] == "OBSERVED"
    assert not (outside / "agent-events.jsonl").exists()


def test_ledger_append_refuses_symlink_swap_at_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    (root / ".hyodo").mkdir(parents=True)
    outside.mkdir()
    target = root / ".hyodo" / "agent-events.jsonl"
    outside_target = outside / "agent-events.jsonl"
    outside_target.write_text("outside_fixture_marker\n")
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    original_open = os.open

    def swap(path: object, flags: int, *args: object, **kwargs: object) -> int:
        if path == "agent-events.jsonl" and not target.exists():
            target.symlink_to(outside_target)
        return original_open(path, flags, *args, **kwargs)

    monkeypatch.setattr(os, "open", swap)
    with pytest.raises(OSError, match="path escapes the locked workspace"):
        anchored_append(root, Path(".hyodo/agent-events.jsonl"), "{}\n")
    assert outside_target.read_text() == "outside_fixture_marker\n"


def test_private_state_parent_symlink_fails_without_external_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (tmp_path / "state-link").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state-link"))
    entry = AccessEntry("2026-10-01T00:00:00+00:00", "hyodo_agent_rules", str(root), 0, 1)
    result = record_access_result(entry, root=root)
    assert result.state == "UNOBSERVED"
    assert list(outside.iterdir()) == []


def test_private_state_lock_symlink_fails_without_external_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    from hyodo.user_state import workspace_state_dir

    state_dir = workspace_state_dir(root)
    state_dir.mkdir(parents=True)
    outside = tmp_path / "outside.lock"
    outside.write_text("outside_fixture_marker")
    (state_dir / ".ledger-origin.lock").symlink_to(outside)
    entry = AccessEntry("2026-10-01T00:00:00+00:00", "hyodo_agent_rules", str(root), 0, 1)
    result = record_access_result(entry, root=root)
    assert result.state == "UNOBSERVED"
    assert outside.read_text() == "outside_fixture_marker"


def test_reader_registration_and_cleanup_use_private_directory_handle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    registry = tmp_path / "registry"
    monkeypatch.setenv(mcp_readers.READER_DIR_ENV, str(registry))
    monkeypatch.setattr(
        mcp_readers,
        "build_registration",
        lambda *_args: {
            "schema_version": mcp_readers.READER_SCHEMA_VERSION,
            "reader_pid": 43210,
            "process_start": "fixture-start",
        },
    )
    with mcp_readers.registered_reader(root, "stdio") as path:
        assert path is not None
        assert path.name == "43210.json"
        assert len(mcp_readers.load_registrations(registry)[0]) == 1
    assert not (registry / "43210.json").exists()


def test_reader_directory_symlink_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (tmp_path / "registry-link").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv(mcp_readers.READER_DIR_ENV, str(tmp_path / "registry-link"))
    with mcp_readers.registered_reader(root, "stdio") as path:
        assert path is None
    assert list(outside.iterdir()) == []


def test_private_anchor_symlink_is_not_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from hyodo.user_state import workspace_state_dir

    root = tmp_path / "workspace"
    root.mkdir()
    monkeypatch.setenv("HYODO_STATE_HOME", str(tmp_path / "state"))
    state_dir = workspace_state_dir(root)
    state_dir.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text("outside_fixture_marker")
    (state_dir / "ledger-origin.json").symlink_to(outside)
    entry = AccessEntry("2026-10-01T00:00:00+00:00", "hyodo_agent_rules", str(root), 0, 1)
    record_access_result(entry, root=root)
    assert outside.read_text() == "outside_fixture_marker"


def test_reader_final_symlink_is_not_replaced(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    registry = tmp_path / "registry"
    root.mkdir()
    registry.mkdir()
    outside = tmp_path / "outside.json"
    outside.write_text("outside_fixture_marker")
    (registry / "43210.json").symlink_to(outside)
    monkeypatch.setattr(
        mcp_readers,
        "build_registration",
        lambda *_args: {
            "schema_version": mcp_readers.READER_SCHEMA_VERSION,
            "reader_pid": 43210,
            "process_start": "fixture-start",
        },
    )
    assert mcp_readers.register_reader(root, root, "stdio", directory=registry) is None
    assert (registry / "43210.json").is_symlink()
    assert outside.read_text() == "outside_fixture_marker"


def test_reader_directory_swap_keeps_write_and_cleanup_on_pinned_handle(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    registry = tmp_path / "registry"
    moved = tmp_path / "registry-moved"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    monkeypatch.setenv(mcp_readers.READER_DIR_ENV, str(registry))
    monkeypatch.setattr(
        mcp_readers,
        "build_registration",
        lambda *_args: {
            "schema_version": mcp_readers.READER_SCHEMA_VERSION,
            "reader_pid": 43210,
            "process_start": "fixture-start",
        },
    )
    original_replace = os.replace

    def swap(src: object, dst: object, *args: object, **kwargs: object) -> None:
        if dst == "43210.json":
            registry.rename(moved)
            registry.symlink_to(outside, target_is_directory=True)
        original_replace(src, dst, *args, **kwargs)

    monkeypatch.setattr(os, "replace", swap)
    with mcp_readers.registered_reader(root, "stdio") as path:
        assert path is not None
        assert (moved / "43210.json").exists()
        assert list(outside.iterdir()) == []
    assert not (moved / "43210.json").exists()
    assert list(outside.iterdir()) == []
