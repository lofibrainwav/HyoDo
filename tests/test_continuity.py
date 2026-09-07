"""Receipts for M5-D cross-model continuity.

What is proven locally: two distinct MCP callers against the *same*
workspace — the stdio adapter (host A) and the paired loopback HTTP bridge
(host B) — read and write the same four local truth stores
(``.hyodo/agent-events.jsonl``, ``.hyodo/policy.toml``,
``.hyodo/mcp-access.jsonl``, ``.hyodo/pairing.json``) with no second store
appearing. ChatGPT/the remote connector is never driven here and stays
``UNOBSERVED`` in every receipt — see ``hyodo.continuity`` and
``docs/M5_REMOTE_CONNECTOR_CONTRACT.md``'s M5-D section.
"""

from __future__ import annotations

import asyncio
import json
import threading
import time
import uuid
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.access_ledger import ACCESS_LEDGER_PATH, read_access_log
from hyodo.cli.main import app
from hyodo.continuity import CONTINUITY_SCHEMA_VERSION, STDIO_IDENTITY, measure_continuity
from hyodo.events import AGENT_EVENTS_RELATIVE_PATH, read_agent_events
from hyodo.mcp_server import create_loopback_app, create_server
from hyodo.pairing import create_pairing

try:  # HTTP bridge tests need extras the base test lane does not install.
    import httpx
    import uvicorn
    from mcp.client.streamable_http import streamablehttp_client
except ImportError:  # pragma: no cover - exercised only in the base lane
    httpx = None  # type: ignore[assignment]
    uvicorn = None  # type: ignore[assignment]
    streamablehttp_client = None  # type: ignore[assignment]

from mcp import ClientSession

needs_http_bridge = pytest.mark.skipif(
    httpx is None or uvicorn is None or streamablehttp_client is None,
    reason="httpx, uvicorn, and the streamable HTTP client are required",
)

runner = CliRunner()


class _LoopbackServerThread:
    """Serve one ASGI app on 127.0.0.1 on an ephemeral port, in a daemon thread.

    Identical pattern to ``tests/test_mcp_stdio.py``'s helper of the same
    name: a real socket on loopback only, driving the SDK's real
    session-manager lifespan for the paired bridge (host B).
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


async def call_hyodo_tool(server: object, name: str, arguments: dict) -> dict:
    """Return the dict a HyoDo tool produced, on either MCP SDK major."""
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


def _valid_event(run_id: str, **overrides: object) -> dict:
    event: dict = {
        "schema_version": "hyodo.agent-event/v1",
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "ts": "2026-09-07T00:00:00+00:00",
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


def _store_files(root: Path) -> set[Path]:
    """Every ``*.jsonl``/``*.db``/``*.sqlite`` file under *root*, outside ``.git``."""
    found: set[Path] = set()
    for pattern in ("*.jsonl", "*.db", "*.sqlite"):
        for path in root.rglob(pattern):
            if ".git" not in path.parts:
                found.add(path)
    return found


@needs_http_bridge
def test_two_hosts_write_the_same_truth_store_and_continuity_reports_it(tmp_path) -> None:
    """The full M5-D receipt: host A (stdio) and host B (paired) share one workspace."""
    run_id_a = str(uuid.uuid4())
    run_id_b = str(uuid.uuid4())

    before = _store_files(tmp_path)

    # Host A: the stdio adapter, driven in-process exactly as `create_server`
    # is used elsewhere — no caller_id, so its ledger rows carry caller_id=null.
    server_a = create_server(tmp_path)
    context_a = asyncio.run(call_hyodo_tool(server_a, "get_local_context", {}))
    assert context_a["exit_code"] == 0
    safe_a = asyncio.run(call_hyodo_tool(server_a, "hyodo_safe", {}))
    assert safe_a["exit_code"] == 0
    record_a = asyncio.run(
        call_hyodo_tool(server_a, "hyodo_event_record", {"event": _valid_event(run_id_a)})
    )
    assert json.loads(record_a["stdout"])["exit_code"] == 0

    # Host B: the paired loopback HTTP bridge, over a real socket, exactly as
    # tests/test_mcp_stdio.py's M5-B receipts drive it.
    pairing_record, token = create_pairing(tmp_path)
    app_under_test = create_loopback_app(tmp_path, paired=True)
    http_server = _LoopbackServerThread(app_under_test)
    port = http_server.start()
    try:
        context_b = asyncio.run(_call_tool_over_http(port, token, "get_local_context", {}))
        assert context_b["exit_code"] == 0
        record_b_raw = asyncio.run(
            _call_tool_over_http(
                port, token, "hyodo_event_record", {"event": _valid_event(run_id_b)}
            )
        )
        assert json.loads(record_b_raw["stdout"])["exit_code"] == 0
    finally:
        http_server.stop()

    # (1) Both events landed in the one agent-event ledger.
    events, corrupt = read_agent_events(tmp_path)
    assert corrupt == 0
    assert events is not None
    run_ids = {event.get("run_id") for event in events}
    assert {run_id_a, run_id_b} <= run_ids
    assert len(events) == 2

    # (2) `hyodo report --format graph` shows both actors' events in one graph.
    report_result = runner.invoke(
        app, ["report", "--root", str(tmp_path), "--format", "graph", "--json"]
    )
    assert report_result.exit_code == 0, report_result.output
    graph_path = tmp_path / ".hyodo" / "reports" / "hyodo-report.graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph_run_ids = {node["run_id"] for node in graph["nodes"]}
    assert {run_id_a, run_id_b} <= graph_run_ids
    assert len(graph["nodes"]) == 2

    # (3) The access ledger has two distinct caller identities.
    entries = read_access_log(tmp_path)
    caller_ids = {entry.caller_id for entry in entries}
    assert None in caller_ids
    assert pairing_record.workspace_id in caller_ids
    assert len(caller_ids) == 2

    # (4) `hyodo mcp continuity --json` reports hosts observed 2/2, a single
    # ledger digest, and remote UNOBSERVED.
    continuity_result = runner.invoke(app, ["mcp", "continuity", "--root", str(tmp_path), "--json"])
    assert continuity_result.exit_code == 0, continuity_result.output
    receipt = json.loads(continuity_result.output)
    assert receipt["schema_version"] == CONTINUITY_SCHEMA_VERSION
    assert receipt["status"] == "READY"
    assert receipt["integrity_status"] == "READY"
    assert receipt["coverage_status"] == "OBSERVED"
    assert receipt["hosts"]["observed"] == 2
    assert receipt["hosts"]["expected"] == 2
    assert receipt["hosts"]["label"] == "hosts observed: 2/2 expected"
    assert receipt["remote"] == {"status": "UNOBSERVED", "reason": "remote_not_probed"}
    identities = {caller["identity"] for caller in receipt["callers"]}
    assert identities == {STDIO_IDENTITY, f"paired:{pairing_record.workspace_id}"}
    # One ledger, one digest — never a per-caller store.
    assert receipt["stores"]["agent_events"]["count"] == 2
    assert receipt["stores"]["agent_events"]["digest"] is not None
    assert receipt["continuity"]["same_ledger"] is True
    assert (
        receipt["continuity"]["agent_events_digest"] == receipt["stores"]["agent_events"]["digest"]
    )
    for caller in receipt["callers"]:
        assert receipt["continuity"]["event_record_calls_per_caller"][caller["identity"]] == 1

    # (5) `hyodo mcp contract --json` folds the same receipt in, additively.
    contract_result = runner.invoke(app, ["mcp", "contract", "--root", str(tmp_path), "--json"])
    assert contract_result.exit_code == 0, contract_result.output
    contract = json.loads(contract_result.output)
    assert contract["continuity"] == {"local": "OBSERVED", "remote": "UNOBSERVED"}

    # (6) No other *.jsonl/*.db/*.sqlite store appeared anywhere under the root.
    after = _store_files(tmp_path)
    new_files = after - before
    assert new_files == {
        tmp_path / AGENT_EVENTS_RELATIVE_PATH,
        tmp_path / ACCESS_LEDGER_PATH,
    }


def test_continuity_reports_unobserved_and_exit_2_on_a_corrupt_ledger(tmp_path) -> None:
    """A present-but-corrupt agent-event ledger fails closed as UNOBSERVED, never READY."""
    ledger_path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text(
        '{"schema_version": "hyodo.agent-event/v1"}\nnot json\n', encoding="utf-8"
    )

    result = runner.invoke(app, ["mcp", "continuity", "--root", str(tmp_path), "--json"])

    assert result.exit_code == 2
    receipt = json.loads(result.output)
    assert receipt["status"] == "UNOBSERVED"
    assert receipt["integrity_status"] == "CORRUPT"
    assert "agent_events_corrupt" in receipt["reasons"]
    assert receipt["stores"]["agent_events"]["corrupt_lines"] == 1


def test_continuity_is_per_workspace_not_global(tmp_path) -> None:
    """Two different workspace roots are two different truths, not one shared one."""
    root_a = tmp_path / "workspace-a"
    root_b = tmp_path / "workspace-b"
    root_a.mkdir()
    root_b.mkdir()

    server_a = create_server(root_a)
    record_a = asyncio.run(
        call_hyodo_tool(server_a, "hyodo_event_record", {"event": _valid_event(str(uuid.uuid4()))})
    )
    assert json.loads(record_a["stdout"])["exit_code"] == 0

    receipt_a = measure_continuity(root_a)
    receipt_b = measure_continuity(root_b)

    assert receipt_a["stores"]["agent_events"]["exists"] is True
    assert receipt_b["stores"]["agent_events"]["exists"] is False
    assert (
        receipt_a["stores"]["agent_events"]["digest"]
        != receipt_b["stores"]["agent_events"]["digest"]
    )
    assert receipt_a["root"] != receipt_b["root"]


def test_continuity_never_probes_remote_regardless_of_local_state(tmp_path) -> None:
    """Remote stays UNOBSERVED with reason remote_not_probed on every input shape."""
    empty = measure_continuity(tmp_path)
    assert empty["remote"] == {"status": "UNOBSERVED", "reason": "remote_not_probed"}

    create_pairing(tmp_path)
    paired = measure_continuity(tmp_path)
    assert paired["remote"] == {"status": "UNOBSERVED", "reason": "remote_not_probed"}


def test_continuity_optional_stores_absent_does_not_corrupt_integrity(tmp_path) -> None:
    """No policy.toml and no pairing.json is integrity READY — both are optional.

    An empty workspace still has nothing observed, though: overall `status`
    stays UNOBSERVED (see the empty-root coverage test below), which is the
    behavior this test used to assert as READY before the false-green fix.
    """
    receipt = measure_continuity(tmp_path)

    assert receipt["integrity_status"] == "READY"
    assert receipt["stores"]["policy"]["exists"] is False
    assert receipt["stores"]["pairing"]["exists"] is False


def test_continuity_empty_root_is_unobserved_not_ready(tmp_path) -> None:
    """An empty root (no `.hyodo` stores, 0/2 hosts) must never read as READY.

    Regression for the false-green: `measure_continuity` used to only append
    `reasons` for corrupt/invalid stores, so "nothing exists" == READY. It
    means "nothing present is broken", not "continuity connected" — the two
    are now split into `integrity_status` and `coverage_status`.
    """
    receipt = measure_continuity(tmp_path)

    assert receipt["integrity_status"] == "READY"
    assert receipt["coverage_status"] == "UNOBSERVED"
    assert receipt["status"] == "UNOBSERVED"
    assert receipt["exit_code"] == 2
    assert "hosts_unobserved" in receipt["reasons"]
    assert receipt["hosts"]["observed"] == 0

    result = runner.invoke(app, ["mcp", "continuity", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 2
    cli_receipt = json.loads(result.output)
    assert cli_receipt["status"] == "UNOBSERVED"
    assert cli_receipt["coverage_status"] == "UNOBSERVED"


def test_continuity_one_caller_is_partial_coverage(tmp_path) -> None:
    """One observed caller (of 2 expected) is PARTIAL coverage, not OBSERVED.

    Overall `status` stays UNOBSERVED (fail-closed) even though the stores
    that do exist are readable — `integrity_status` is READY, but
    `coverage_status` PARTIAL keeps the overall receipt honest.
    """
    run_id = str(uuid.uuid4())
    server = create_server(tmp_path)
    record = asyncio.run(
        call_hyodo_tool(server, "hyodo_event_record", {"event": _valid_event(run_id)})
    )
    assert json.loads(record["stdout"])["exit_code"] == 0

    receipt = measure_continuity(tmp_path)

    assert receipt["hosts"]["observed"] == 1
    assert receipt["integrity_status"] == "READY"
    assert receipt["coverage_status"] == "PARTIAL"
    assert receipt["status"] == "UNOBSERVED"
    assert receipt["exit_code"] == 2
    assert "hosts_partial" in receipt["reasons"]


def test_continuity_corrupt_store_is_corrupt_integrity_regardless_of_coverage(tmp_path) -> None:
    """A corrupt store is `integrity_status: CORRUPT`, and overall UNOBSERVED.

    Integrity failure overrides coverage: even if hosts were fully observed,
    a corrupt store must never let `status` read READY.
    """
    ledger_path = tmp_path / AGENT_EVENTS_RELATIVE_PATH
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text(
        '{"schema_version": "hyodo.agent-event/v1"}\nnot json\n', encoding="utf-8"
    )

    receipt = measure_continuity(tmp_path)

    assert receipt["integrity_status"] == "CORRUPT"
    assert receipt["status"] == "UNOBSERVED"
    assert receipt["exit_code"] == 2
    assert "agent_events_corrupt" in receipt["reasons"]
