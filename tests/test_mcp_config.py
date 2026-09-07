"""Tests for ``hyodo mcp config``: snippet shape per host, platform path
resolution, dry run vs. ``--write`` (merge, ``.bak``, idempotency), the
``chatgpt`` UNOBSERVED contract, and the documented VS Code/Cursor deep
links. No bearer token or secret ever appears in any output here — the
stdio adapter needs none.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.mcp_config import (
    ALL_HOSTS,
    CHATGPT_UNOBSERVED_MESSAGE,
    MCP_HOSTS,
    build_server_entry,
    build_vscode_server_entry,
    cursor_deep_link,
    detect_hosts,
    host_target,
    plan_host,
    resolve_claude_desktop_path,
    stdio_args,
    vscode_deep_link,
    write_host,
)

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolated_environment(tmp_path: Path, monkeypatch) -> None:
    """Every test here is hermetic: never touch the real machine's home
    directory (``claude-desktop``/``codex`` targets live under ``$HOME``),
    and never let Rich's terminal-width line-wrapping split a long path or
    label across a substring assertion.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir(exist_ok=True)
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv("COLUMNS", "1000")


def _dir_digest(root: Path) -> str:
    """Hash every file under *root* (path + content) to prove a dry run wrote nothing."""
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            hasher.update(str(path.relative_to(root)).encode("utf-8"))
            hasher.update(path.read_bytes())
    return hasher.hexdigest()


# --------------------------------------------------------------------------
# stdio args / server entry shape
# --------------------------------------------------------------------------


def test_stdio_args_use_absolute_root(tmp_path: Path) -> None:
    args = stdio_args(tmp_path)
    assert args == ["mcp", "stdio", "--root", str(tmp_path)]
    assert Path(args[-1]).is_absolute()


def test_build_server_entry_has_no_token_field(tmp_path: Path) -> None:
    entry = build_server_entry(tmp_path)
    assert entry == {"command": "hyodo", "args": ["mcp", "stdio", "--root", str(tmp_path)]}
    assert "token" not in json.dumps(entry).lower()


def test_build_vscode_server_entry_adds_type_stdio(tmp_path: Path) -> None:
    entry = build_vscode_server_entry(tmp_path)
    assert entry["type"] == "stdio"
    assert entry["command"] == "hyodo"


# --------------------------------------------------------------------------
# Host -> file target resolution
# --------------------------------------------------------------------------


def test_claude_code_target_is_root_mcp_json(tmp_path: Path) -> None:
    target = host_target("claude-code", tmp_path)
    assert target.path == tmp_path / ".mcp.json"
    assert target.key_path == ("mcpServers", "hyodo")
    assert target.verified is True


def test_cursor_target_is_dot_cursor_mcp_json(tmp_path: Path) -> None:
    target = host_target("cursor", tmp_path)
    assert target.path == tmp_path / ".cursor" / "mcp.json"
    assert target.key_path == ("mcpServers", "hyodo")


def test_vscode_target_uses_servers_key(tmp_path: Path) -> None:
    target = host_target("vscode", tmp_path)
    assert target.path == tmp_path / ".vscode" / "mcp.json"
    assert target.key_path == ("servers", "hyodo")


def test_codex_target_is_home_codex_config_toml_and_unverified(tmp_path: Path) -> None:
    target = host_target("codex", tmp_path, home=tmp_path)
    assert target.path == tmp_path / ".codex" / "config.toml"
    assert target.key_path == ("mcp_servers", "hyodo")
    assert target.entry_format == "toml"
    assert target.verified is False


def test_claude_desktop_path_macos(tmp_path: Path) -> None:
    path = resolve_claude_desktop_path("darwin", tmp_path, None)
    assert (
        path
        == tmp_path / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    )


def test_claude_desktop_path_windows_with_appdata(tmp_path: Path) -> None:
    appdata = str(tmp_path / "AppData" / "Roaming")
    path = resolve_claude_desktop_path("win32", tmp_path, appdata)
    assert path == Path(appdata) / "Claude" / "claude_desktop_config.json"


def test_claude_desktop_path_windows_without_appdata_falls_back(tmp_path: Path) -> None:
    path = resolve_claude_desktop_path("win32", tmp_path, None)
    assert path == tmp_path / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"


def test_claude_desktop_path_linux_documented_convention(tmp_path: Path) -> None:
    path = resolve_claude_desktop_path("linux", tmp_path, None)
    assert path == tmp_path / ".config" / "Claude" / "claude_desktop_config.json"


def test_detect_hosts_reports_presence_not_content(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".codex").mkdir()  # acting as "home" below
    detected = detect_hosts(tmp_path, home=tmp_path, platform="linux")
    assert detected["cursor"] is True
    assert detected["vscode"] is False
    assert detected["codex"] is True


# --------------------------------------------------------------------------
# Dry run: prints, writes nothing
# --------------------------------------------------------------------------


def test_dry_run_writes_nothing_for_every_writable_host(tmp_path: Path) -> None:
    before = _dir_digest(tmp_path)
    for host in MCP_HOSTS:
        result = runner.invoke(app, ["mcp", "config", host, "--root", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert str(tmp_path) in result.output
    assert _dir_digest(tmp_path) == before


def test_dry_run_json_reports_would_write_and_content(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "cursor", "--root", str(tmp_path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["status"] == "would_write"
    assert payload["write"] is False
    assert payload["existed_before"] is False
    settings = json.loads(payload["content"])
    assert settings["mcpServers"]["hyodo"]["command"] == "hyodo"
    assert not (tmp_path / ".cursor").exists()


# --------------------------------------------------------------------------
# --write: merge, .bak, idempotency
# --------------------------------------------------------------------------


def test_write_creates_claude_code_mcp_json(tmp_path: Path) -> None:
    result = runner.invoke(
        app, ["mcp", "config", "claude-code", "--root", str(tmp_path), "--write"]
    )
    assert result.exit_code == 0, result.output
    written = json.loads((tmp_path / ".mcp.json").read_text(encoding="utf-8"))
    assert written["mcpServers"]["hyodo"]["args"][-1] == str(tmp_path)


def test_write_merge_keeps_foreign_server_and_creates_bak(tmp_path: Path) -> None:
    cursor_dir = tmp_path / ".cursor"
    cursor_dir.mkdir()
    foreign = {"mcpServers": {"other-tool": {"command": "other", "args": []}}}
    config_path = cursor_dir / "mcp.json"
    config_path.write_text(json.dumps(foreign), encoding="utf-8")

    result = runner.invoke(app, ["mcp", "config", "cursor", "--root", str(tmp_path), "--write"])
    assert result.exit_code == 0, result.output

    merged = json.loads(config_path.read_text(encoding="utf-8"))
    assert merged["mcpServers"]["other-tool"] == {"command": "other", "args": []}
    assert merged["mcpServers"]["hyodo"]["command"] == "hyodo"

    backup_path = cursor_dir / "mcp.json.bak"
    assert backup_path.is_file()
    assert json.loads(backup_path.read_text(encoding="utf-8")) == foreign


def test_write_twice_is_idempotent_no_second_backup(tmp_path: Path) -> None:
    cursor_dir = tmp_path / ".cursor"
    cursor_dir.mkdir()
    foreign = {"mcpServers": {"other-tool": {"command": "other", "args": []}}}
    config_path = cursor_dir / "mcp.json"
    config_path.write_text(json.dumps(foreign), encoding="utf-8")

    runner.invoke(app, ["mcp", "config", "cursor", "--root", str(tmp_path), "--write"])
    backup_path = cursor_dir / "mcp.json.bak"
    first_backup_mtime = backup_path.stat().st_mtime_ns
    content_after_first_write = config_path.read_text(encoding="utf-8")

    second = runner.invoke(app, ["mcp", "config", "cursor", "--root", str(tmp_path), "--write"])
    assert second.exit_code == 0, second.output

    assert config_path.read_text(encoding="utf-8") == content_after_first_write
    assert backup_path.stat().st_mtime_ns == first_backup_mtime  # not re-backed-up


def test_codex_toml_merge_preserves_unrelated_content(tmp_path: Path) -> None:
    codex_dir = tmp_path / ".codex"
    codex_dir.mkdir()
    config_path = codex_dir / "config.toml"
    config_path.write_text('[some_other_table]\nfoo = "bar"\n', encoding="utf-8")

    plan = write_host("codex", tmp_path, home=tmp_path)
    assert plan.status == "would_write"
    written = config_path.read_text(encoding="utf-8")
    assert 'foo = "bar"' in written
    assert "[mcp_servers.hyodo]" in written
    assert str(tmp_path) in written

    backup_path = codex_dir / "config.toml.bak"
    assert backup_path.is_file()

    # Second write: idempotent, no new backup, content unchanged.
    before_mtime = backup_path.stat().st_mtime_ns
    plan2 = write_host("codex", tmp_path, home=tmp_path)
    assert plan2.status == "up_to_date"
    assert backup_path.stat().st_mtime_ns == before_mtime


# --------------------------------------------------------------------------
# chatgpt: always UNOBSERVED
# --------------------------------------------------------------------------


def test_chatgpt_host_exits_two_unobserved(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "chatgpt", "--root", str(tmp_path)])
    assert result.exit_code == 2, result.output
    assert "UNOBSERVED" in result.output


def test_chatgpt_host_write_still_exits_two_and_writes_nothing(tmp_path: Path) -> None:
    before = _dir_digest(tmp_path)
    result = runner.invoke(app, ["mcp", "config", "chatgpt", "--root", str(tmp_path), "--write"])
    assert result.exit_code == 2, result.output
    assert _dir_digest(tmp_path) == before


def test_chatgpt_json_payload_carries_m5_contract_message(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "chatgpt", "--root", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["exit_code"] == 2
    assert payload["ok"] is False
    assert payload["message"] == CHATGPT_UNOBSERVED_MESSAGE
    assert "mcp.hyodo.app" in payload["message"]


def test_unknown_host_exits_two(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "not-a-real-host", "--root", str(tmp_path)])
    assert result.exit_code == 2, result.output


def test_all_hosts_constant_is_mcp_hosts_plus_chatgpt() -> None:
    assert set(ALL_HOSTS) == set(MCP_HOSTS) | {"chatgpt"}


# --------------------------------------------------------------------------
# codex: documented, unverified format
# --------------------------------------------------------------------------


def test_codex_dry_run_preview_keeps_the_toml_table_header(tmp_path: Path) -> None:
    """Regression: Rich treats a bare ``[...]`` line as markup and silently
    strips it unless the preview print disables markup - a TOML table header
    like ``[mcp_servers.hyodo]`` must survive the printed preview verbatim.
    """
    result = runner.invoke(app, ["mcp", "config", "codex", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "[mcp_servers.hyodo]" in result.output


def test_codex_dry_run_labels_unverified(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "codex", "--root", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "not verified against a live install" in result.output


def test_codex_json_reports_verified_false(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "codex", "--root", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["verified"] is False


def test_claude_code_json_reports_verified_true(tmp_path: Path) -> None:
    result = runner.invoke(app, ["mcp", "config", "claude-code", "--root", str(tmp_path), "--json"])
    payload = json.loads(result.output)
    assert payload["verified"] is True


# --------------------------------------------------------------------------
# Deep links: documented, decode back to the same config
# --------------------------------------------------------------------------


def test_vscode_deep_link_decodes_to_same_config(tmp_path: Path) -> None:
    link = vscode_deep_link(tmp_path)
    assert link.startswith("vscode:mcp/install?")
    query = unquote(link.split("?", 1)[1])
    decoded = json.loads(query)
    assert decoded["name"] == "hyodo"
    assert decoded["command"] == "hyodo"
    assert decoded["args"] == stdio_args(tmp_path)


def test_cursor_deep_link_decodes_to_same_config(tmp_path: Path) -> None:
    link = cursor_deep_link(tmp_path)
    assert link.startswith("cursor://anysphere.cursor-deeplink/mcp/install?")
    parsed = urlsplit(link)
    params = parse_qs(parsed.query)
    assert params["name"] == ["hyodo"]
    decoded = json.loads(base64.b64decode(params["config"][0]).decode("utf-8"))
    assert decoded == build_server_entry(tmp_path)


def test_cli_prints_deep_links_for_vscode_and_cursor(tmp_path: Path) -> None:
    for host in ("vscode", "cursor"):
        result = runner.invoke(app, ["mcp", "config", host, "--root", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "deep link" in result.output
        assert "not verified against a live install" in result.output


def test_cli_json_includes_deep_links_for_vscode_and_cursor(tmp_path: Path) -> None:
    for host in ("vscode", "cursor"):
        result = runner.invoke(app, ["mcp", "config", host, "--root", str(tmp_path), "--json"])
        payload = json.loads(result.output)
        assert host in payload["deep_links"]


def test_no_deep_link_for_claude_code_or_codex(tmp_path: Path) -> None:
    for host in ("claude-code", "codex"):
        result = runner.invoke(app, ["mcp", "config", host, "--root", str(tmp_path), "--json"])
        payload = json.loads(result.output)
        assert "deep_links" not in payload


# --------------------------------------------------------------------------
# No secret ever appears
# --------------------------------------------------------------------------


def test_no_token_or_secret_substring_in_any_host_output(tmp_path: Path) -> None:
    forbidden = ("bearer", "hyodo_mcp_token", "authorization")
    for host in MCP_HOSTS:
        for extra in ([], ["--json"]):
            result = runner.invoke(app, ["mcp", "config", host, "--root", str(tmp_path), *extra])
            lowered = result.output.lower()
            for word in forbidden:
                assert word not in lowered, f"{host} {extra}: unexpected {word!r} in output"


def test_plan_host_and_write_host_agree_on_content(tmp_path: Path) -> None:
    for host in MCP_HOSTS:
        planned = plan_host(host, tmp_path, home=tmp_path)
        assert planned.status == "would_write"
        written = write_host(host, tmp_path, home=tmp_path)
        assert written.content == planned.content
