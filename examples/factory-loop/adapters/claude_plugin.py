"""Phase 2.2 — Multi-Host / Claude Code Runtime Plugin adapter (`claude-plugin`).

Handles skill repositories that bundle runtime scripts, browser binaries,
hooks, or MCP server definitions alongside `SKILL.md` (such as `gstack`,
`superpowers`, `pstack`, `taste-skill`, `ui-ux-pro-max-skill`, or `impeccable`).
Tracks hooks and intra-module binary dependencies (e.g. `qa` -> `browse`) so
enabling one skill activates only its required dependencies and removing it
cleans up all registered hooks/permissions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from factory.contracts import ModuleRecord, PermissionBoundary, SkillUnitSpec

from adapters.agent_skills import (
    _git_head_sha,
    detect_repo_license,
    detect_repo_supported_hosts,
    detect_repo_version,
    discover_skill_files,
    parse_skill_unit,
)

_PLUGIN_MANIFEST_PATHS = (
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".antigravity-plugin/plugin.json",
    "plugin.json",
    "package.json",
    "cli/package.json",
)


def _discover_plugin_metadata(root: Path) -> tuple[tuple[str, ...], tuple[str, ...], str]:
    """Return `(hooks, mcp_servers, version)` declared by any plugin manifest in *root*."""
    hooks: list[str] = []
    mcp_servers: list[str] = []
    version = detect_repo_version(root)

    for rel in _PLUGIN_MANIFEST_PATHS:
        cand = root / rel
        if not cand.is_file() or cand.is_symlink():
            continue
        try:
            data = json.loads(cand.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        if isinstance(data.get("hooks"), list):
            for h in data["hooks"]:
                tag = str(h)
                if tag not in hooks:
                    hooks.append(tag)
        elif isinstance(data.get("hooks"), dict):
            for k in data["hooks"]:
                tag = f"manifest-hook:{k}"
                if tag not in hooks:
                    hooks.append(tag)
        if isinstance(data.get("mcpServers"), dict):
            for k in data["mcpServers"]:
                srv = str(k)
                if srv not in mcp_servers:
                    mcp_servers.append(srv)

    return tuple(hooks), tuple(mcp_servers), version


def load_claude_plugin_module(
    source_path: Path,
    *,
    module_id: str | None = None,
    version: str | None = None,
) -> ModuleRecord:
    """Load a runtime/hook-equipped plugin repository as a `ModuleRecord`."""
    root = source_path.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"plugin source must be a directory: {source_path}")
    mod_id = (module_id or root.name).strip().lower().replace(" ", "-")
    declared_hooks, declared_mcp, detected_version = _discover_plugin_metadata(root)
    resolved_version = version or detected_version
    license_spdx = detect_repo_license(root)
    hosts = tuple(detect_repo_supported_hosts(root))

    skill_files = discover_skill_files(root)
    if not skill_files:
        raise ValueError(f"no skill files found in plugin directory {root}")

    raw_units: dict[str, tuple[SkillUnitSpec, str]] = {}
    for sfile in skill_files:
        text = sfile.read_text(encoding="utf-8", errors="replace")
        unit = parse_skill_unit(
            root,
            mod_id,
            sfile,
            adapter_name="claude-plugin",
            supported_hosts=hosts,
        )
        if unit.skill_id in raw_units:
            raise ValueError(f"duplicate_skill_id: {unit.skill_id}")
        raw_units[unit.skill_id] = (unit, text)

    browse_skill_id = f"{mod_id}/browse"
    has_browse = browse_skill_id in raw_units

    skills: dict[str, SkillUnitSpec] = {}
    tree_hasher = hashlib.sha256()
    for skill_id, (unit, text) in sorted(raw_units.items()):
        deps = list(unit.dependencies)
        if (
            has_browse
            and skill_id != browse_skill_id
            and ("$B " in text or "/browse" in text or "headless browser" in text.lower())
            and browse_skill_id not in deps
        ):
            deps.append(browse_skill_id)

        skill_hooks = list(dict.fromkeys([*declared_hooks, *unit.boundary.hooks]))
        if unit.name in ("careful", "freeze", "guard"):
            hook_tag = f"pre-tool:{mod_id}:{unit.name}"
            if hook_tag not in skill_hooks:
                skill_hooks.append(hook_tag)

        boundary = PermissionBoundary(
            allowed_tools=("Read", "Grep", "Glob", "Bash")
            if unit.role_hint in ("builder", "verifier")
            else ("Read",),
            allowed_paths=(str(root),),
            hooks=tuple(skill_hooks),
            mcp_servers=declared_mcp,
            filesystem_read=True,
            filesystem_write=unit.boundary.filesystem_write,
            subprocess_exec=bool(unit.executable_scripts)
            or unit.role_hint in ("builder", "verifier"),
            network_access=False,
            browser_automation=(
                has_browse and (skill_id == browse_skill_id or browse_skill_id in deps)
            ),
            execution_authority=False,
        )
        enriched = replace(unit, dependencies=tuple(deps), boundary=boundary)
        skills[skill_id] = enriched
        tree_hasher.update(f"{enriched.skill_id}:{enriched.content_sha256}\n".encode())

    return ModuleRecord(
        module_id=mod_id,
        source_path=str(root),
        adapter="claude-plugin",
        version=resolved_version,
        git_commit=_git_head_sha(root),
        tree_sha256=tree_hasher.hexdigest(),
        enabled=True,
        license_spdx=license_spdx,
        skills=skills,
    )
