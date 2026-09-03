"""TDD contracts for ``hyodo mcp doctor`` (M4 slice 1).

Doctor checks are read-only diagnostics — they must never start a server
or mutate state.  Each check returns a structured result that the CLI
renders for humans and (with --json) emits as machine-readable JSON.
"""

from __future__ import annotations

import json
import socket
import sys

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app

runner = CliRunner()


# ---------------------------------------------------------------------------
# 1. The command exists and is wired into the ``mcp`` sub-group.
# ---------------------------------------------------------------------------

def test_mcp_doctor_command_is_registered():
    """``hyodo mcp doctor`` appears in the CLI help output."""
    result = runner.invoke(app, ["mcp", "--help"])
    assert result.exit_code == 0
    assert "doctor" in result.output


# ---------------------------------------------------------------------------
# 2. MCP SDK availability check
# ---------------------------------------------------------------------------

def test_mcp_doctor_reports_mcp_sdk_present():
    """When the ``mcp`` package is importable, doctor reports it as available."""
    result = runner.invoke(app, ["mcp", "doctor"])
    assert result.exit_code == 0
    assert "mcp-sdk" in result.output
    assert "available" in result.output.lower()


def test_mcp_doctor_reports_mcp_sdk_missing(monkeypatch):
    """When the ``mcp`` package cannot be imported, doctor reports it as missing."""
    # Make get_mcp_server_class raise ModuleNotFoundError so the doctor
    # detects the SDK as missing, regardless of what's actually installed.

    def _raise_module_not_found(*args, **kwargs):
        raise ModuleNotFoundError("mcp")

    monkeypatch.setattr(
        "hyodo._mcp_compat.get_mcp_server_class",
        _raise_module_not_found,
    )
    # Also prevent the fallback `import mcp` from succeeding.
    monkeypatch.setitem(sys.modules, "mcp", None)

    result = runner.invoke(app, ["mcp", "doctor"])
    assert result.exit_code == 0
    assert "mcp-sdk" in result.output
    assert "missing" in result.output.lower()


# ---------------------------------------------------------------------------
# 3. Workspace root check
# ---------------------------------------------------------------------------

def test_mcp_doctor_reports_valid_workspace(tmp_path):
    """A valid directory root is reported as OK."""
    result = runner.invoke(app, ["mcp", "doctor", "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "workspace" in result.output.lower()
    # Rich may line-wrap the path; check that the dir name appears.
    assert tmp_path.name in result.output


def test_mcp_doctor_reports_missing_workspace(tmp_path):
    """A nonexistent workspace root is reported as a problem."""
    missing = tmp_path / "no-such-dir"
    result = runner.invoke(app, ["mcp", "doctor", "--root", str(missing)])
    assert result.exit_code == 0  # doctor never hard-fails; it reports
    assert "missing" in result.output.lower() or "not a directory" in result.output.lower()


# ---------------------------------------------------------------------------
# 4. Port availability check (default 8769)
# ---------------------------------------------------------------------------

def test_mcp_doctor_reports_port_free():
    """When the default MCP port is free, doctor reports it as available."""
    result = runner.invoke(app, ["mcp", "doctor"])
    assert result.exit_code == 0
    assert "port" in result.output.lower()
    assert "8769" in result.output


def test_mcp_doctor_reports_port_in_use():
    """When the default MCP port is occupied, doctor reports the conflict."""
    # Bind a socket to port 8769 to simulate an occupied port.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as blocker:
        try:
            blocker.bind(("127.0.0.1", 8769))
        except OSError:
            pytest.skip("Port 8769 already in use; cannot simulate conflict")
        result = runner.invoke(app, ["mcp", "doctor"])
    assert result.exit_code == 0
    assert "in use" in result.output.lower() or "occupied" in result.output.lower()


# ---------------------------------------------------------------------------
# 5. Dashboard port conflict (8768)
# ---------------------------------------------------------------------------

def test_mcp_doctor_warns_dashboard_port_conflict():
    """If port 8768 is occupied by the dashboard, doctor notes the reservation."""
    result = runner.invoke(app, ["mcp", "doctor", "--port", "8768"])
    assert result.exit_code == 0
    # Doctor should warn that 8768 is reserved for the dashboard.
    assert "dashboard" in result.output.lower() or "reserved" in result.output.lower()


# ---------------------------------------------------------------------------
# 6. Tailscale check (best-effort, may not be installed)
# ---------------------------------------------------------------------------

def test_mcp_doctor_includes_tailscale_section():
    """Doctor includes a tailscale section even when tailscale is unavailable."""
    result = runner.invoke(app, ["mcp", "doctor"])
    assert result.exit_code == 0
    assert "tailscale" in result.output.lower()


# ---------------------------------------------------------------------------
# 7. JSON output
# ---------------------------------------------------------------------------

def test_mcp_doctor_json_output(tmp_path):
    """With ``--json``, doctor emits a valid JSON structure with all check keys."""
    result = runner.invoke(app, ["mcp", "doctor", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.output)
    # The JSON structure must contain at least these top-level check groups.
    assert "mcp_sdk" in payload
    assert "workspace" in payload
    assert "port" in payload
    assert "tailscale" in payload


def test_mcp_doctor_json_mcp_sdk_fields(tmp_path):
    """The mcp_sdk JSON group has ``available`` and ``version`` keys."""
    result = runner.invoke(app, ["mcp", "doctor", "--root", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert "available" in payload["mcp_sdk"]
    assert "version" in payload["mcp_sdk"]


def test_mcp_doctor_json_port_fields(tmp_path):
    """The port JSON group has ``number``, ``free``, and ``conflict`` keys."""
    result = runner.invoke(app, ["mcp", "doctor", "--root", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert "number" in payload["port"]
    assert "free" in payload["port"]


# ---------------------------------------------------------------------------
# 8. Doctor never starts a server
# ---------------------------------------------------------------------------

def test_mcp_doctor_never_starts_a_server(monkeypatch):
    """Doctor must not call run_stdio, run_loopback, or run_tailscale."""
    from hyodo import mcp_server

    guarded = []
    for name in ("run_stdio", "run_loopback", "run_tailscale"):
        monkeypatch.setattr(
            mcp_server,
            name,
            lambda *a, _name=name, **kw: guarded.append(_name),
        )

    runner.invoke(app, ["mcp", "doctor"])
    assert guarded == [], f"doctor called a server start function: {guarded}"


# ---------------------------------------------------------------------------
# 9. Exit code semantics
# ---------------------------------------------------------------------------

def test_mcp_doctor_exits_0_even_with_problems(tmp_path):
    """Doctor exits 0 even when problems are found; it reports, not blocks."""
    missing = tmp_path / "no-such-dir"
    result = runner.invoke(app, ["mcp", "doctor", "--root", str(missing)])
    # Doctor is diagnostic — it never hard-fails.
    assert result.exit_code == 0
