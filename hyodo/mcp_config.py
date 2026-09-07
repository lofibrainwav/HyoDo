"""``hyodo mcp config`` — print (or write) the MCP client configuration that
registers HyoDo's local stdio adapter (``hyodo mcp stdio --root <root>``) for
one host.

Mirrors ``hyodo/connect.py``'s shape: a pure "what would be written" planner
(:func:`plan_host`) that dry-run and ``--write`` both call, so the two paths
can never drift. Every host uses the same underlying server entry
(:func:`build_server_entry`) — command ``hyodo``, args
``mcp stdio --root <absolute root>`` — no bearer token, no secret, ever.

Hosts and files:

- ``claude-code``    -> ``<root>/.mcp.json``                (``mcpServers.hyodo``)
- ``claude-desktop``  -> platform-specific (see
  :func:`resolve_claude_desktop_path`)                       (``mcpServers.hyodo``)
- ``cursor``          -> ``<root>/.cursor/mcp.json``          (``mcpServers.hyodo``)
- ``vscode``          -> ``<root>/.vscode/mcp.json``          (``servers.hyodo``, VS Code's shape)
- ``codex``           -> ``~/.codex/config.toml``             (``[mcp_servers.hyodo]`` table)
- ``chatgpt``         -> always ``UNOBSERVED`` (remote connector is not live; see
  ``docs/M5_REMOTE_CONNECTOR_CONTRACT.md``)

``codex``'s TOML table format is documented, not verified against a live
install — the same caution ``hyodo connect`` applies to the cursor/codex hook
contracts. JSON files are merged key-level (existing servers/keys preserved);
the TOML file is merged with a marked block, the same technique
``hyodo/connect.py`` uses for ``.pre-commit-config.yaml``. A file HyoDo did
not create itself gets a ``.bak`` alongside it on its first write; once the
``hyodo`` entry exists, later writes update it in place without another
backup (idempotent).
"""

from __future__ import annotations

import base64
import json
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

from hyodo.connector_contract import REMOTE_CONNECTOR_URL

#: Hosts that get a real, generated MCP client config.
MCP_HOSTS: tuple[str, ...] = ("claude-code", "claude-desktop", "cursor", "vscode", "codex")
#: Hosts this command always reports UNOBSERVED for (no live remote connector).
UNOBSERVED_HOSTS: tuple[str, ...] = ("chatgpt",)
ALL_HOSTS: tuple[str, ...] = MCP_HOSTS + UNOBSERVED_HOSTS

#: Hosts whose config format is documented but not verified against a live
#: install — mirrors ``hyodo/connect.py``'s UNOBSERVED_TARGETS caution for
#: cursor/codex hooks, applied here to codex's MCP table format.
UNVERIFIED_HOSTS: tuple[str, ...] = ("codex",)

#: Hosts with a documented one-click deep link (text only — never claimed
#: tested against a live install).
DEEP_LINK_HOSTS: tuple[str, ...] = ("vscode", "cursor")

DEEP_LINK_LABEL = "generated from the documented URL scheme, not verified against a live install"
UNVERIFIED_FORMAT_LABEL = "documented format, not verified against a live install"

CHATGPT_UNOBSERVED_MESSAGE = (
    f"remote connector ({REMOTE_CONNECTOR_URL}) is not live — UNOBSERVED, "
    "nothing written. See `hyodo mcp contract`."
)
UNKNOWN_HOST_MESSAGE_PREFIX = "unknown host"

STDIO_COMMAND = "hyodo"
_STDIO_ARGS_PREFIX = ("mcp", "stdio", "--root")

_TOML_MARKER_BEGIN = "# hyodo:mcp-config:begin"
_TOML_MARKER_END = "# hyodo:mcp-config:end"


def stdio_args(root: Path) -> list[str]:
    """Return the stdio adapter's argv tail for *root* (always an absolute path)."""
    return [*_STDIO_ARGS_PREFIX, str(root)]


def build_server_entry(root: Path) -> dict[str, Any]:
    """The server entry shared by claude-code/claude-desktop/cursor (``mcpServers``)."""
    return {"command": STDIO_COMMAND, "args": stdio_args(root)}


def build_vscode_server_entry(root: Path) -> dict[str, Any]:
    """VS Code's shape adds an explicit ``"type": "stdio"`` field."""
    return {"type": "stdio", "command": STDIO_COMMAND, "args": stdio_args(root)}


# --------------------------------------------------------------------------
# Host -> file target resolution
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class HostTarget:
    """Where a host's config lives and how HyoDo's entry is keyed inside it."""

    host: str
    path: Path
    key_path: tuple[str, str]
    entry_format: str  # "json" | "toml"
    verified: bool


def resolve_claude_desktop_path(platform: str, home: Path, appdata: str | None) -> Path:
    """Resolve Claude Desktop's config path for *platform* (``sys.platform`` value).

    macOS: ``~/Library/Application Support/Claude/claude_desktop_config.json``.
    Windows: ``%APPDATA%\\Claude\\claude_desktop_config.json`` (falls back to
    ``<home>/AppData/Roaming`` if ``appdata`` is unset). Anything else: the
    documented Linux convention, ``~/.config/Claude/claude_desktop_config.json``
    — Claude Desktop is not officially shipped for Linux; this path is
    documented, not verified against a live install.
    """
    if platform.startswith("darwin"):
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if platform.startswith("win"):
        base = Path(appdata) if appdata else home / "AppData" / "Roaming"
        return base / "Claude" / "claude_desktop_config.json"
    return home / ".config" / "Claude" / "claude_desktop_config.json"


def detect_hosts(
    root: Path,
    *,
    platform: str | None = None,
    home: Path | None = None,
    appdata: str | None = None,
) -> dict[str, bool]:
    """Report which MCP hosts already look set up under *root* (never writes).

    "Detected" means the host's own directory (or, for ``claude-code``, its
    MCP config file) already exists — the same "presence, not content"
    signal ``hyodo/connect.py``'s ``detect()`` uses for ``.claude``. Used by
    ``hyodo start`` to narrow "connect which host now?" to hosts worth
    asking about.
    """
    if home is None:
        home = Path.home()
    claude_desktop_dir = host_target(
        "claude-desktop", root, platform=platform, home=home, appdata=appdata
    ).path.parent
    return {
        "claude-code": (root / ".claude").is_dir() or (root / ".mcp.json").is_file(),
        "claude-desktop": claude_desktop_dir.is_dir(),
        "cursor": (root / ".cursor").is_dir(),
        "vscode": (root / ".vscode").is_dir(),
        "codex": (home / ".codex").is_dir(),
    }


def host_target(
    host: str,
    root: Path,
    *,
    platform: str | None = None,
    home: Path | None = None,
    appdata: str | None = None,
) -> HostTarget:
    """Resolve *host*'s config file, key path, and format. ``root`` must be absolute.

    ``platform``/``home``/``appdata`` are injectable seams for tests
    (``claude-desktop`` is the only host whose path depends on them); real
    callers leave them ``None`` to read ``sys.platform``/``Path.home()``/
    ``os.environ["APPDATA"]``.
    """
    if platform is None:
        platform = sys.platform
    if home is None:
        home = Path.home()
    if host == "claude-code":
        return HostTarget(host, root / ".mcp.json", ("mcpServers", "hyodo"), "json", True)
    if host == "claude-desktop":
        if appdata is None:
            import os

            appdata = os.environ.get("APPDATA")
        path = resolve_claude_desktop_path(platform, home, appdata)
        return HostTarget(host, path, ("mcpServers", "hyodo"), "json", True)
    if host == "cursor":
        return HostTarget(
            host, root / ".cursor" / "mcp.json", ("mcpServers", "hyodo"), "json", True
        )
    if host == "vscode":
        return HostTarget(host, root / ".vscode" / "mcp.json", ("servers", "hyodo"), "json", True)
    if host == "codex":
        return HostTarget(
            host, home / ".codex" / "config.toml", ("mcp_servers", "hyodo"), "toml", False
        )
    raise ValueError(f"unknown host: {host}")


# --------------------------------------------------------------------------
# Content builders
# --------------------------------------------------------------------------


def _read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _read_json(path: Path) -> dict[str, Any] | None:
    text = _read_text(path)
    if text is None:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _json_already_owned(existing: dict[str, Any] | None, key_path: tuple[str, str]) -> bool:
    if not isinstance(existing, dict):
        return False
    section = existing.get(key_path[0])
    return isinstance(section, dict) and key_path[1] in section


def build_json_config(
    existing: dict[str, Any] | None, key_path: tuple[str, str], entry: dict[str, Any]
) -> dict[str, Any]:
    """Merge *entry* into ``existing[key_path[0]][key_path[1]]``, key-level.

    Every other top-level key and every other server already under
    ``key_path[0]`` is passed through unchanged.
    """
    config: dict[str, Any] = dict(existing) if isinstance(existing, dict) else {}
    top_key, leaf_key = key_path
    existing_section = config.get(top_key)
    section: dict[str, Any] = dict(existing_section) if isinstance(existing_section, dict) else {}
    section[leaf_key] = entry
    config[top_key] = section
    return config


def _toml_string(value: str) -> str:
    return json.dumps(value)  # TOML basic strings are a subset of JSON string escaping.


def _codex_toml_block(root: Path) -> str:
    args_toml = ", ".join(_toml_string(a) for a in stdio_args(root))
    return (
        f"{_TOML_MARKER_BEGIN}\n"
        "[mcp_servers.hyodo]\n"
        f"command = {_toml_string(STDIO_COMMAND)}\n"
        f"args = [{args_toml}]\n"
        f"{_TOML_MARKER_END}\n"
    )


def build_codex_config(existing_text: str | None, root: Path) -> str:
    """Return the full ``~/.codex/config.toml`` content, marker-merged.

    Same technique as ``hyodo/connect.py``'s ``.pre-commit-config.yaml``
    merge: only the text between the marker comments is ever replaced,
    everything else in the file is left byte-for-byte untouched.
    """
    block = _codex_toml_block(root)
    if existing_text is None:
        return block
    if _TOML_MARKER_BEGIN in existing_text and _TOML_MARKER_END in existing_text:
        start = existing_text.index(_TOML_MARKER_BEGIN)
        end = existing_text.index(_TOML_MARKER_END) + len(_TOML_MARKER_END)
        if end < len(existing_text) and existing_text[end] == "\n":
            end += 1
        return existing_text[:start] + block + existing_text[end:]
    separator = "" if existing_text == "" or existing_text.endswith("\n") else "\n"
    return existing_text + separator + block


def _toml_already_owned(existing_text: str | None) -> bool:
    return existing_text is not None and _TOML_MARKER_BEGIN in existing_text


# --------------------------------------------------------------------------
# Planning — dry run and --write share this.
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class HostPlan:
    """What ``mcp config <host>`` would do, or did."""

    host: str
    status: str  # "would_write" | "up_to_date" | "unobserved" | "unknown"
    message: str
    path: Path | None = None
    content: str = ""
    existed_before: bool = False
    will_change: bool = False
    needs_backup: bool = False
    verified: bool = True
    deep_links: dict[str, str] = field(default_factory=dict)


def plan_host(
    host: str,
    root: Path,
    *,
    platform: str | None = None,
    home: Path | None = None,
    appdata: str | None = None,
) -> HostPlan:
    """Compute what ``mcp config`` would do for *host*, writing nothing."""
    if host in UNOBSERVED_HOSTS:
        return HostPlan(host=host, status="unobserved", message=CHATGPT_UNOBSERVED_MESSAGE)
    if host not in MCP_HOSTS:
        message = f"{UNKNOWN_HOST_MESSAGE_PREFIX}: {host}. Known hosts: {', '.join(ALL_HOSTS)}"
        return HostPlan(host=host, status="unknown", message=message)

    target = host_target(host, root, platform=platform, home=home, appdata=appdata)
    deep_links = {name: _build_deep_link(name, root) for name in DEEP_LINK_HOSTS if name == host}

    if target.entry_format == "json":
        existing = _read_json(target.path)
        current_text = _read_text(target.path)
        already_owned = _json_already_owned(existing, target.key_path)
        entry = build_vscode_server_entry(root) if host == "vscode" else build_server_entry(root)
        new_config = build_json_config(existing, target.key_path, entry)
        content = json.dumps(new_config, indent=2, sort_keys=True) + "\n"
    else:  # toml (codex)
        current_text = _read_text(target.path)
        already_owned = _toml_already_owned(current_text)
        content = build_codex_config(current_text, root)

    existed_before = current_text is not None
    will_change = current_text != content
    needs_backup = existed_before and not already_owned
    status = "would_write" if will_change else "up_to_date"
    message = (
        (
            f"{target.path} would be created"
            if not existed_before
            else f"{target.path} would be updated"
        )
        if will_change
        else f"{target.path} already up to date"
    )
    return HostPlan(
        host=host,
        status=status,
        message=message,
        path=target.path,
        content=content,
        existed_before=existed_before,
        will_change=will_change,
        needs_backup=needs_backup,
        verified=target.verified,
        deep_links=deep_links,
    )


def write_host(
    host: str,
    root: Path,
    *,
    platform: str | None = None,
    home: Path | None = None,
    appdata: str | None = None,
) -> HostPlan:
    """Write *host*'s config file (idempotent, ``.bak`` on first foreign write)."""
    plan = plan_host(host, root, platform=platform, home=home, appdata=appdata)
    if plan.status in ("unobserved", "unknown") or plan.path is None:
        return plan
    if not plan.will_change:
        return plan
    full = plan.path
    if plan.needs_backup:
        backup_path = full.with_name(full.name + ".bak")
        shutil.copy2(full, backup_path)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(plan.content, encoding="utf-8")
    return plan


# --------------------------------------------------------------------------
# Deep links — documented one-click install URLs, never claimed tested.
# --------------------------------------------------------------------------


def vscode_deep_link(root: Path) -> str:
    """The documented VS Code one-click MCP install link for *root*."""
    payload = {"name": "hyodo", **build_server_entry(root)}
    return "vscode:mcp/install?" + quote(json.dumps(payload), safe="")


def cursor_deep_link(root: Path) -> str:
    """The documented Cursor one-click MCP install link for *root*."""
    encoded = base64.b64encode(json.dumps(build_server_entry(root)).encode("utf-8")).decode("ascii")
    return f"cursor://anysphere.cursor-deeplink/mcp/install?name=hyodo&config={encoded}"


def _build_deep_link(host: str, root: Path) -> str:
    if host == "vscode":
        return vscode_deep_link(root)
    if host == "cursor":
        return cursor_deep_link(root)
    raise ValueError(f"no deep link for host: {host}")
