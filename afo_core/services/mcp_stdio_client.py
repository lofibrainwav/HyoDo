from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen
from threading import Lock
from typing import Any


class MCPStdioError(RuntimeError):
    pass


@dataclass(frozen=True)
class MCPServerConfig:
    command: str
    args: list[str]
    env: dict[str, str] | None = None


@dataclass
class MCPProcessSession:
    """MCP server process session with connection reuse."""

    config: MCPServerConfig
    process: Popen | None = None
    initialized: bool = False
    last_used: float = 0.0
    request_id: int = 1
    lock: Lock | None = None

    def __post_init__(self) -> None:
        if self.lock is None:
            self.lock = threading.Lock()


_DEFAULT_PATTERN = re.compile(r"\$\{([A-Z0-9_]+):-([^}]+)\}")


def _expand_default_vars(value: str) -> str:
    value = _DEFAULT_PATTERN.sub(lambda m: os.getenv(m.group(1), m.group(2)), value)
    return os.path.expandvars(value)


def _find_repo_root() -> Path:
    here = Path(__file__).resolve()

    # Prefer the actual git root when available.
    for parent in [here, *here.parents]:
        if (parent / ".git").exists():
            return parent

    # Fallback: choose the outermost AGENTS.md (monorepo has nested AGENTS.md).
    last_agents: Path | None = None
    for parent in [here, *here.parents]:
        if (parent / "AGENTS.md").exists():
            last_agents = parent
    if last_agents:
        return last_agents

    raise MCPStdioError("repo root not found (.git/AGENTS.md missing in parents)")


def _load_cursor_mcp_json(repo_root: Path) -> dict[str, Any]:
    cfg_path = repo_root / ".cursor" / "mcp.json"
    if not cfg_path.exists():
        raise MCPStdioError(f"missing MCP config: {cfg_path}")
    try:
        result: dict[str, Any] = json.loads(cfg_path.read_text(encoding="utf-8"))
        return result
    except Exception as e:
        raise MCPStdioError(f"failed to parse {cfg_path}: {e}") from e


def load_mcp_server_config(server_name: str, *, repo_root: Path | None = None) -> MCPServerConfig:
    root = repo_root or _find_repo_root()
    data = _load_cursor_mcp_json(root)
    servers = data.get("mcpServers", {})
    if server_name not in servers:
        raise MCPStdioError(f"server '{server_name}' not found in .cursor/mcp.json")

    raw = servers[server_name]
    command = str(raw.get("command") or "").strip()
    if not command:
        raise MCPStdioError(f"server '{server_name}' missing 'command'")

    args_raw = raw.get("args") or []
    if not isinstance(args_raw, list):
        raise MCPStdioError(f"server '{server_name}' has invalid 'args'")
    args = [_expand_default_vars(str(a)) for a in args_raw]

    env_raw = raw.get("env")
    env: dict[str, str] | None = None
    if isinstance(env_raw, dict):
        env = {str(k): _expand_default_vars(str(v)) for k, v in env_raw.items()}

    return MCPServerConfig(command=_expand_default_vars(command), args=args, env=env)


def _rpc_call(
    cfg: MCPServerConfig,
    *,
    method: str,
    params: dict[str, Any] | None = None,
    timeout_sec: float = 20.0,
) -> dict[str, Any]:
    start = time.monotonic()

    def remaining() -> float:
        return max(0.1, timeout_sec - (time.monotonic() - start))

    stderr_ring: deque[str] = deque(maxlen=200)

    def stderr_tail() -> str:
        return "".join(stderr_ring).strip()[-2000:]

    def read_line_with_timeout() -> str:
        line_holder: list[str] = []

        def _read() -> None:
            assert proc.stdout is not None
            line_holder.append(proc.stdout.readline())

        t = threading.Thread(target=_read, daemon=True)
        t.start()
        t.join(timeout=remaining())
        if t.is_alive():
            raise MCPStdioError(
                "timeout waiting for MCP response "
                f"(command={cfg.command}, args={cfg.args}, stderr tail: {stderr_tail()})"
            )
        return line_holder[0] if line_holder else ""

    def read_jsonrpc_with_timeout(*, expected_id: int | None = None) -> dict[str, Any]:
        while True:
            line = read_line_with_timeout()
            if not line:
                raise MCPStdioError(
                    "no response from MCP server "
                    f"(command={cfg.command}, args={cfg.args}, stderr tail: {stderr_tail()})"
                )
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                # Some servers can be noisy; ignore non-JSON lines.
                continue
            if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
                continue
            if expected_id is not None and payload.get("id") != expected_id:
                # Ignore out-of-band messages when we're waiting for a specific response.
                continue
            return payload

    env = os.environ.copy()
    if cfg.env:
        env.update(cfg.env)

    proc = subprocess.Popen(
        [cfg.command, *cfg.args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        bufsize=1,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    assert proc.stderr is not None

    def _drain_stderr() -> None:
        assert proc.stderr is not None
        for line in proc.stderr:
            stderr_ring.append(line)

    threading.Thread(target=_drain_stderr, daemon=True).start()

    try:
        init_req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "afo-core", "version": "0"},
            },
        }
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        _ = read_jsonrpc_with_timeout(expected_id=1)

        # MCP handshake requires a `notifications/initialized` notification after initialize.
        proc.stdin.write(
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            + "\n"
        )
        proc.stdin.flush()

        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": method,
            "params": params or {},
        }
        proc.stdin.write(json.dumps(req) + "\n")
        proc.stdin.flush()

        return read_jsonrpc_with_timeout(expected_id=2)
    except json.JSONDecodeError as e:
        raise MCPStdioError(f"invalid JSON-RPC response: {e}") from e
    except BrokenPipeError as e:
        raise MCPStdioError(
            "MCP server closed stdin unexpectedly "
            f"(command={cfg.command}, args={cfg.args}, stderr tail: {stderr_tail()})"
        ) from e
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=max(0.1, remaining()))
        except Exception:
            proc.kill()


def list_tools(server_name: str, *, repo_root: Path | None = None) -> list[str]:
    cfg = load_mcp_server_config(server_name, repo_root=repo_root)

    # Node-based MCP servers (npx) may need longer on first run.
    cmd = Path(cfg.command).name
    timeout = 180.0 if cmd == "npx" or cfg.command == "npx" else 20.0

    resp = _rpc_call(cfg, method="tools/list", timeout_sec=timeout)
    tools = resp.get("result", {}).get("tools", [])
    if not isinstance(tools, list):
        return []
    return [
        str(name) for t in tools if isinstance(t, dict) and isinstance((name := t.get("name")), str)
    ]


def call_tool(
    server_name: str,
    *,
    tool_name: str,
    arguments: dict[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    cfg = load_mcp_server_config(server_name, repo_root=repo_root)
    params = {"name": tool_name, "arguments": arguments or {}}

    cmd = Path(cfg.command).name
    timeout = 180.0 if cmd == "npx" or cfg.command == "npx" else 20.0

    return _rpc_call(cfg, method="tools/call", params=params, timeout_sec=timeout)
