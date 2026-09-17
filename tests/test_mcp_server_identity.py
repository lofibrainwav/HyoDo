"""The MCP adapter must tell a client which HyoDo it is.

Observed 2026-09-16: under MCP SDK v2 the adapter advertised
``serverInfo.version: ""``. The v2 constructor accepts ``version`` and defaults
it to the empty string, and HyoDo never passed one. Under v1 the same field
carried the SDK's own version (for example ``1.28.1``), which is honest about
the transport but says nothing about the adapter. Neither major reported
HyoDo's version, so a client could not distinguish a current adapter from a
stale one.

These tests pin the call site, not the SDK: a constructor that accepts a
version receives HyoDo's, and one that does not is still constructed cleanly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

from hyodo import __version__
from hyodo.mcp_server import create_server


class _V1StyleServer:
    """Stand-in for SDK v1 ``FastMCP``: transport options, no ``version``."""

    built: ClassVar[list[_V1StyleServer]] = []

    def __init__(
        self,
        name: str,
        *,
        instructions: str | None = None,
        host: str | None = None,
        port: int | None = None,
        json_response: bool | None = None,
        streamable_http_path: str | None = None,
        **extra: Any,
    ) -> None:
        self.name = name
        self.instructions = instructions
        self.extra = extra
        _V1StyleServer.built.append(self)

    def tool(self) -> Any:
        """Return a decorator that registers a tool without altering it."""

        def decorator(func: Any) -> Any:
            return func

        return decorator


class _V2StyleServer:
    """Stand-in for SDK v2 ``MCPServer``: takes ``version``, defaults to ""."""

    built: ClassVar[list[_V2StyleServer]] = []

    def __init__(
        self,
        name: str,
        *,
        instructions: str | None = None,
        version: str = "",
        **extra: Any,
    ) -> None:
        self.name = name
        self.instructions = instructions
        self.version = version
        self.extra = extra
        _V2StyleServer.built.append(self)

    def tool(self) -> Any:
        """Return a decorator that registers a tool without altering it."""

        def decorator(func: Any) -> Any:
            return func

        return decorator


def _install(monkeypatch: Any, server_class: Any) -> list[Any]:
    """Route both lookup sites at *server_class* and reset its record.

    The class is installed as-is rather than wrapped: the probe reads
    ``__init__``'s signature, and a ``*args, **kwargs`` subclass would erase
    exactly the parameter under test.
    """
    server_class.built.clear()
    monkeypatch.setattr("hyodo._mcp_compat.get_mcp_server_class", lambda: server_class)
    monkeypatch.setattr("hyodo.mcp_server.get_mcp_server_class", lambda: server_class)
    return server_class.built


def test_v2_constructor_receives_hyodo_version(monkeypatch: Any, tmp_path: Path) -> None:
    """A v2-style constructor is given HyoDo's version, not the empty default."""
    built = _install(monkeypatch, _V2StyleServer)

    create_server(tmp_path)

    assert len(built) == 1
    assert built[0].version == __version__
    assert built[0].version != ""


def test_v1_constructor_is_not_given_a_version(monkeypatch: Any, tmp_path: Path) -> None:
    """A v1-style constructor has no ``version``; passing one would raise."""
    built = _install(monkeypatch, _V1StyleServer)

    create_server(tmp_path)

    assert len(built) == 1
    assert "version" not in built[0].extra


def test_version_probe_matches_the_constructor(monkeypatch: Any, tmp_path: Path) -> None:
    """The probe answers from the signature that will actually be called."""
    from hyodo._mcp_compat import constructor_accepts_version

    _install(monkeypatch, _V2StyleServer)
    assert constructor_accepts_version() is True

    _install(monkeypatch, _V1StyleServer)
    assert constructor_accepts_version() is False
