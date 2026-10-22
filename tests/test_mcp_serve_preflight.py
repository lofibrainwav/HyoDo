"""MCP serve preflight must validate roots without opening a network listener."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.workspace_io import open_workspace_root


def test_serve_valid_root_closes_preflight_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The preflight descriptor is released before the transport owns its root."""
    descriptors: list[int] = []
    calls: list[Path] = []

    def observe_root(root: Path) -> tuple[Path, int]:
        pinned, fd = open_workspace_root(root)
        descriptors.append(fd)
        return pinned, fd

    def fake_loopback(root: Path, **kwargs: object) -> None:
        calls.append(root)
        assert len(descriptors) == 1
        with pytest.raises(OSError, match="Bad file descriptor"):
            os.fstat(descriptors[0])

    monkeypatch.setattr("hyodo._mcp_compat.get_mcp_server_class", lambda: object)
    monkeypatch.setattr("hyodo.workspace_io.open_workspace_root", observe_root)
    monkeypatch.setattr("hyodo.mcp_server.run_loopback", fake_loopback)
    result = CliRunner().invoke(app, ["mcp", "serve", "--root", str(tmp_path), "--port", "8769"])
    assert result.exit_code == 0, result.output
    assert calls == [tmp_path]


@pytest.mark.parametrize("linked", [False, True])
def test_serve_invalid_root_never_announces_ready_or_calls_transport(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, linked: bool
) -> None:
    """Missing roots and outward root links fail before any transport call."""
    root = tmp_path / "root"
    if linked:
        outside = tmp_path / "outside"
        outside.mkdir()
        root.symlink_to(outside, target_is_directory=True)
    calls: list[Path] = []
    monkeypatch.setattr("hyodo._mcp_compat.get_mcp_server_class", lambda: object)
    monkeypatch.setattr("hyodo.mcp_server.run_loopback", lambda root, **kwargs: calls.append(root))
    result = CliRunner().invoke(app, ["mcp", "serve", "--root", str(root), "--port", "8769"])
    assert result.exit_code == 2
    assert calls == []
    assert "connector ready" not in result.output
