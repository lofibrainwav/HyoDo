"""Optional local stdio MCP adapter for the public HyoDo CLI.

The adapter intentionally owns no gate or policy logic.  Every tool delegates
to the installed HyoDo Typer CLI in a child process and returns its observable
exit contract.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from secrets import compare_digest
from typing import Any

from mcp.server.fastmcp import FastMCP  # pyright: ignore[reportMissingImports]

_CLI_TIMEOUT_SECONDS = 120
_LOOPBACK_HOST = "127.0.0.1"
_MCP_PATH = "/mcp"


def resolve_workspace_root(root: Path) -> Path:
    """Return one existing workspace directory for the lifetime of the server."""
    resolved = root.expanduser().resolve()
    if not resolved.is_dir():
        raise ValueError(f"workspace root is not a directory: {resolved}")
    return resolved


def _resolve_workspace_path(root: Path, value: str) -> Path:
    """Resolve a relative path without allowing it to escape the locked workspace."""
    candidate = Path(value)
    if candidate.is_absolute():
        raise ValueError("path must be relative to the locked workspace")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes the locked workspace") from exc
    return resolved


def _run_cli(
    root: Path,
    args: list[str],
    *,
    stdin: str | None = None,
) -> dict[str, Any]:
    """Run the HyoDo CLI SSOT and serialize its observable result."""
    command = [sys.executable, "-m", "hyodo.cli.main", *args]
    try:
        process = subprocess.run(
            command,
            cwd=root,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=_CLI_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": "",
            "error": f"timeout after {_CLI_TIMEOUT_SECONDS}s",
        }
    except OSError as exc:
        return {
            "exit_code": 2,
            "stdout": "",
            "stderr": "",
            "error": f"cli_unavailable: {exc}",
        }
    return {
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def _run_git(root: Path, *args: str) -> tuple[bool, str]:
    """Read a small git fact without treating an unavailable repository as green."""
    try:
        process = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    return process.returncode == 0, process.stdout


def create_server(
    root: Path,
    *,
    host: str = _LOOPBACK_HOST,
    port: int = 8000,
) -> FastMCP:
    """Create one root-locked MCP server without owning gate logic."""
    workspace = resolve_workspace_root(root)
    server = FastMCP(
        "HyoDo",
        instructions=(
            "Local HyoDo CLI adapter. Tools act only on the configured host workspace; "
            "review signals never authorize approval."
        ),
        json_response=True,
        host=host,
        port=port,
        streamable_http_path=_MCP_PATH,
    )

    @server.tool()
    def get_local_context() -> dict[str, Any]:
        """Read the configured host workspace root and small git context."""
        status_ok, status = _run_git(workspace, "status", "--short")
        diff_ok, diff = _run_git(workspace, "diff", "--stat")
        return {
            "exit_code": 0,
            "root": str(workspace),
            "git_status": status.splitlines() if status_ok else [],
            "git_diff_stat": diff.strip() if diff_ok else "",
            "git_observed": status_ok and diff_ok,
        }

    @server.tool()
    def hyodo_safe() -> dict[str, Any]:
        """Run ``hyodo safe --json`` against the configured host workspace."""
        return _run_cli(workspace, ["safe", "--json", str(workspace)])

    @server.tool()
    def hyodo_check() -> dict[str, Any]:
        """Run ``hyodo check`` against the configured host workspace."""
        return _run_cli(workspace, ["check", str(workspace)])

    @server.tool()
    def hyodo_event_record(
        event: dict[str, Any],
        policy_path: str | None = None,
        full_body: bool = False,
    ) -> dict[str, Any]:
        """Record one event through ``hyodo event record`` using digest-only storage by default."""
        args = ["event", "record", "--stdin", "--root", str(workspace), "--json"]
        if policy_path is not None:
            try:
                args.extend(["--policy", str(_resolve_workspace_path(workspace, policy_path))])
            except ValueError as exc:
                return {"exit_code": 2, "stdout": "", "stderr": "", "error": str(exc)}
        if full_body:
            args.append("--full-body")
        return _run_cli(workspace, args, stdin=json.dumps(event))

    @server.tool()
    def hyodo_policy_check(
        event: dict[str, Any], policy_path: str = ".hyodo/policy.toml"
    ) -> dict[str, Any]:
        """Evaluate one event through ``hyodo policy check`` within the locked workspace."""
        try:
            config = _resolve_workspace_path(workspace, policy_path)
        except ValueError as exc:
            return {"exit_code": 2, "stdout": "", "stderr": "", "error": str(exc)}
        return _run_cli(
            workspace,
            ["policy", "check", "--stdin", "--config", str(config), "--json"],
            stdin=json.dumps(event),
        )

    return server


def run_stdio(root: Path) -> None:
    """Start the M1 local stdio transport. No network listener is created."""
    create_server(root).run(transport="stdio")


class _BearerTokenMiddleware:
    """Reject unauthenticated HTTP requests before the MCP SDK dispatches tools."""

    def __init__(self, app: Any, token: str):
        self.app = app
        self.token = token

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            supplied = headers.get(b"authorization", b"").decode("latin-1")
            if not compare_digest(supplied, f"Bearer {self.token}"):
                await send(
                    {
                        "type": "http.response.start",
                        "status": 401,
                        "headers": [(b"content-length", b"0")],
                    }
                )
                await send({"type": "http.response.body", "body": b""})
                return
        await self.app(scope, receive, send)


def _create_http_app(root: Path, host: str, token: str | None, *, port: int) -> Any:
    """Build one authenticated streamable-HTTP MCP app for a validated host."""
    app: Any = create_server(root, host=host, port=port).streamable_http_app()
    return _BearerTokenMiddleware(app, token) if token else app


def create_loopback_app(root: Path, token: str | None = None, *, port: int = 8769) -> Any:
    """Build the official streamable-HTTP MCP app for one loopback workspace."""
    return _create_http_app(root, _LOOPBACK_HOST, token, port=port)


def run_loopback(root: Path, *, port: int, token: str | None) -> None:
    """Serve MCP streamable HTTP only on the local IPv4 loopback interface."""
    import uvicorn

    uvicorn.run(
        create_loopback_app(root, token, port=port),
        host=_LOOPBACK_HOST,
        port=port,
        log_level="warning",
    )


def run_tailscale(root: Path, *, host: str, port: int, token: str) -> None:
    """Serve authenticated MCP only on one caller-validated Tailscale address."""
    import uvicorn

    uvicorn.run(
        _create_http_app(root, host, token, port=port),
        host=host,
        port=port,
        log_level="warning",
    )
