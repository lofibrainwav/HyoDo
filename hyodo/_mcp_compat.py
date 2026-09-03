"""Compatibility layer across MCP Python SDK major versions.

The optional ``hyodo[mcp]`` extra must stay installable while the SDK's v1
(``mcp.server.fastmcp.FastMCP``) and v2 (``mcp.server.mcpserver.MCPServer``)
lines both exist. v1 takes host/port/json_response/streamable_http_path as
constructor options; v2 moved them into ``streamable_http_app()``. This module
picks the right class once per process and exposes small capability probes so
call sites never branch on version numbers.
"""

from __future__ import annotations

import inspect
from typing import Any

_V2Server: type[Any] | None
try:  # MCP SDK v2 (2026-07-28 protocol revision and later)
    from mcp.server import mcpserver as _v2_module  # pyright: ignore[reportAttributeAccessIssue]

    _V2Server = _v2_module.MCPServer
except ImportError:  # SDK v1: the symbol import fails before the module lookup
    _V2Server = None


def get_mcp_server_class() -> type[Any]:
    """Return the installed SDK's high-level server class."""
    if _V2Server is not None:
        return _V2Server
    # Reachable only when the v2 module is absent (SDK v1). Under a v2 install
    # this import is statically unresolvable, which is expected — ignore both
    # missing-module and unknown-symbol reports accordingly.
    from mcp.server.fastmcp import (
        FastMCP,  # pyright: ignore[reportMissingImports, reportAttributeAccessIssue]
    )

    return FastMCP


def constructor_accepts_transport_options() -> bool:
    """True when host/port/json_response belong in the constructor (SDK v1)."""
    params = inspect.signature(get_mcp_server_class().__init__).parameters
    return "host" in params and "json_response" in params


def http_app_accepts_options() -> bool:
    """True when streamable_http_app() takes json_response/streamable_http_path (v2)."""
    params = inspect.signature(get_mcp_server_class().streamable_http_app).parameters
    return "json_response" in params


# Both majors expose the same decorator/driver surface HyoDo uses (tool(),
# run(transport=...), streamable_http_app()); only option placement differs.
MCPServerLike = Any
