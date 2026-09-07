"""TDD contracts for the optional local stdio MCP adapter."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import threading
import time
import uuid
from pathlib import Path

import httpx
import pytest
import tomllib
import uvicorn
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.streamable_http import streamablehttp_client
from typer.testing import CliRunner

from hyodo.access_ledger import read_access_log
from hyodo.cli.main import app
from hyodo.pairing import PAIRING_RELATIVE_PATH, create_pairing, revoke_pairing

runner = CliRunner()


class _LoopbackServerThread:
    """Serve one ASGI app on 127.0.0.1 on an ephemeral port, in a daemon thread.

    Same pattern as ``tests/test_dashboard_server.py``'s ``ThreadingHTTPServer``
    fixture: a real socket bound to loopback only, never touching an external
    network, so the streamable-HTTP MCP client can drive a real request/response
    cycle including the SDK's session-manager lifespan.
    """

    def __init__(self, app: object) -> None:
        config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="warning")
        self.server = uvicorn.Server(config)
        self.thread = threading.Thread(target=self._run, daemon=True)

    def _run(self) -> None:
        asyncio.run(self.server.serve())

    def start(self) -> int:
        self.thread.start()
        for _ in range(500):
            if self.server.started:
                break
            time.sleep(0.02)
        else:
            raise RuntimeError("loopback test server did not start in time")
        port = self.server.servers[0].sockets[0].getsockname()[1]
        return port

    def stop(self) -> None:
        self.server.should_exit = True
        self.thread.join(timeout=5)


async def _call_tool_over_http(port: int, token: str, name: str, arguments: dict) -> dict:
    async with (
        streamablehttp_client(
            f"http://127.0.0.1:{port}/mcp",
            headers={"Authorization": f"Bearer {token}"},
        ) as (read, write, _get_session_id),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool(name, arguments)
        for block in result.content:
            text = getattr(block, "text", None)
            if text is not None:
                return json.loads(text)
        raise AssertionError(f"no text content block in {result!r}")


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


async def call_hyodo_tool(server: object, name: str, arguments: dict) -> dict:
    """Return the dict a HyoDo tool produced, on either MCP SDK major.

    SDK v1 FastMCP.call_tool returns ``(content, structured_data)``; v2
    MCPServer.call_tool returns one CallToolResult whose text block carries the
    JSON. Both must serialize to the same CLI JSON contract.
    """
    outcome = await server.call_tool(name, arguments)  # type: ignore[attr-defined]
    if isinstance(outcome, tuple):
        data = outcome[1]
        assert isinstance(data, dict), data
        return data
    for block in getattr(outcome, "content", []):
        text = getattr(block, "text", None)
        if text is not None:
            return json.loads(text)
    raise AssertionError(f"no text content block in {outcome!r}")


def test_mcp_stdio_delegates_to_the_optional_adapter(tmp_path, monkeypatch):
    """The CLI only starts the adapter; it does not implement MCP itself."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo import mcp_server

    seen = []
    monkeypatch.setattr(
        mcp_server,
        "run_stdio",
        lambda root, *, allow_full_body=False: seen.append((root, allow_full_body)),
    )

    result = runner.invoke(app, ["mcp", "stdio", "--root", str(tmp_path)])

    assert result.exit_code == 0
    # Full-body storage is operator consent and must default to off.
    assert seen == [(tmp_path, False)]


def test_mcp_stdio_full_body_requires_operator_flag(tmp_path, monkeypatch):
    """Only the person starting the server can enable raw-body storage."""
    from hyodo import mcp_server

    seen = []
    monkeypatch.setattr(
        mcp_server,
        "run_stdio",
        lambda root, *, allow_full_body=False: seen.append((root, allow_full_body)),
    )

    result = runner.invoke(app, ["mcp", "stdio", "--root", str(tmp_path), "--allow-full-body"])

    assert result.exit_code == 0
    assert seen == [(tmp_path, True)]


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
    names = {tool.name for tool in tools}

    assert names == {
        "get_local_context",
        "hyodo_safe",
        "hyodo_check",
        "hyodo_event_record",
        "hyodo_policy_check",
        "hyodo_agent_rules",
    }
    # M5-B receipt: no served tool runs a shell or reads/writes an arbitrary
    # path — every tool still shells out only to the fixed `hyodo` CLI SSOT.
    banned_substrings = ("shell", "exec", "read_file", "write_file")
    for name in names:
        for banned in banned_substrings:
            assert banned not in name, f"tool {name!r} looks like it grants {banned}"


def test_mcp_context_is_locked_to_the_configured_workspace(tmp_path):
    """The context tool reports the host root and never accepts a client path."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo.mcp_server import create_server

    result = asyncio.run(call_hyodo_tool(create_server(tmp_path), "get_local_context", {}))

    assert result["root"] == str(tmp_path.resolve())
    assert result["exit_code"] == 0
    assert result["git_status"] == []


def test_mcp_safe_preserves_the_cli_json_exit_contract(tmp_path):
    """The MCP wrapper returns the exact JSON contract produced by ``hyodo safe``."""
    assert importlib.util.find_spec("hyodo.mcp_server") is not None
    from hyodo.mcp_server import create_server

    sample = tmp_path / "leaked.txt"
    sample.write_text("aws_key = AKIAABCDEFGHIJKLMNOP\n", encoding="utf-8")
    result = asyncio.run(call_hyodo_tool(create_server(tmp_path), "hyodo_safe", {}))

    payload = json.loads(result["stdout"])
    assert result["exit_code"] == payload["exit_code"] == 0
    assert any(finding["severity"] == "high" for finding in payload["findings"])


def test_mcp_event_record_preserves_digest_only_default(tmp_path):
    """MCP delegates event writes to the CLI and does not retain raw bodies by default."""
    from hyodo.events import AGENT_EVENTS_RELATIVE_PATH
    from hyodo.mcp_server import create_server

    result = asyncio.run(
        call_hyodo_tool(create_server(tmp_path), "hyodo_event_record", {"event": _valid_event()})
    )

    receipt = json.loads(result["stdout"])
    ledger = (tmp_path / AGENT_EVENTS_RELATIVE_PATH).read_text(encoding="utf-8")
    assert result["exit_code"] == receipt["exit_code"] == 0
    assert "input_text" not in ledger
    assert "input_digest" in ledger


def test_mcp_policy_preserves_unobserved_exit_and_rejects_path_escape(tmp_path):
    """Missing policy and client path traversal both stay explicit failures, never ALLOW."""
    from hyodo.mcp_server import create_server

    unobserved = asyncio.run(
        call_hyodo_tool(create_server(tmp_path), "hyodo_policy_check", {"event": _valid_event()})
    )
    escaped = asyncio.run(
        call_hyodo_tool(
            create_server(tmp_path),
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
        "hyodo_agent_rules",
    }


def test_mcp_serve_only_delegates_the_loopback_transport(tmp_path, monkeypatch):
    """M2 leaves tool registration to M1 and fixes the listener to loopback."""
    from hyodo import mcp_server

    seen = []
    monkeypatch.setattr(
        mcp_server,
        "run_loopback",
        lambda root, *, port, token, paired=False: seen.append((root, port, token, paired)),
    )

    result = runner.invoke(
        app,
        ["mcp", "serve", "--bind", "loopback", "--port", "8769", "--root", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert seen == [(tmp_path, 8769, None, False)]
    assert "http://127.0.0.1:8769/mcp" in result.output


def test_mcp_serve_rejects_unknown_bind_dashboard_port_and_missing_root(tmp_path):
    """The explicit listener choices retain the dashboard and root protections."""
    invalid_bind = runner.invoke(app, ["mcp", "serve", "--bind", "public"])
    dashboard_port = runner.invoke(app, ["mcp", "serve", "--port", "8768"])
    missing_root = runner.invoke(app, ["mcp", "serve", "--root", str(tmp_path / "missing")])

    assert invalid_bind.exit_code == 2
    assert "Only --bind loopback or --bind tailscale is available" in invalid_bind.output
    assert dashboard_port.exit_code == 2
    assert "reserved for the HyoDo dashboard" in dashboard_port.output
    assert missing_root.exit_code == 2
    assert "workspace root is not a directory" in missing_root.output


def test_mcp_serve_never_accepts_a_public_workstation_listener(tmp_path):
    """M5-B receipt: no CLI path can bind a public/non-loopback, non-tailnet host."""
    public_bind = runner.invoke(app, ["mcp", "serve", "--bind", "0.0.0.0"])
    public_bind_ip = runner.invoke(
        app,
        [
            "mcp",
            "serve",
            "--bind",
            "tailscale",
            "--bind-ip",
            "0.0.0.0",
            "--token",
            "test-token",
        ],
    )

    assert public_bind.exit_code == 2
    assert "Only --bind loopback or --bind tailscale is available" in public_bind.output
    assert public_bind_ip.exit_code == 2
    assert "must be a Tailscale 100.64.0.0/10 address" in public_bind_ip.output


def test_mcp_tailscale_requires_token_and_delegates_only_a_tailnet_ip(tmp_path, monkeypatch):
    """T2 validates the tailnet address and bearer before any server is started."""
    from hyodo import mcp_server

    seen = []
    monkeypatch.setattr(
        mcp_server,
        "run_tailscale",
        lambda root, *, host, port, token, paired=False: seen.append(
            (root, host, port, token, paired)
        ),
    )

    missing_token = runner.invoke(
        app,
        ["mcp", "serve", "--bind", "tailscale", "--bind-ip", "100.99.88.77"],
    )
    public_ip = runner.invoke(
        app,
        [
            "mcp",
            "serve",
            "--bind",
            "tailscale",
            "--bind-ip",
            "192.168.1.20",
            "--token",
            "test-token",
        ],
    )
    successful = runner.invoke(
        app,
        [
            "mcp",
            "serve",
            "--bind",
            "tailscale",
            "--bind-ip",
            "100.99.88.77",
            "--token",
            "test-token",
            "--root",
            str(tmp_path),
        ],
    )

    assert missing_token.exit_code == 2
    assert "requires a non-empty bearer token" in missing_token.output
    assert public_ip.exit_code == 2
    assert "must be a Tailscale 100.64.0.0/10 address" in public_ip.output
    assert successful.exit_code == 0
    assert seen == [(tmp_path, "100.99.88.77", 8769, "test-token", False)]
    assert "http://100.99.88.77:8769/mcp" in successful.output


def test_mcp_tailscale_rejects_missing_or_blank_bind_ip_before_listen(tmp_path, monkeypatch):
    """T2 never guesses an interface or treats whitespace as an authentication token."""
    from hyodo import mcp_server

    monkeypatch.setattr(
        mcp_server,
        "run_tailscale",
        lambda root, *, host, port, token, paired=False: pytest.fail("T2 must not listen"),
    )

    missing_ip = runner.invoke(
        app,
        ["mcp", "serve", "--bind", "tailscale", "--token", "test-token"],
    )
    blank_token = runner.invoke(
        app,
        [
            "mcp",
            "serve",
            "--bind",
            "tailscale",
            "--bind-ip",
            "100.99.88.77",
            "--token",
            "   ",
        ],
    )

    assert missing_ip.exit_code == 2
    assert "requires --bind-ip" in missing_ip.output
    assert blank_token.exit_code == 2
    assert "requires a non-empty bearer token" in blank_token.output


def test_mcp_loopback_auth_rejects_missing_or_invalid_bearer_before_tools():
    """A configured M2 token returns 401 before a request reaches MCP tools."""
    from hyodo.mcp_server import _BearerTokenMiddleware

    async def status_for(headers: list[tuple[bytes, bytes]]) -> tuple[int, bool]:
        reached = False
        messages = []

        async def app(scope, receive, send):
            nonlocal reached
            reached = True

        async def send(message):
            messages.append(message)

        async def receive():
            return {"type": "http.disconnect"}

        await _BearerTokenMiddleware(app, "expected-token")(
            {"type": "http", "headers": headers},
            receive,
            send,
        )
        return messages[0]["status"], reached

    assert asyncio.run(status_for([])) == (401, False)
    assert asyncio.run(status_for([(b"authorization", b"Bearer wrong-token")])) == (401, False)


def test_mcp_loopback_auth_allows_valid_bearer_to_reach_the_mcp_endpoint():
    """A valid configured bearer reaches the SDK endpoint instead of a 401 response."""
    from hyodo.mcp_server import _BearerTokenMiddleware

    reached = False

    async def app(scope, receive, send):
        nonlocal reached
        reached = True

    async def receive():
        return {"type": "http.disconnect"}

    async def send(message):
        return None

    asyncio.run(
        _BearerTokenMiddleware(app, "expected-token")(
            {"type": "http", "headers": [(b"authorization", b"Bearer expected-token")]},
            receive,
            send,
        )
    )

    assert reached


# ── M5-B: paired loopback bridge receipts ──────────────────────────────────


async def _post_mcp(asgi_app, token: str | None) -> httpx.Response:
    """One raw HTTP POST against a paired app's rejection path.

    The pairing middleware rejects before the MCP session manager is ever
    reached, so this does not need a running server or lifespan — an ASGI
    transport is enough for the negative paths.
    """
    transport = httpx.ASGITransport(app=asgi_app)
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post("/mcp", headers=headers, json={})


def test_mcp_paired_bridge_authenticated_route_reaches_the_locked_workspace(tmp_path):
    """Receipt: one authenticated remote route reaches one root-locked workspace."""
    from hyodo.access_ledger import AccessEntry
    from hyodo.mcp_server import create_loopback_app
    from hyodo.pairing import load_pairing

    record, token = create_pairing(tmp_path)
    assert record.last_seen_at is None

    app_under_test = create_loopback_app(tmp_path, paired=True)
    server = _LoopbackServerThread(app_under_test)
    port = server.start()
    try:
        result = asyncio.run(_call_tool_over_http(port, token, "get_local_context", {}))
    finally:
        server.stop()

    assert result["exit_code"] == 0
    assert result["root"] == str(tmp_path.resolve())

    # Every served request updates last_seen_at.
    after = load_pairing(tmp_path)
    assert after is not None
    assert after.last_seen_at is not None

    # And is recorded in the access ledger against the pairing's workspace_id,
    # never the token.
    entries: list[AccessEntry] = read_access_log(tmp_path)
    assert entries, "expected at least one access ledger entry"
    assert entries[-1].caller_id == record.workspace_id


def test_mcp_paired_bridge_revoked_token_is_rejected(tmp_path):
    """Receipt: revoke takes effect immediately — same token, 401 REVOKED."""
    from hyodo.mcp_server import create_loopback_app

    _record, token = create_pairing(tmp_path)
    revoke_pairing(tmp_path)
    app_under_test = create_loopback_app(tmp_path, paired=True)

    response = asyncio.run(_post_mcp(app_under_test, token))

    assert response.status_code == 401
    assert response.json() == {"state": "REVOKED"}


def test_mcp_paired_bridge_unpaired_workspace_is_rejected(tmp_path):
    """Receipt: no pairing file at all — 401 UNPAIRED, never PASS."""
    from hyodo.mcp_server import create_loopback_app

    app_under_test = create_loopback_app(tmp_path, paired=True)

    response = asyncio.run(_post_mcp(app_under_test, "some-token"))

    assert response.status_code == 401
    assert response.json() == {"state": "UNPAIRED"}


def test_mcp_paired_bridge_corrupt_pairing_file_is_unobserved(tmp_path):
    """Receipt: a present-but-unreadable pairing file fails closed as UNOBSERVED."""
    from hyodo.mcp_server import create_loopback_app

    path = tmp_path / PAIRING_RELATIVE_PATH
    path.parent.mkdir(parents=True)
    path.write_text("{not json", encoding="utf-8")
    app_under_test = create_loopback_app(tmp_path, paired=True)

    response = asyncio.run(_post_mcp(app_under_test, "any-token"))

    assert response.status_code == 503
    assert response.json() == {"state": "UNOBSERVED"}


def test_mcp_paired_bridge_never_persists_the_token(tmp_path):
    """Receipt: the bearer token is never written to the pairing file or the ledger."""
    from hyodo.mcp_server import create_loopback_app

    record, token = create_pairing(tmp_path)
    app_under_test = create_loopback_app(tmp_path, paired=True)
    server = _LoopbackServerThread(app_under_test)
    port = server.start()
    try:
        asyncio.run(_call_tool_over_http(port, token, "get_local_context", {}))
    finally:
        server.stop()

    pairing_raw = (tmp_path / PAIRING_RELATIVE_PATH).read_text(encoding="utf-8")
    assert token not in pairing_raw

    ledger_path = tmp_path / ".hyodo" / "mcp-access.jsonl"
    ledger_raw = ledger_path.read_text(encoding="utf-8")
    assert token not in ledger_raw
    assert record.workspace_id in ledger_raw


def test_mcp_serve_paired_and_static_token_are_mutually_exclusive(tmp_path):
    """--paired verifies against the pairing record; a static --token is refused."""
    result = runner.invoke(
        app,
        [
            "mcp",
            "serve",
            "--paired",
            "--token",
            "static-token",
            "--root",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 2
    assert "do not also" in result.output
    assert "--token" in result.output


def test_mcp_serve_paired_delegates_paired_flag_to_run_loopback(tmp_path, monkeypatch):
    from hyodo import mcp_server

    seen = []
    monkeypatch.setattr(
        mcp_server,
        "run_loopback",
        lambda root, *, port, token, paired=False: seen.append((root, port, token, paired)),
    )

    result = runner.invoke(
        app,
        ["mcp", "serve", "--bind", "loopback", "--paired", "--root", str(tmp_path)],
    )

    assert result.exit_code == 0
    assert seen == [(tmp_path, 8769, None, True)]
