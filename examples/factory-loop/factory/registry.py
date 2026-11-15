"""Phase 2.1 — Skill Registry (`.hyodo/factory/registry.toml` & `lock.json`).

Stores registered modules, per-skill enablement, content SHA-256 pins, and
active hook/permission bindings without hardcoding any repository name or path.
Uses atomic temp-file + `os.replace()` writes and cleans up host hook configs
(`.claude/settings.json`) when skills are disabled or removed.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import stat
import subprocess
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from factory.contracts import (
    FACTORY_LOCK_SCHEMA,
    FACTORY_REGISTRY_SCHEMA,
    ModuleRecord,
    SkillUnitSpec,
    utc_now_iso,
)
from hyodo.provenance import clean_git_env
from hyodo.skills import (
    compile_rule,
    content_digest,
    infer_pillars,
    load_manifest,
    rule_id_for,
    save_manifest,
    strip_pillar_tag,
)

FACTORY_DIR_REL = Path(".hyodo") / "factory"
REGISTRY_TOML_REL = FACTORY_DIR_REL / "registry.toml"
LOCK_JSON_REL = FACTORY_DIR_REL / "lock.json"
ACTIVE_HOOKS_REL = FACTORY_DIR_REL / "active_hooks.json"
SNAPSHOTS_DIR_REL = FACTORY_DIR_REL / "snapshots"
RUN_LOCK_REL = FACTORY_DIR_REL / "run.lock"
LIFECYCLE_FLOCK_REL = FACTORY_DIR_REL / "lifecycle.flock"

FACTORY_HOOK_MARKER = "# hyodo-factory-hook:"

# The only directory never hashed into a module tree digest is the module
# root's own `.git/`: git internals change on fetch/gc without changing what a
# skill runs (the commit and dirty flag are recorded separately). Any other
# `.git` or `.hyodo` directory (nested, or a `.hyodo/` inside the module) can
# hold files a skill runs, so it is hashed like everything else.
_TREE_EXCLUDED_ROOT_DIR = ".git"


def redact_remote_url(raw: str) -> str | None:
    """Strip credentials from a git remote URL: userinfo, query string and fragment.

    Only URLs with a scheme and a host are rewritten; scp-style `host:path`
    remotes and local paths carry no userinfo field and are returned as is.
    """
    raw = raw.strip()
    if not raw:
        return None
    parts = urlsplit(raw)
    if not parts.scheme or not parts.netloc:
        return raw
    host = parts.netloc.rpartition("@")[2]
    return urlunsplit((parts.scheme, host, parts.path, "", ""))


def compute_module_tree_digest(module_root: Path) -> tuple[str | None, int, str | None]:
    """Digest every regular file under *module_root* (relative path, exec bit, content).

    Symlinks (files or directories) and non-regular files are refused: the
    digest is then `None` with a reason, because a binding that cannot see what
    a link points to at run time binds nothing. Returns `(digest, file_count, error)`.
    """
    if module_root.is_symlink() or not module_root.is_dir():
        return None, 0, "module_root_missing_or_symlink"
    hasher = hashlib.sha256()
    count = 0
    for dirpath, dirnames, filenames in os.walk(module_root, followlinks=False):
        base = Path(dirpath)
        kept_dirs: list[str] = []
        for name in sorted(dirnames):
            if name == _TREE_EXCLUDED_ROOT_DIR and base == module_root:
                continue
            if (base / name).is_symlink():
                rel = (base / name).relative_to(module_root).as_posix()
                return None, count, f"symlink_refused:{rel}"
            kept_dirs.append(name)
        dirnames[:] = kept_dirs
        for name in sorted(filenames):
            full = base / name
            rel = full.relative_to(module_root).as_posix()
            try:
                st = full.lstat()
            except OSError:
                return None, count, f"unreadable:{rel}"
            if stat.S_ISLNK(st.st_mode):
                return None, count, f"symlink_refused:{rel}"
            if not stat.S_ISREG(st.st_mode):
                return None, count, f"non_regular_file_refused:{rel}"
            file_hasher = hashlib.sha256()
            try:
                with full.open("rb") as fh:
                    while chunk := fh.read(1 << 20):
                        file_hasher.update(chunk)
            except OSError:
                return None, count, f"unreadable:{rel}"
            exec_flag = "x" if st.st_mode & 0o111 else "-"
            hasher.update(f"{rel}\0{exec_flag}\0{file_hasher.hexdigest()}\n".encode())
            count += 1
    return hasher.hexdigest(), count, None


def _git_out(root: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
            env=clean_git_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def observe_module_origin(module_root: Path) -> dict[str, Any]:
    """Record where a module came from, as observed now (never inferred).

    Git fields are `None` when *module_root* is not inside a git work tree.
    Credentials embedded in a remote URL are stripped before recording.
    """
    tree_digest, file_count, tree_error = compute_module_tree_digest(module_root)
    inside = (_git_out(module_root, "rev-parse", "--is-inside-work-tree") or "").strip()
    in_git = inside == "true"
    remote_url: str | None = None
    commit: str | None = None
    dirty: bool | None = None
    if in_git:
        raw_remote = (_git_out(module_root, "config", "--get", "remote.origin.url") or "").strip()
        remote_url = redact_remote_url(raw_remote)
        commit = (_git_out(module_root, "rev-parse", "HEAD") or "").strip() or None
        porcelain = _git_out(
            module_root, "status", "--porcelain", "--untracked-files=normal", "--", "."
        )
        dirty = None if porcelain is None else bool(porcelain.strip())
    return {
        "source_path": str(module_root),
        "git_repo": in_git,
        "git_remote_url": remote_url,
        "git_commit": commit,
        "git_dirty": dirty,
        "module_tree_sha256": tree_digest,
        "module_tree_file_count": file_count,
        "module_tree_error": tree_error,
        "recorded_at": utc_now_iso(),
    }


def compare_module_origin(mod: ModuleRecord) -> dict[str, Any]:
    """Compare the origin recorded in `lock.json` with what is on disk now.

    `state` is `UNCHANGED`, `DRIFTED` (with `changed_fields`), `UNRECORDED`
    (a lock written before origins were recorded) or `UNBINDABLE` (the tree
    could not be digested at add time, e.g. it contains a symlink).
    """
    recorded = mod.origin
    if not recorded:
        return {"state": "UNRECORDED", "changed_fields": [], "current": None}
    current = observe_module_origin(Path(mod.source_path))
    changed: list[str] = []
    if recorded.get("source_path") != mod.source_path:
        changed.append("source_path")
    for key in ("git_remote_url", "git_commit"):
        if recorded.get(key) != current.get(key):
            changed.append(key)
    recorded_tree = recorded.get("module_tree_sha256")
    if recorded_tree is not None and current.get("module_tree_sha256") != recorded_tree:
        changed.append("module_tree_sha256")
    if changed:
        state = "DRIFTED"
    elif recorded_tree is None:
        state = "UNBINDABLE"
    else:
        state = "UNCHANGED"
    return {"state": state, "changed_fields": changed, "current": current}


def _atomic_write_text(target: Path, content: str) -> None:
    """Write *content* to *target* atomically via a sibling temporary file + `os.replace`."""
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target.parent / f".{target.name}.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    try:
        with tmp_path.open("w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            with contextlib.suppress(OSError):
                tmp_path.unlink()


def _render_registry_toml(modules: dict[str, ModuleRecord]) -> str:
    """Render deterministic `.hyodo/factory/registry.toml`."""
    lines = [
        f"# Managed by HyoDo Factory Registry ({FACTORY_REGISTRY_SCHEMA})",
        f'schema = "{FACTORY_REGISTRY_SCHEMA}"',
        "",
    ]
    for mod_id in sorted(modules):
        mod = modules[mod_id]
        enabled_skills = sorted(sid for sid, u in mod.skills.items() if u.enabled)
        lines.append(f'[modules."{mod.module_id}"]')
        lines.append(f"source_path = {json.dumps(mod.source_path)}")
        lines.append(f'adapter = "{mod.adapter}"')
        lines.append(f'version = "{mod.version}"')
        lines.append(f'license_spdx = "{mod.license_spdx}"')
        lines.append(f'git_commit = "{mod.git_commit or "UNOBSERVED"}"')
        lines.append(f'tree_sha256 = "{mod.tree_sha256}"')
        origin = mod.origin or {}
        lines.append(f"git_remote_url = {json.dumps(origin.get('git_remote_url') or 'UNOBSERVED')}")
        dirty = origin.get("git_dirty")
        lines.append(f'git_dirty = "{"UNOBSERVED" if dirty is None else str(dirty).lower()}"')
        lines.append(f'module_tree_sha256 = "{origin.get("module_tree_sha256") or "UNOBSERVED"}"')
        lines.append(f"enabled = {'true' if mod.enabled else 'false'}")
        lines.append(f"enabled_skills = {json.dumps(enabled_skills)}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def load_registry_state(workspace_root: Path) -> dict[str, ModuleRecord]:
    """Load all registered `ModuleRecord` items from `.hyodo/factory/lock.json`."""
    lock_path = workspace_root / LOCK_JSON_REL
    if not lock_path.is_file():
        return {}
    raw = json.loads(lock_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema") != FACTORY_LOCK_SCHEMA:
        raise ValueError("corrupt or unsupported .hyodo/factory/lock.json")
    modules_raw = raw.get("modules", {})
    if not isinstance(modules_raw, dict):
        return {}
    return {
        mod_id: ModuleRecord.from_dict(mod_data)
        for mod_id, mod_data in sorted(modules_raw.items())
        if isinstance(mod_data, dict)
    }


def _sync_claude_settings_hooks(
    workspace_root: Path,
    hooks_by_skill: dict[str, list[str]],
) -> None:
    """If `.claude/settings.json` exists in *workspace_root*, sync factory skill hooks and remove stale ones."""
    settings_path = workspace_root / ".claude" / "settings.json"
    if not settings_path.is_file() or settings_path.is_symlink():
        return
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(settings, dict):
        return

    hooks_obj = settings.get("hooks")
    hooks_dict: dict[str, Any] = dict(hooks_obj) if isinstance(hooks_obj, dict) else {}
    pre_list_raw = hooks_dict.get("PreToolUse")
    pre_list: list[Any] = list(pre_list_raw) if isinstance(pre_list_raw, list) else []

    # Strip all previously registered factory hooks first
    kept_pre: list[Any] = []
    for entry in pre_list:
        if not isinstance(entry, dict):
            kept_pre.append(entry)
            continue
        inner = entry.get("hooks")
        if isinstance(inner, list) and any(
            isinstance(h, dict)
            and isinstance(h.get("command"), str)
            and FACTORY_HOOK_MARKER in h["command"]
            for h in inner
        ):
            continue
        kept_pre.append(entry)

    # Re-add currently active factory skill hooks
    for skill_id in sorted(hooks_by_skill):
        for hook_tag in hooks_by_skill[skill_id]:
            cmd = f"hyodo policy check --stdin --hook claude-code {FACTORY_HOOK_MARKER}{skill_id}:{hook_tag}"
            kept_pre.append(
                {
                    "matcher": "*",
                    "hooks": [{"type": "command", "command": cmd}],
                }
            )

    hooks_dict["PreToolUse"] = kept_pre
    settings["hooks"] = hooks_dict
    _atomic_write_text(settings_path, json.dumps(settings, indent=2, sort_keys=True) + "\n")


def _sync_active_hooks_and_manifest(
    workspace_root: Path,
    modules: dict[str, ModuleRecord],
) -> None:
    """Synchronize `.hyodo/factory/active_hooks.json`, `.claude/settings.json`, and `.hyodo/skills/manifest.json`."""
    hooks_by_skill: dict[str, list[str]] = {}
    permissions_by_skill: dict[str, dict[str, Any]] = {}
    factory_manifest_entries: list[dict[str, Any]] = []

    for mod_id in sorted(modules):
        mod = modules[mod_id]
        if not mod.enabled:
            continue
        for skill_id in sorted(mod.skills):
            unit = mod.skills[skill_id]
            if not unit.enabled:
                continue
            if unit.boundary.hooks:
                hooks_by_skill[skill_id] = list(unit.boundary.hooks)
            permissions_by_skill[skill_id] = unit.boundary.to_dict()

            if unit.mechanical_rules:
                node_rules = []
                compiled_ids = []
                pillars_acc: list[str] = []
                for idx, rtext in enumerate(unit.mechanical_rules, start=1):
                    base_text, tagged = strip_pillar_tag(rtext)
                    pillars = tagged if tagged is not None else infer_pillars(base_text)
                    compiled = compile_rule(base_text)
                    if compiled is None:
                        continue
                    rid = rule_id_for(f"factory/{skill_id}", base_text)
                    compiled_ids.append(rid)
                    for p in pillars:
                        if p not in pillars_acc:
                            pillars_acc.append(p)
                    node_rules.append(
                        {
                            "skill": unit.name,
                            "source": f"path:{unit.relative_path}",
                            "rule_text": rtext,
                            "rule_digest": content_digest(rtext) or "",
                            "score_rank": idx,
                        }
                    )
                if node_rules:
                    factory_manifest_entries.append(
                        {
                            "name": f"factory-{skill_id.replace('/', '-')}",
                            "source": f"node:factory-{skill_id.replace('/', '-')}",
                            "content_digest": unit.content_sha256[:12],
                            "status": "ok",
                            "pillars": pillars_acc,
                            "compiled_rule_ids": compiled_ids,
                            "ingested_at": mod.installed_at,
                            "body_stored": False,
                            "node_rules": node_rules,
                        }
                    )

    active_hooks_path = workspace_root / ACTIVE_HOOKS_REL
    _atomic_write_text(
        active_hooks_path,
        json.dumps(
            {
                "active_hooks": hooks_by_skill,
                "active_permissions": permissions_by_skill,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    _sync_claude_settings_hooks(workspace_root, hooks_by_skill)

    manifest, status = load_manifest(workspace_root)
    existing = list(manifest.get("skills", [])) if manifest and status == "ok" else []
    non_factory = [
        row
        for row in existing
        if not (isinstance(row.get("source"), str) and row["source"].startswith("node:factory-"))
    ]
    if (
        non_factory
        or factory_manifest_entries
        or (workspace_root / ".hyodo" / "skills" / "manifest.json").exists()
    ):
        save_manifest(workspace_root, [*non_factory, *factory_manifest_entries])


def _ensure_hyodo_git_exclude(workspace_root: Path) -> None:
    """Ensure `.hyodo/` is listed in `.git/info/exclude` so harness state does not dirty git worktree."""
    exclude_file = workspace_root / ".git" / "info" / "exclude"
    if not exclude_file.parent.is_dir():
        return
    try:
        current = exclude_file.read_text(encoding="utf-8") if exclude_file.is_file() else ""
        entries = {line.strip() for line in current.splitlines()}
        if ".hyodo/" not in entries and ".hyodo" not in entries:
            suffix = "" if (not current or current.endswith("\n")) else "\n"
            exclude_file.write_text(f"{current}{suffix}.hyodo/\n", encoding="utf-8")
    except OSError:
        pass


def save_registry_state(workspace_root: Path, modules: dict[str, ModuleRecord]) -> None:
    """Persist both `registry.toml`, `lock.json`, and synced hooks/manifest atomically."""
    _ensure_hyodo_git_exclude(workspace_root)
    lock_payload = {
        "schema": FACTORY_LOCK_SCHEMA,
        "modules": {mod_id: mod.to_dict() for mod_id, mod in sorted(modules.items())},
    }
    _atomic_write_text(
        workspace_root / LOCK_JSON_REL,
        json.dumps(lock_payload, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write_text(
        workspace_root / REGISTRY_TOML_REL,
        _render_registry_toml(modules),
    )
    _sync_active_hooks_and_manifest(workspace_root, modules)


def list_enabled_skills(workspace_root: Path) -> list[SkillUnitSpec]:
    """Return all currently enabled `SkillUnitSpec` objects in deterministic order."""
    modules = load_registry_state(workspace_root)
    active: list[SkillUnitSpec] = []
    for mod_id in sorted(modules):
        mod = modules[mod_id]
        if not mod.enabled:
            continue
        for skill_id in sorted(mod.skills):
            unit = mod.skills[skill_id]
            if unit.enabled:
                active.append(unit)
    return active


def verify_lock_integrity(workspace_root: Path) -> list[str]:
    """Verify that every enabled skill's on-disk SHA-256 matches `lock.json`."""
    problems: list[str] = []
    modules = load_registry_state(workspace_root)
    for mod_id, mod in sorted(modules.items()):
        if not mod.enabled:
            continue
        src = Path(mod.source_path)
        if not src.is_dir():
            problems.append(f"missing_module_source:{mod_id}:{mod.source_path}")
            continue
        for skill_id, unit in sorted(mod.skills.items()):
            if not unit.enabled:
                continue
            target = src / unit.relative_path
            if target.is_symlink() or not target.is_file():
                problems.append(f"missing_or_symlink_skill_file:{skill_id}")
                continue
            actual_sha = hashlib.sha256(target.read_bytes()).hexdigest()
            if actual_sha != unit.content_sha256:
                problems.append(f"content_hash_drift:{skill_id}")
    return problems
