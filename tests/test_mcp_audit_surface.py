from __future__ import annotations

import asyncio
import json
from pathlib import Path

from hyodo.access_ledger import AccessWriteResult
from hyodo.mcp_server import create_server


async def call_tool(server: object, name: str, arguments: dict) -> dict:
    outcome = await server.call_tool(name, arguments)  # type: ignore[attr-defined]
    if isinstance(outcome, tuple):
        data = outcome[1]
        assert isinstance(data, dict)
        return data
    for block in getattr(outcome, "content", []):
        text = getattr(block, "text", None)
        if text is not None:
            return json.loads(text)
    raise AssertionError(f"no text content block in {outcome!r}")


def test_tool_result_surfaces_observed_audit(tmp_path: Path) -> None:
    result = asyncio.run(call_tool(create_server(tmp_path), "get_local_context", {}))
    assert result["exit_code"] == 0
    assert result["audit"] == {"state": "OBSERVED", "reason": None}


def test_audit_write_failure_does_not_change_operation_result(tmp_path: Path, monkeypatch) -> None:
    from hyodo import mcp_server

    monkeypatch.setattr(
        mcp_server,
        "record_access_result",
        lambda *args, **kwargs: AccessWriteResult(
            path=tmp_path / ".hyodo" / "mcp-access.jsonl",
            state="UNOBSERVED",
            reason="write_failed",
        ),
    )
    result = asyncio.run(call_tool(create_server(tmp_path), "get_local_context", {}))
    assert result["exit_code"] == 0
    assert result["audit"] == {"state": "UNOBSERVED", "reason": "write_failed"}


def test_unexpected_audit_exception_is_fail_visible_and_non_fatal(tmp_path: Path, monkeypatch) -> None:
    from hyodo import mcp_server

    def explode(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(mcp_server, "record_access_result", explode)
    result = asyncio.run(call_tool(create_server(tmp_path), "get_local_context", {}))
    assert result["exit_code"] == 0
    assert result["audit"] == {
        "state": "UNOBSERVED",
        "reason": "record_access_exception",
    }


def test_early_path_validation_failure_is_audited(tmp_path: Path) -> None:
    result = asyncio.run(
        call_tool(
            create_server(tmp_path),
            "hyodo_policy_check",
            {"event": {}, "policy_path": "../outside.toml"},
        )
    )
    assert result["exit_code"] == 2
    assert result["error"] == "path escapes the locked workspace"
    assert result["audit"]["state"] == "OBSERVED"


def test_agent_rules_read_is_audited(tmp_path: Path) -> None:
    result = asyncio.run(call_tool(create_server(tmp_path), "hyodo_agent_rules", {}))
    assert isinstance(result["rules"], list)
    assert result["audit"] == {"state": "OBSERVED", "reason": None}
