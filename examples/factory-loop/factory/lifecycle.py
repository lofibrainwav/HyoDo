"""Phase 2.1 — Lifecycle Manager (`add`, `enable`, `disable`, `update`, `rollback`, `remove`, `doctor`, `discover`, `hosts`).

Manages module installation, granular sub-skill activation with automatic
dependency resolution, conflict detection, atomic update with rollback
snapshots, hook/permission cleanup on removal, mid-run/concurrent locking,
generic external skill discovery, and host integration verification.
"""

from __future__ import annotations

import ast
import contextlib
import fcntl
import json
import os
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

from adapters.agent_skills import (
    detect_repo_license,
    detect_repo_version,
    discover_skill_files,
    load_agent_skills_module,
)
from adapters.claude_plugin import load_claude_plugin_module
from adapters.external_evaluator import load_external_evaluator_module

from factory.contracts import ModuleRecord
from factory.registry import (
    ACTIVE_HOOKS_REL,
    LIFECYCLE_FLOCK_REL,
    RUN_LOCK_REL,
    SNAPSHOTS_DIR_REL,
    _atomic_write_text,
    compare_module_origin,
    load_registry_state,
    observe_module_origin,
    save_registry_state,
    verify_lock_integrity,
)
from hyodo.connect import ALL_TARGETS as CONNECT_TARGETS
from hyodo.connect import plan_target as plan_connect_target
from hyodo.mcp_config import ALL_HOSTS as MCP_ALL_HOSTS
from hyodo.mcp_config import plan_host as plan_mcp_host

# Doctor warnings about provenance that could not be observed. They make the
# doctor status UNOBSERVED but do not degrade the module's skills for routing.
PROVENANCE_UNOBSERVED_PREFIXES = ("module_origin_unrecorded:", "module_tree_unbindable:")


@contextlib.contextmanager
def _lifecycle_flock(workspace_root: Path) -> Iterator[None]:
    """Acquire an OS-level exclusive advisory file lock for atomic registry mutations."""
    flock_path = workspace_root / LIFECYCLE_FLOCK_REL
    flock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(flock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _run_lock_owned_by(workspace_root: Path, owner_run_id: str | None) -> bool:
    if owner_run_id is None:
        return False
    try:
        held = json.loads((workspace_root / RUN_LOCK_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return (
        isinstance(held, dict)
        and held.get("run_id") == owner_run_id
        and held.get("pid") == os.getpid()
    )


def _check_not_mid_run(workspace_root: Path, owner_run_id: str | None = None) -> None:
    """Refuse lifecycle mutations while a task run lock is active (Acceptance Gate #9).

    The run that holds the lock (same `run_id` and process) may still apply its
    own task-scoped activation and restore it; nobody else may.
    """
    run_lock = workspace_root / RUN_LOCK_REL
    if run_lock.exists() and not _run_lock_owned_by(workspace_root, owner_run_id):
        raise RuntimeError(
            "MID_RUN_SKILL_MUTATION_FORBIDDEN: cannot add, remove, update, or toggle skills while a run is active"
        )


def acquire_run_lock(workspace_root: Path, run_id: str) -> Path:
    """Atomically acquire `.hyodo/factory/run.lock` (`O_CREAT | O_EXCL`) and verify lock integrity."""
    problems = verify_lock_integrity(workspace_root)
    if problems:
        raise RuntimeError(f"MID_RUN_SKILL_DRIFT: {problems}")
    lock_file = workspace_root / RUN_LOCK_REL
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(
            f"CONCURRENT_RUN_LOCK_HELD: another factory run already holds {RUN_LOCK_REL}"
        ) from exc
    try:
        payload = (json.dumps({"run_id": run_id, "pid": os.getpid()}) + "\n").encode("utf-8")
        os.write(fd, payload)
        os.fsync(fd)
    finally:
        os.close(fd)
    return lock_file


def release_run_lock(workspace_root: Path) -> None:
    """Release `.hyodo/factory/run.lock`."""
    lock_file = workspace_root / RUN_LOCK_REL
    if lock_file.exists():
        with contextlib.suppress(FileNotFoundError):
            lock_file.unlink()


def detect_adapter_kind(source_path: Path) -> str:
    """Auto-detect whether *source_path* is an external evaluator, multi-host/Claude plugin, or Agent Skills repo."""
    if list(source_path.glob("*_worker.py")):
        return "external-evaluator"
    for manifest_rel in (
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".antigravity-plugin/plugin.json",
        "plugin.json",
        "package.json",
        "cli/package.json",
    ):
        if (source_path / manifest_rel).is_file():
            return "claude-plugin"
    return "agent-skills"


def _load_module_with_adapter(
    source_path: Path,
    *,
    adapter: str | None = None,
    module_id: str | None = None,
    version: str | None = None,
) -> ModuleRecord:
    kind = adapter or detect_adapter_kind(source_path)
    if kind == "external-evaluator":
        record = load_external_evaluator_module(source_path, module_id=module_id, version=version)
    elif kind == "claude-plugin":
        record = load_claude_plugin_module(source_path, module_id=module_id, version=version)
    elif kind == "agent-skills":
        record = load_agent_skills_module(source_path, module_id=module_id, version=version)
    else:
        raise ValueError(f"unsupported adapter kind: {kind}")
    # Record the module's real origin (path, git remote/commit/dirty, whole-tree
    # digest) at add/update time so `doctor` can report later drift.
    return replace(record, origin=observe_module_origin(Path(record.source_path)))


def add_module(
    workspace_root: Path,
    source_path: Path,
    *,
    adapter: str | None = None,
    module_id: str | None = None,
    version: str | None = None,
    enable_all: bool = True,
) -> ModuleRecord:
    """Discover, validate, and register a skill module into `.hyodo/factory/`."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root)
        modules = load_registry_state(workspace_root)
        record = _load_module_with_adapter(
            source_path, adapter=adapter, module_id=module_id, version=version
        )
        if record.module_id in modules:
            raise ValueError(f"duplicate_module_id: {record.module_id} is already registered")

        if not enable_all:
            disabled_skills = {sid: replace(u, enabled=False) for sid, u in record.skills.items()}
            record = replace(record, enabled=False, skills=disabled_skills)

        modules[record.module_id] = record
        save_registry_state(workspace_root, modules)
        return record


def enable_target(
    workspace_root: Path,
    target: str,
    *,
    only: bool = False,
) -> list[str]:
    """Enable a whole module (`gstack`) or a specific skill (`gstack/qa`) plus its required dependencies."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root)
        modules = load_registry_state(workspace_root)

        if "/" not in target:
            if target not in modules:
                raise KeyError(f"unknown module: {target}")
            mod = modules[target]
            updated_skills = {sid: replace(u, enabled=True) for sid, u in mod.skills.items()}
            modules[target] = replace(mod, enabled=True, skills=updated_skills)
            save_registry_state(workspace_root, modules)
            return sorted(updated_skills)

        mod_id, _ = target.split("/", 1)
        if mod_id not in modules or target not in modules[mod_id].skills:
            raise KeyError(f"unknown skill: {target}")

        to_enable: set[str] = set()
        queue = [target]
        while queue:
            current = queue.pop(0)
            if current in to_enable:
                continue
            c_mod_id = current.split("/", 1)[0]
            if c_mod_id not in modules or current not in modules[c_mod_id].skills:
                raise ValueError(f"missing_dependency: {current} required by {target}")
            unit = modules[c_mod_id].skills[current]
            for m in modules.values():
                if not m.enabled:
                    continue
                for other_id, other_unit in m.skills.items():
                    if not other_unit.enabled or (
                        only and m.module_id == mod_id and other_id not in to_enable
                    ):
                        continue
                    if other_id in unit.conflicts_with or current in other_unit.conflicts_with:
                        raise ValueError(
                            f"skill_conflict: {current} conflicts with enabled skill {other_id}"
                        )
            to_enable.add(current)
            for dep in unit.dependencies:
                if dep not in to_enable:
                    queue.append(dep)

        for skill_id in to_enable:
            s_mod_id = skill_id.split("/", 1)[0]
            s_mod = modules[s_mod_id]
            new_skills = dict(s_mod.skills)
            if only and s_mod_id == mod_id:
                new_skills = {
                    sid: replace(u, enabled=(sid in to_enable)) for sid, u in new_skills.items()
                }
            else:
                new_skills[skill_id] = replace(new_skills[skill_id], enabled=True)
            modules[s_mod_id] = replace(s_mod, enabled=True, skills=new_skills)

        save_registry_state(workspace_root, modules)
        return sorted(to_enable)


def disable_target(workspace_root: Path, target: str) -> list[str]:
    """Disable an entire module (`gstack`) or a single skill (`gstack/qa`) and any skill depending on it."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root)
        modules = load_registry_state(workspace_root)

        if "/" not in target:
            if target not in modules:
                raise KeyError(f"unknown module: {target}")
            mod = modules[target]
            disabled_skills = {sid: replace(u, enabled=False) for sid, u in mod.skills.items()}
            modules[target] = replace(mod, enabled=False, skills=disabled_skills)
            save_registry_state(workspace_root, modules)
            return sorted(disabled_skills)

        mod_id, _ = target.split("/", 1)
        if mod_id not in modules or target not in modules[mod_id].skills:
            raise KeyError(f"unknown skill: {target}")

        disabled: set[str] = {target}
        changed = True
        while changed:
            changed = False
            for _m_id, m in modules.items():
                for sid, u in m.skills.items():
                    if (
                        u.enabled
                        and sid not in disabled
                        and any(dep in disabled for dep in u.dependencies)
                    ):
                        disabled.add(sid)
                        changed = True

        for sid in disabled:
            m_id = sid.split("/", 1)[0]
            m = modules[m_id]
            new_skills = dict(m.skills)
            new_skills[sid] = replace(new_skills[sid], enabled=False)
            any_still_enabled = any(u.enabled for u in new_skills.values())
            modules[m_id] = replace(m, enabled=any_still_enabled, skills=new_skills)

        save_registry_state(workspace_root, modules)
        return sorted(disabled)


def activate_selected_skills(
    workspace_root: Path,
    skill_ids: list[str],
    *,
    disable_others: bool = True,
    owner_run_id: str | None = None,
) -> list[str]:
    """Atomically enable only *skill_ids* plus their transitive dependencies in one registry write."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root, owner_run_id)
        modules = load_registry_state(workspace_root)
        unit_map = {sid: u for mod in modules.values() for sid, u in mod.skills.items()}
        to_enable: set[str] = set()
        queue = [sid for sid in skill_ids if sid in unit_map]
        while queue:
            cur = queue.pop(0)
            if cur in to_enable:
                continue
            unit = unit_map.get(cur)
            if unit is None:
                continue
            if any(c in to_enable for c in unit.conflicts_with):
                continue
            if any(cur in unit_map[e].conflicts_with for e in to_enable if e in unit_map):
                continue
            to_enable.add(cur)
            for dep in unit.dependencies:
                if dep in unit_map and dep not in to_enable:
                    queue.append(dep)

        for mod_id, mod in list(modules.items()):
            new_skills = {}
            for sid, u in mod.skills.items():
                should_enable = (
                    sid in to_enable if disable_others else (u.enabled or sid in to_enable)
                )
                new_skills[sid] = replace(u, enabled=should_enable)
            any_enabled = any(u.enabled for u in new_skills.values())
            modules[mod_id] = replace(mod, enabled=any_enabled, skills=new_skills)

        save_registry_state(workspace_root, modules)
        return sorted(to_enable)


ActivationSnapshot = dict[str, tuple[bool, dict[str, bool]]]


def snapshot_activation_state(workspace_root: Path) -> ActivationSnapshot:
    """Capture every module's and skill's `enabled` flag (for task-scoped activation)."""
    modules = load_registry_state(workspace_root)
    return {
        mod_id: (mod.enabled, {sid: u.enabled for sid, u in mod.skills.items()})
        for mod_id, mod in modules.items()
    }


def restore_activation_state(
    workspace_root: Path,
    snapshot: ActivationSnapshot,
    *,
    owner_run_id: str | None = None,
) -> list[str]:
    """Restore the `enabled` flags captured by `snapshot_activation_state` in one write.

    Only enablement is restored; skills or modules added since the snapshot are
    left as they are. Returns the skill ids whose flag was changed back.
    """
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root, owner_run_id)
        modules = load_registry_state(workspace_root)
        restored: list[str] = []
        for mod_id, mod in list(modules.items()):
            if mod_id not in snapshot:
                continue
            mod_enabled, skill_flags = snapshot[mod_id]
            new_skills = {}
            for sid, u in mod.skills.items():
                want = skill_flags.get(sid, u.enabled)
                if want != u.enabled:
                    restored.append(sid)
                new_skills[sid] = replace(u, enabled=want)
            modules[mod_id] = replace(mod, enabled=mod_enabled, skills=new_skills)
        save_registry_state(workspace_root, modules)
        return sorted(restored)


def update_module(
    workspace_root: Path,
    module_id: str,
    *,
    new_source_path: Path | None = None,
    new_version: str | None = None,
) -> ModuleRecord:
    """Atomically update *module_id*, saving a rollback snapshot first."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root)
        modules = load_registry_state(workspace_root)
        if module_id not in modules:
            raise KeyError(f"unknown module: {module_id}")

        previous = modules[module_id]
        src = new_source_path or Path(previous.source_path)
        ver = new_version or previous.version
        updated = _load_module_with_adapter(
            src,
            adapter=previous.adapter,
            module_id=module_id,
            version=ver,
        )
        merged_skills = {}
        for sid, u in updated.skills.items():
            was_enabled = (
                previous.skills[sid].enabled if sid in previous.skills else updated.enabled
            )
            merged_skills[sid] = replace(u, enabled=was_enabled)
        updated = replace(updated, enabled=previous.enabled, skills=merged_skills)

        snapshot_file = workspace_root / SNAPSHOTS_DIR_REL / f"{module_id}.json"
        _atomic_write_text(
            snapshot_file,
            json.dumps(previous.to_dict(), indent=2, sort_keys=True) + "\n",
        )

        modules[module_id] = updated
        save_registry_state(workspace_root, modules)
        return updated


def rollback_module(workspace_root: Path, module_id: str) -> ModuleRecord:
    """Restore *module_id* atomically from its saved snapshot in `.hyodo/factory/snapshots/`."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root)
        modules = load_registry_state(workspace_root)
        snapshot_file = workspace_root / SNAPSHOTS_DIR_REL / f"{module_id}.json"
        if not snapshot_file.is_file():
            raise FileNotFoundError(f"no rollback snapshot found for module: {module_id}")
        restored = ModuleRecord.from_dict(json.loads(snapshot_file.read_text(encoding="utf-8")))
        modules[module_id] = restored
        save_registry_state(workspace_root, modules)
        return restored


def remove_module(workspace_root: Path, module_id: str) -> dict[str, Any]:
    """Remove *module_id* and clean up all registered hooks, permissions, and manifest rules."""
    with _lifecycle_flock(workspace_root):
        _check_not_mid_run(workspace_root)
        modules = load_registry_state(workspace_root)
        if module_id not in modules:
            raise KeyError(f"unknown module: {module_id}")
        removed = modules.pop(module_id)
        save_registry_state(workspace_root, modules)
        hooks_state = json.loads((workspace_root / ACTIVE_HOOKS_REL).read_text(encoding="utf-8"))
        return {
            "removed_module": module_id,
            "removed_skills": sorted(removed.skills),
            "remaining_active_hooks": hooks_state.get("active_hooks", {}),
        }


def doctor(workspace_root: Path) -> dict[str, Any]:
    """Check registry health, content hash integrity, dependencies, conflicts, and script compatibility."""
    modules = load_registry_state(workspace_root)
    problems = verify_lock_integrity(workspace_root)
    warnings: list[str] = []

    enabled_ids: set[str] = set()
    for mod in modules.values():
        if mod.enabled:
            for sid, u in mod.skills.items():
                if u.enabled:
                    enabled_ids.add(sid)

    for mod in modules.values():
        if not mod.enabled:
            continue
        mod_root = Path(mod.source_path)
        for sid, u in mod.skills.items():
            if not u.enabled:
                continue
            for dep in u.dependencies:
                if dep not in enabled_ids:
                    problems.append(f"unmet_dependency:{sid}->requires->{dep}")
            for conflict in u.conflicts_with:
                if conflict in enabled_ids:
                    problems.append(f"active_conflict:{sid}<->{conflict}")
            # Verify Python script syntax compatibility on current runtime
            for script_rel in u.executable_scripts:
                if not script_rel.endswith(".py"):
                    continue
                script_path = mod_root / script_rel
                if script_path.is_file() and not script_path.is_symlink():
                    try:
                        ast.parse(
                            script_path.read_text(encoding="utf-8", errors="replace"),
                            filename=str(script_path),
                        )
                    except SyntaxError as exc:
                        problems.append(
                            f"incompatible_python_syntax:{sid}:{script_rel}:line_{exc.lineno}"
                        )
            if "hook_silent_zero_fallback" in u.capabilities:
                hook_scripts = [s for s in u.executable_scripts if "gate." in s or "hook" in s]
                existing_hook_scripts = [
                    s
                    for s in hook_scripts
                    if (mod_root / s).is_file() and not (mod_root / s).is_symlink()
                ]
                if existing_hook_scripts:
                    warnings.append(
                        f"unverified_hook_silent_zero:{sid}:frontmatter_hook_exits_0_when_host_env_unbound:"
                        f"script_present={existing_hook_scripts[0]}"
                    )
                else:
                    warnings.append(
                        f"unverified_hook_silent_zero:{sid}:frontmatter_hook_exits_0_when_script_missing"
                    )

    # Origin/tree drift: what would run is no longer what was registered.
    # Drift is a problem for enabled modules and a warning for dormant ones.
    # Unrecorded/unbindable origins are reported here only, never as healthy
    # evidence and never as drift.
    provenance: dict[str, dict[str, Any]] = {}
    for mod_id, mod in sorted(modules.items()):
        if not Path(mod.source_path).is_dir():
            continue
        cmp = compare_module_origin(mod)
        current = cmp["current"] or {}
        provenance[mod_id] = {
            "state": cmp["state"],
            "changed_fields": cmp["changed_fields"],
            "recorded_git_commit": mod.origin.get("git_commit"),
            "recorded_git_remote_url": mod.origin.get("git_remote_url"),
            "git_dirty_now": current.get("git_dirty"),
            "module_tree_error": mod.origin.get("module_tree_error"),
        }
        if cmp["state"] == "DRIFTED":
            sink = problems if mod.enabled else warnings
            for changed in cmp["changed_fields"]:
                if changed == "module_tree_sha256":
                    sink.append(f"module_tree_drift:{mod_id}")
                else:
                    sink.append(f"module_origin_drift:{mod_id}:{changed}")
        elif cmp["state"] == "UNRECORDED":
            warnings.append(f"{PROVENANCE_UNOBSERVED_PREFIXES[0]}{mod_id}")
        elif cmp["state"] == "UNBINDABLE":
            error = mod.origin.get("module_tree_error") or "unknown"
            warnings.append(f"{PROVENANCE_UNOBSERVED_PREFIXES[1]}{mod_id}|{error}")

    # Unrecorded or unbindable provenance is not evidence of health: without
    # problems the status is UNOBSERVED, never HEALTHY.
    provenance_unobserved = any(
        state["state"] in ("UNRECORDED", "UNBINDABLE") for state in provenance.values()
    )
    if problems:
        status = "DEGRADED"
    elif provenance_unobserved:
        status = "UNOBSERVED"
    else:
        status = "HEALTHY"
    return {
        "status": status,
        "modules_registered": len(modules),
        "skills_enabled": len(enabled_ids),
        "problems": sorted(set(problems)),
        "warnings": sorted(set(warnings)),
        "module_provenance": provenance,
    }


def discover_skills(
    search_roots: list[Path],
    *,
    query: str | None = None,
    max_results: int = 25,
) -> list[dict[str, Any]]:
    """Generic Agent Skills & Plugin discovery across local directories or catalogs (e.g. `antigravity-awesome-skills`, `external-skills`)."""
    q_tokens = [tok.lower() for tok in (query or "").split() if tok.strip()]
    results: list[dict[str, Any]] = []
    seen_paths: set[Path] = set()

    for base in search_roots:
        if not base.is_dir() or base.is_symlink():
            continue
        base_resolved = base.resolve()
        # 1. Check if `base` itself or its immediate children are skill repositories/packages
        candidate_dirs: list[Path] = []
        if (base_resolved / "skills_index.json").is_file() and (base_resolved / "skills").is_dir():
            candidate_dirs.extend(
                sorted(
                    p
                    for p in (base_resolved / "skills").iterdir()
                    if p.is_dir() and not p.name.startswith(".")
                )
            )
        else:
            if discover_skill_files(base_resolved) or list(base_resolved.glob("*_worker.py")):
                candidate_dirs.append(base_resolved)
            for child in sorted(base_resolved.iterdir()):
                if (
                    child.is_dir()
                    and not child.name.startswith(".")
                    and not child.is_symlink()
                    and (discover_skill_files(child) or list(child.glob("*_worker.py")))
                ):
                    candidate_dirs.append(child)

        for cdir in candidate_dirs:
            c_resolved = cdir.resolve()
            if c_resolved in seen_paths:
                continue
            seen_paths.add(c_resolved)
            try:
                adapter = detect_adapter_kind(c_resolved)
                skill_files = discover_skill_files(c_resolved)
                skill_names = [
                    sf.parent.name if sf.parent != c_resolved else c_resolved.name
                    for sf in skill_files
                ]
                haystack = f"{c_resolved.name} {' '.join(skill_names)}".lower()
                if q_tokens and not any(tok in haystack for tok in q_tokens):
                    continue
                hits = sum(1 for tok in q_tokens if tok in haystack) if q_tokens else 1
                results.append(
                    {
                        "name": c_resolved.name,
                        "path": str(c_resolved),
                        "adapter": adapter,
                        "version": detect_repo_version(c_resolved),
                        "license_spdx": detect_repo_license(c_resolved),
                        "skill_count": len(skill_files)
                        or len(list(c_resolved.glob("*_worker.py"))),
                        "sample_skills": skill_names[:8],
                        "match_score": hits,
                    }
                )
            except (OSError, ValueError):
                continue

    results.sort(key=lambda r: (-int(r["match_score"]), str(r["name"])))
    return results[:max_results]


_LIVE_CONTRACT_UNOBSERVED_REASON = (
    "no live host session was exercised; only local connect/MCP config plans were inspected"
)


def verify_host_integrations(workspace_root: Path) -> dict[str, dict[str, Any]]:
    """Report host connection mechanics and support boundaries across Claude Code, Cursor, Codex, and Antigravity.

    This inspects local configuration plans only. It never runs a host, so the
    live host contract is reported as `UNOBSERVED` (`verified_live_contract: False`)
    for every host.
    """
    root = workspace_root.resolve()
    connect_plans = {t: plan_connect_target(t, root, shadow=True) for t in CONNECT_TARGETS}
    mcp_plans = {h: plan_mcp_host(h, root) for h in MCP_ALL_HOSTS}
    modules = load_registry_state(root)

    def _mods_for_host(host: str) -> list[str]:
        found: set[str] = set()
        for mod in modules.values():
            for unit in mod.skills.values():
                if not unit.supported_hosts or host in unit.supported_hosts:
                    found.add(mod.module_id)
        return sorted(found)

    return {
        "claude-code": {
            "hook_enforcement": "OBSERVED"
            if connect_plans["claude-code"].status != "unobserved"
            else "UNOBSERVED",
            "hook_config_path": ".claude/settings.json",
            "mcp_stdio": "OBSERVED"
            if mcp_plans["claude-code"].status != "unobserved"
            else "UNOBSERVED",
            "mcp_config_path": ".mcp.json",
            "skill_directories": (".claude/skills/", ".claude-plugin/plugin.json", "SKILL.md"),
            "verified_live_contract": False,
            "live_contract": "UNOBSERVED",
            "live_contract_reason": _LIVE_CONTRACT_UNOBSERVED_REASON,
            "compatible_modules": _mods_for_host("claude-code"),
        },
        "cursor": {
            "hook_enforcement": "UNOBSERVED",  # HyoDo connect.py explicitly reports cursor hooks UNOBSERVED
            "hook_reason": connect_plans["cursor"].message,
            "mcp_stdio": "OBSERVED" if mcp_plans["cursor"].status != "unobserved" else "UNOBSERVED",
            "mcp_config_path": ".cursor/mcp.json",
            "skill_directories": (".cursor/skills/", ".cursor-plugin/plugin.json", "SKILL.md"),
            "verified_live_contract": False,
            "live_contract": "UNOBSERVED",
            "live_contract_reason": _LIVE_CONTRACT_UNOBSERVED_REASON,
            "compatible_modules": _mods_for_host("cursor"),
        },
        "codex": {
            "hook_enforcement": "UNOBSERVED",  # HyoDo connect.py explicitly reports codex hooks UNOBSERVED
            "hook_reason": connect_plans["codex"].message,
            "mcp_stdio": "UNVERIFIED_FORMAT",  # Documented ~/.codex/config.toml, not live-verified
            "mcp_config_path": "~/.codex/config.toml",
            "skill_directories": (
                ".agents/skills/",
                "AGENTS.md",
                ".codex-plugin/plugin.json",
                "SKILL.md",
            ),
            "verified_live_contract": False,
            "live_contract": "UNOBSERVED",
            "live_contract_reason": _LIVE_CONTRACT_UNOBSERVED_REASON,
            "compatible_modules": _mods_for_host("codex"),
        },
        "antigravity": {
            "hook_enforcement": "UNOBSERVED",  # Host-managed exebox sandbox, no user hook config file
            "mcp_stdio": "HOST_MANAGED",
            "skill_directories": (
                ".agent/skills/",
                ".agents/skills/",
                "AGENTS.md",
                ".antigravity-plugin/plugin.json",
                "SKILL.md",
            ),
            "verified_live_contract": False,
            "live_contract": "UNOBSERVED",
            "live_contract_reason": _LIVE_CONTRACT_UNOBSERVED_REASON,
            "compatible_modules": _mods_for_host("antigravity"),
        },
    }
