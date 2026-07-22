"""TDD contracts for the optional local stdio MCP adapter."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import uuid
from pathlib import Path

import tomllib
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


def _valid_event(**overrides: object) -> dict:
    event: dict = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": str(uuid.uuid4()),
        "run_id": str(uuid.uuid4()),
        "ts": "2026-07-22T00:00:00+00:00",
        "kind": "tool_call",
        "step_index": 0,
        "actor": "agent",
        "tool": {"name": "safe", "args_digest": None, "paths": []},
        "io": {"input_text": "customer prompt", "bytes_in": 15, "bytes_out": 0},
        "policy": {"decision": None, "rule_id": None, "reason": None},
        "meta": {"model": "test", "tags": []},
    }
    event.update(overrides)
    return event


def test_mcp_stdio_delegates_to_the_optional_adapter(tmp_path, monkeypatch):
    """The CLI only starts the adapter; it does not implement MCP itself."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo import mcp_server

    seen = []
    monkeypatch.setattr(mcp_server, "run_stdio", lambda root: seen.append(root))

    result = runner.invoke(app, ["mcp", "stdio", "--root", str(tmp_path)])

    assert result.exit_code == 0
    assert seen == [tmp_path]


def test_mcp_stdio_missing_workspace_exits_2(tmp_path):
    """A missing host workspace is an explicit observation failure, not a traceback."""
    missing = tmp_path / "missing-workspace"

    result = runner.invoke(app, ["mcp", "stdio", "--root", str(missing)])

    assert result.exit_code == 2
    assert "workspace root is not a directory" in result.output


def test_mcp_dependency_is_optional_for_core_installs():
    """MCP belongs to an opt-in extra and to the development test environment."""
    with Path("pyproject.toml").open("rb") as handle:
        project = tomllib.load(handle)["project"]

    extras = project["optional-dependencies"]
    assert any(requirement.startswith("mcp>=") for requirement in extras["mcp"])
    assert any(requirement.startswith("mcp>=") for requirement in extras["dev"])
    assert all(not requirement.startswith("mcp>=") for requirement in project["dependencies"])


def test_mcp_server_lists_only_the_m1_tools(tmp_path):
    """M1 exposes the documented local CLI wrappers and nothing transport-specific."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo.mcp_server import create_server

    tools = asyncio.run(create_server(tmp_path).list_tools())

    assert {tool.name for tool in tools} == {
        "get_local_context",
        "hyodo_safe",
        "hyodo_check",
        "hyodo_event_record",
        "hyodo_policy_check",
    }


def test_mcp_context_is_locked_to_the_configured_workspace(tmp_path):
    """The context tool reports the host root and never accepts a client path."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo.mcp_server import create_server

    _content, result = asyncio.run(create_server(tmp_path).call_tool("get_local_context", {}))

    assert result["root"] == str(tmp_path.resolve())
    assert result["exit_code"] == 0
    assert result["git_status"] == []


def test_mcp_safe_preserves_the_cli_json_exit_contract(tmp_path):
    """The MCP wrapper returns the exact JSON contract produced by ``hyodo safe``."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo.mcp_server import create_server

    sample = tmp_path / "leaked.txt"
    sample.write_text("aws_key = AKIAABCDEFGHIJKLMNOP\n", encoding="utf-8")
    _content, result = asyncio.run(create_server(tmp_path).call_tool("hyodo_safe", {}))

    payload = json.loads(result["stdout"])
    assert result["exit_code"] == payload["exit_code"] == 0
    assert any(finding["severity"] == "high" for finding in payload["findings"])


def test_mcp_event_record_preserves_digest_only_default(tmp_path):
    """MCP delegates event writes to the CLI and does not retain raw bodies by default."""
    from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
    from hyodo.mcp_server import create_server

    _content, result = asyncio.run(
        create_server(tmp_path).call_tool("hyodo_event_record", {"event": _valid_event()})
    )

    receipt = json.loads(result["stdout"])
    ledger = (tmp_path / AGENT_EVENTS_RELATIVE_PATH).read_text(encoding="utf-8")
    assert result["exit_code"] == receipt["exit_code"] == 0
    assert "input_text" not in ledger
    assert "input_digest" in ledger


def test_mcp_policy_preserves_unobserved_exit_and_rejects_path_escape(tmp_path):
    """Missing policy and client path traversal both stay explicit failures, never ALLOW."""
    from hyodo.mcp_server import create_server

    _content, unobserved = asyncio.run(
        create_server(tmp_path).call_tool("hyodo_policy_check", {"event": _valid_event()})
    )
    _content, escaped = asyncio.run(
        create_server(tmp_path).call_tool(
            "hyodo_policy_check",
            {"event": _valid_event(), "policy_path": "../policy.toml"},
        )
    )

    decision = json.loads(unobserved["stdout"])
    assert unobserved["exit_code"] == decision["exit_code"] == 2
    assert decision["decision"] == "UNOBSERVED"
    assert escaped["exit_code"] == 2
    assert escaped["error"] == "path escapes the locked workspace"


def test_mcp_stdio_protocol_lists_the_m1_tools(tmp_path):
    """A real stdio client can initialize the server and discover the documented tools."""

    async def run_client() -> set[str]:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "hyodo.cli.main", "mcp", "stdio", "--root", str(tmp_path)],
        )
        async with (
            stdio_client(params) as (read_stream, write_stream),
            ClientSession(read_stream, write_stream) as session,
        ):
            await session.initialize()
            response = await session.list_tools()
            return {tool.name for tool in response.tools}

    assert asyncio.run(run_client()) == {
        "get_local_context",
        "hyodo_safe",
        "hyodo_check",
        "hyodo_event_record",
        "hyodo_policy_check",
    }
