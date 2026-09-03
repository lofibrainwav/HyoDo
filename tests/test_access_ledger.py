"""TDD contracts for the MCP access ledger (M4 slice 2).

The access ledger records every MCP tool invocation that the local MCP
adapter serves, creating an audit trail in ``.hyodo/mcp-access.jsonl``.
It is separate from ``agent-events.jsonl`` (agent steps) and from
``policy.toml`` (rules).  Recording is best-effort: a ledger write
failure must never crash a tool call.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# a) AccessEntry creation and serialization round-trip
# ---------------------------------------------------------------------------


def test_access_entry_creation_and_roundtrip():
    """AccessEntry fields survive dataclass creation + JSON round-trip."""
    from hyodo.access_ledger import AccessEntry

    entry = AccessEntry(
        timestamp="2026-09-03T12:00:00+00:00",
        tool_name="hyodo_safe",
        root="/tmp/workspace",
        exit_code=0,
        duration_ms=120,
        caller_id=None,
    )
    data = asdict(entry)
    assert data["tool_name"] == "hyodo_safe"
    assert data["exit_code"] == 0
    assert data["caller_id"] is None

    # Round-trip through JSON
    raw = json.dumps(data)
    restored = json.loads(raw)
    assert restored["tool_name"] == "hyodo_safe"
    assert restored["root"] == "/tmp/workspace"


def test_access_entry_with_caller_id():
    """AccessEntry accepts an optional caller_id string."""
    from hyodo.access_ledger import AccessEntry

    entry = AccessEntry(
        timestamp="2026-09-03T12:00:00+00:00",
        tool_name="hyodo_check",
        root="/tmp/workspace",
        exit_code=1,
        duration_ms=50,
        caller_id="agent-001",
    )
    assert entry.caller_id == "agent-001"


# ---------------------------------------------------------------------------
# b) record_access writes a JSONL line that can be read back
# ---------------------------------------------------------------------------


def test_record_access_writes_jsonl_line(tmp_path: Path):
    """record_access appends one JSON line to the ledger file."""
    from hyodo.access_ledger import AccessEntry, record_access

    entry = AccessEntry(
        timestamp="2026-09-03T12:00:00+00:00",
        tool_name="hyodo_safe",
        root=str(tmp_path),
        exit_code=0,
        duration_ms=80,
        caller_id=None,
    )
    path = record_access(entry, root=tmp_path)
    assert path.exists()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    parsed = json.loads(lines[0])
    assert parsed["tool_name"] == "hyodo_safe"
    assert parsed["exit_code"] == 0


def test_record_access_appends_multiple(tmp_path: Path):
    """Multiple record_access calls append to the same file."""
    from hyodo.access_ledger import AccessEntry, record_access

    for i in range(3):
        record_access(
            AccessEntry(
                timestamp=f"2026-09-03T12:00:0{i}+00:00",
                tool_name="hyodo_check",
                root=str(tmp_path),
                exit_code=0,
                duration_ms=10,
                caller_id=None,
            ),
            root=tmp_path,
        )

    from hyodo.access_ledger import ACCESS_LEDGER_PATH

    lines = (tmp_path / ACCESS_LEDGER_PATH).read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3


# ---------------------------------------------------------------------------
# c) read_access_log returns entries in chronological order, respects limit
# ---------------------------------------------------------------------------


def test_read_access_log_chronological_order(tmp_path: Path):
    """read_access_log returns entries in file order (chronological)."""
    from hyodo.access_ledger import AccessEntry, read_access_log, record_access

    for i in range(5):
        record_access(
            AccessEntry(
                timestamp=f"2026-09-03T12:00:0{i}+00:00",
                tool_name=f"tool_{i}",
                root=str(tmp_path),
                exit_code=0,
                duration_ms=10 * i,
                caller_id=None,
            ),
            root=tmp_path,
        )

    entries = read_access_log(root=tmp_path)
    assert len(entries) == 5
    assert [e.tool_name for e in entries] == [
        "tool_0",
        "tool_1",
        "tool_2",
        "tool_3",
        "tool_4",
    ]


def test_read_access_log_respects_limit(tmp_path: Path):
    """read_access_log with limit returns only the most recent entries."""
    from hyodo.access_ledger import AccessEntry, read_access_log, record_access

    for i in range(10):
        record_access(
            AccessEntry(
                timestamp=f"2026-09-03T12:00:0{i}+00:00",
                tool_name=f"tool_{i}",
                root=str(tmp_path),
                exit_code=0,
                duration_ms=10,
                caller_id=None,
            ),
            root=tmp_path,
        )

    entries = read_access_log(root=tmp_path, limit=3)
    assert len(entries) == 3
    # Last 3 entries (chronological order, but limited to newest)
    assert [e.tool_name for e in entries] == ["tool_7", "tool_8", "tool_9"]


def test_read_access_log_empty(tmp_path: Path):
    """read_access_log on a workspace with no ledger returns empty list."""
    from hyodo.access_ledger import read_access_log

    entries = read_access_log(root=tmp_path)
    assert entries == []


# ---------------------------------------------------------------------------
# d) Tool calls in mcp_server are recorded in the ledger
# ---------------------------------------------------------------------------


def test_tool_call_records_access(monkeypatch, tmp_path: Path):
    """Each @server.tool() call in create_server records an access ledger entry."""
    from hyodo.access_ledger import read_access_log

    # Make _run_cli return a quick success dict
    monkeypatch.setattr(
        "hyodo.mcp_server._run_cli",
        lambda *a, **kw: {
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
        },
    )
    monkeypatch.setattr(
        "hyodo.mcp_server._run_git",
        lambda *a, **kw: (True, ""),
    )

    from hyodo.mcp_server import create_server

    server = create_server(tmp_path)
    # Call the tool function directly (they are synchronous)
    tool_fn = _find_tool_fn(server, "get_local_context")
    result = tool_fn()  # noqa: F841

    entries = read_access_log(root=tmp_path)
    assert len(entries) >= 1
    assert any(e.tool_name == "get_local_context" for e in entries)


def _find_tool_fn(server, tool_name: str):
    """Locate the underlying function for a named tool on an MCP server."""
    # SDK v1: FastMCP._tool_manager._tools[name].fn
    tm = getattr(server, "_tool_manager", None)
    if tm is not None:
        inner = getattr(tm, "_tools", None)
        if isinstance(inner, dict) and tool_name in inner:
            return inner[tool_name].fn
    # SDK v2: MCPServer._tools[name] or similar
    tools_dict = getattr(server, "_tools", None)
    if isinstance(tools_dict, dict) and tool_name in tools_dict:
        entry = tools_dict[tool_name]
        return getattr(entry, "fn", entry)
    raise RuntimeError(f"Cannot find tool {tool_name!r} on {type(server)}")


# ---------------------------------------------------------------------------
# e) Ledger write failure does not crash the tool call
# ---------------------------------------------------------------------------


def test_ledger_write_failure_does_not_crash_tool(monkeypatch, tmp_path: Path):
    """If record_access fails, the tool still returns its result."""
    monkeypatch.setattr(
        "hyodo.access_ledger.record_access",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("disk full")),
    )

    monkeypatch.setattr(
        "hyodo.mcp_server._run_cli",
        lambda *a, **kw: {
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
        },
    )
    monkeypatch.setattr(
        "hyodo.mcp_server._run_git",
        lambda *a, **kw: (True, ""),
    )

    from hyodo.mcp_server import create_server

    server = create_server(tmp_path)

    tool_fn = _find_tool_fn(server, "get_local_context")
    result = tool_fn()
    assert result["exit_code"] == 0


# ---------------------------------------------------------------------------
# f) CLI `hyodo mcp access-log` with mcp installed: exit 0, shows table
# ---------------------------------------------------------------------------


def test_mcp_access_log_table_output(tmp_path: Path):
    """``hyodo mcp access-log`` exits 0 and shows a human-readable table."""
    from hyodo.access_ledger import AccessEntry, record_access

    record_access(
        AccessEntry(
            timestamp="2026-09-03T12:00:00+00:00",
            tool_name="hyodo_safe",
            root=str(tmp_path),
            exit_code=0,
            duration_ms=120,
            caller_id=None,
        ),
        root=tmp_path,
    )

    result = runner.invoke(app, ["mcp", "access-log", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "hyodo_safe" in result.output


# ---------------------------------------------------------------------------
# g) CLI `hyodo mcp access-log --json`: exit 0, parseable JSON
# ---------------------------------------------------------------------------


def test_mcp_access_log_json_output(tmp_path: Path):
    """``hyodo mcp access-log --json`` exits 0 and emits parseable JSON."""
    from hyodo.access_ledger import AccessEntry, record_access

    record_access(
        AccessEntry(
            timestamp="2026-09-03T12:00:00+00:00",
            tool_name="hyodo_check",
            root=str(tmp_path),
            exit_code=1,
            duration_ms=50,
            caller_id="agent-007",
        ),
        root=tmp_path,
    )

    result = runner.invoke(app, ["mcp", "access-log", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert isinstance(payload, list)
    assert len(payload) == 1
    assert payload[0]["tool_name"] == "hyodo_check"
    assert payload[0]["exit_code"] == 1
    assert payload[0]["caller_id"] == "agent-007"


# ---------------------------------------------------------------------------
# h) CLI `hyodo mcp access-log` without mcp: exit 2, install hint
# ---------------------------------------------------------------------------


def test_mcp_access_log_without_mcp_exits_2(monkeypatch):
    """Without the MCP SDK, ``hyodo mcp access-log`` exits 2 with an install hint."""

    # Make get_mcp_server_class raise ModuleNotFoundError with name='mcp'
    def _raise_mcp_missing(*args, **kwargs):
        exc = ModuleNotFoundError(name="mcp")
        raise exc

    monkeypatch.setattr(
        "hyodo._mcp_compat.get_mcp_server_class",
        _raise_mcp_missing,
    )
    # Prevent the fallback import from succeeding
    monkeypatch.setitem(sys.modules, "mcp", None)

    result = runner.invoke(app, ["mcp", "access-log"])
    assert result.exit_code == 2
    assert "pip install" in result.output or "hyodo[mcp]" in result.output


# ---------------------------------------------------------------------------
# i) Public language: all new code is English-only
# ---------------------------------------------------------------------------


def test_access_ledger_public_language():
    """The access_ledger module contains no Korean prose (only English)."""
    import re

    import hyodo.access_ledger as mod

    source = Path(mod.__file__).read_text(encoding="utf-8")
    # Hangul syllable block — the same pattern the project's own scanner uses
    HANGUL = re.compile(r"[\uac00-\ud7a3]")
    # The six allowed virtue-label syllables
    ALLOWED_SYLLABLES = frozenset("\uc9c4\uc120\ubbf8\uc778\ud6a8\uc601")
    found = set(HANGUL.findall(source))
    offending = found - ALLOWED_SYLLABLES
    assert not offending, f"Korean prose found in access_ledger.py: {offending}"
