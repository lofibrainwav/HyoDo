"""Phase 2.2 — Standard Agent Skills (`SKILL.md` / `skill.md` / `AGENTS.md`) adapter with Progressive Disclosure.

Discovers skills in any repository or directory without hardcoding repository
names. Separates mechanical rules (`require file:`, `forbid pattern:`,
`require pattern:`, `ruff:`) from semantic/advisory guidance (`advisory_digest`),
detects bundled executable scripts and frontmatter hooks, and deduplicates
multi-host mirror directories (`.agents/skills/`, `.claude/skills/`,
`.cursor/skills/`, `.agent/skills/`).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

from factory.contracts import (
    DESIGN_STAGES,
    ROLE_HINTS,
    SKILL_CATEGORIES,
    ModuleRecord,
    PermissionBoundary,
    SkillUnitSpec,
)

from hyodo.events import content_digest
from hyodo.provenance import clean_git_env
from hyodo.skills import parse_skill_rules

_FRONTMATTER_RE = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*\r?\n", re.DOTALL)

_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "quality": ("qa", "test-browser", "browse", "verify", "impeccable", "gatekeep"),
    "security": ("security", "careful", "guard", "freeze", "audit-security", "cloudflare"),
    "simplification": (
        "ponytail",
        "yagni",
        "simplify",
        "karpathy",
        "caveman",
        "improve",
        "correct",
    ),
    "design": ("design", "taste", "ui-ux", "hallmark", "palette", "typography", "unslop"),
    "craft": ("motion", "animation", "kowalski", "frontend-design", "component"),
    "orchestration": (
        "swarm",
        "arena",
        "ship",
        "retro",
        "office-hours",
        "poteto-mode",
        "using-superpowers",
    ),
    "knowledge": ("graphify", "understand", "context", "how", "why", "zoom-out"),
    "research": ("find-skills", "last30days", "research", "discover"),
    "evaluation": ("jev", "skill-eval", "interrogate", "benchmark"),
    "creative": ("anatomy", "diagram", "hyperframes", "visual", "slides", "banner"),
    "office": ("document-release", "prd", "to-prd", "to-issues"),
    "engineering": (
        "tdd",
        "test-driven-development",
        "grill",
        "diagnose",
        "architect",
        "plan",
        "debug",
        "systematic-debugging",
        "review",
        "brainstorming",
    ),
}

_HOST_MIRROR_PREFIXES: dict[str, str] = {
    ".agents/skills/": "codex",
    ".agent/skills/": "antigravity",
    ".claude/skills/": "claude-code",
    ".cursor/skills/": "cursor",
    ".gemini/skills/": "antigravity",
    "cli/assets/skills/": "cli-mirror",
}


def _git_head_sha(path: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
            env=clean_git_env(),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = proc.stdout.strip()
    return sha if proc.returncode == 0 and len(sha) in (40, 64) else None


def detect_repo_license(root: Path) -> str:
    """Detect SPDX license identifier from manifests or LICENSE file."""
    for rel in (
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".antigravity-plugin/plugin.json",
        "plugin.json",
        "package.json",
        "cli/package.json",
    ):
        cand = root / rel
        if cand.is_file() and not cand.is_symlink():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("license"), str):
                    return data["license"].strip()
            except (OSError, json.JSONDecodeError):
                pass
    for lic_name in ("LICENSE", "LICENSE.md", "LICENSE.txt"):
        lic_path = root / lic_name
        if lic_path.is_file() and not lic_path.is_symlink():
            try:
                head = lic_path.read_text(encoding="utf-8", errors="replace")[:1000]
                if "MIT License" in head or "Permission is hereby granted, free of charge" in head:
                    return "MIT"
                if "Apache License" in head and "Version 2.0" in head:
                    return "Apache-2.0"
                if "BSD" in head:
                    return "BSD"
            except OSError:
                pass
    return "UNOBSERVED"


def detect_repo_version(root: Path) -> str:
    """Detect repository version from plugin manifests, package.json, or pyproject.toml."""
    for rel in (
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".antigravity-plugin/plugin.json",
        "plugin.json",
        "package.json",
        "cli/package.json",
    ):
        cand = root / rel
        if cand.is_file() and not cand.is_symlink():
            try:
                data = json.loads(cand.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("version"), str):
                    return data["version"].strip()
            except (OSError, json.JSONDecodeError):
                pass
    pyproject = root / "pyproject.toml"
    if pyproject.is_file() and not pyproject.is_symlink():
        try:
            text = pyproject.read_text(encoding="utf-8", errors="replace")
            m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if m:
                return m.group(1).strip()
        except OSError:
            pass
    return "0.1.0"


def detect_repo_supported_hosts(root: Path) -> list[str]:
    """Detect which coding hosts a repository explicitly supports via manifests or folders."""
    hosts: list[str] = ["claude-code", "codex", "cursor", "antigravity"]
    explicit: list[str] = []
    if (root / ".claude-plugin" / "plugin.json").is_file() or (root / ".claude").is_dir():
        explicit.append("claude-code")
    if (root / ".codex-plugin" / "plugin.json").is_file() or (root / ".agents").is_dir():
        explicit.append("codex")
    if (root / ".cursor-plugin" / "plugin.json").is_file() or (root / ".cursor").is_dir():
        explicit.append("cursor")
    if (
        (root / ".antigravity-plugin" / "plugin.json").is_file()
        or (root / ".agent").is_dir()
        or (root / ".gemini").is_dir()
    ):
        explicit.append("antigravity")
    return sorted(set(explicit or hosts))


def _parse_simple_frontmatter(text: str) -> dict[str, Any]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    block = match.group(1)
    meta: dict[str, Any] = {}
    frontmatter_hooks: list[str] = []
    in_hooks = False
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")) and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip().strip("\"'")
            in_hooks = key == "hooks"
            if key == "hooks":
                continue
            if val.startswith("[") and val.endswith("]"):
                items = [
                    item.strip().strip("\"'")
                    for item in val[1:-1].split(",")
                    if item.strip().strip("\"'")
                ]
                meta[key] = items
            else:
                meta[key] = val
        elif in_hooks:
            if line.endswith(":") and not line.startswith("-"):
                hook_event = line[:-1].strip()
                if hook_event and hook_event not in ("hooks", "type", "command"):
                    frontmatter_hooks.append(f"frontmatter-hook:{hook_event}")
            elif line.startswith("command:"):
                cmd_val = line.partition(":")[2].strip().strip("\"'")
                if "exit 0" in cmd_val and ("not found" in cmd_val or "missing" in cmd_val):
                    meta["hook_silent_zero_fallback"] = True
        elif raw_line.startswith((" ", "\t")) and ":" in line:
            sub_k, _, sub_v = line.partition(":")
            if sub_k.strip().lower() == "version" and "version" not in meta:
                meta["version"] = sub_v.strip().strip("\"'")
    if frontmatter_hooks:
        meta["frontmatter_hooks"] = frontmatter_hooks
    return meta


def _infer_category(name: str, description: str, frontmatter: dict[str, Any]) -> str:
    explicit = str(frontmatter.get("category", "")).lower()
    if explicit in SKILL_CATEGORIES:
        return explicit
    haystack = f"{name} {description}".lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            return category
    return "engineering"


def _infer_role_hint(name: str, category: str, frontmatter: dict[str, Any]) -> str:
    explicit = str(frontmatter.get("role_hint", "")).lower()
    if explicit in ROLE_HINTS:
        return explicit
    lowered = name.lower()
    if any(
        tok in lowered
        for tok in (
            "qa",
            "review",
            "interrogate",
            "verify",
            "impeccable",
            "security",
            "audit",
            "doctor",
            "check",
            "guard",
        )
    ):
        return "verifier"
    if any(
        tok in lowered
        for tok in ("router", "poteto-mode", "find-skills", "triage", "using-superpowers")
    ):
        return "router"
    if category == "evaluation":
        return "observer"
    return "builder"


def _infer_design_stage(name: str, category: str, frontmatter: dict[str, Any]) -> str | None:
    explicit = str(frontmatter.get("design_stage", "")).lower()
    if explicit in DESIGN_STAGES:
        return explicit
    if category == "design":
        return "architect"
    if category == "craft":
        return "craft"
    if category == "quality" and any(
        k in name.lower() for k in ("qa", "impeccable", "hallmark", "design-review")
    ):
        return "gatekeep"
    return None


def _ensure_safe_subpath(root: Path, candidate: Path) -> str:
    """Ensure *candidate* is a regular file inside *root* with no symlink/path escape."""
    root_resolved = root.resolve(strict=True)
    if candidate.is_symlink():
        raise ValueError(f"path_escape: symlinked skill file refused ({candidate})")
    resolved = candidate.resolve(strict=True)
    try:
        rel = resolved.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path_escape: {candidate} escapes {root_resolved}") from exc
    if ".." in rel.parts:
        raise ValueError(f"path_escape: '..' in {rel}")
    return str(rel).replace("\\", "/")


def _discover_skill_scripts(module_root: Path, skill_dir: Path) -> tuple[str, ...]:
    """Find executable scripts (`scripts/*.py`, `scripts/*.sh`, `scripts/*.mjs`) inside *skill_dir*."""
    scripts_dir = skill_dir / "scripts"
    if not scripts_dir.is_dir() or scripts_dir.is_symlink():
        return ()
    found: list[str] = []
    for ext in ("*.py", "*.sh", "*.mjs"):
        for cand in sorted(scripts_dir.glob(ext)):
            if cand.is_symlink() or not cand.is_file():
                continue
            try:
                found.append(_ensure_safe_subpath(module_root, cand))
            except ValueError:
                continue
    return tuple(found)


def parse_skill_unit(
    module_root: Path,
    module_id: str,
    skill_file: Path,
    *,
    adapter_name: str = "agent-skills",
    extra_boundary: PermissionBoundary | None = None,
    supported_hosts: tuple[str, ...] = (),
) -> SkillUnitSpec:
    """Parse one `SKILL.md` / `skill.md` / `AGENTS.md` file into a `SkillUnitSpec` without retaining full body in memory."""
    rel_path = _ensure_safe_subpath(module_root, skill_file)
    raw_bytes = skill_file.read_bytes()
    sha256_hex = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8", errors="replace")
    frontmatter = _parse_simple_frontmatter(text)

    if skill_file.parent != module_root:
        sub_name = skill_file.parent.name.strip().lower().replace(" ", "-")
    elif skill_file.name.lower() == "agents.md" and (
        (module_root / "SKILL.md").is_file() or (module_root / "skill.md").is_file()
    ):
        sub_name = "agents"
    else:
        raw_name = str(frontmatter.get("name") or "core").strip().lower().replace(" ", "-")
        sub_name = "core" if raw_name == module_id.lower() else raw_name
    skill_id = f"{module_id}/{sub_name}"

    description = str(frontmatter.get("description") or "").strip()
    if not description or description in (">-", "|"):
        for line in text.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith(("#", "---", "<")):
                description = stripped[:160]
                break

    parsed_rules = parse_skill_rules(skill_id, text)
    mechanical = tuple(rule.text for rule in parsed_rules if rule.compiled is not None)
    advisory_digest = content_digest(text)

    category = _infer_category(sub_name, description, frontmatter)
    role_hint = _infer_role_hint(sub_name, category, frontmatter)
    design_stage = _infer_design_stage(sub_name, category, frontmatter)

    deps_raw = frontmatter.get("dependencies", [])
    deps = tuple(deps_raw) if isinstance(deps_raw, list) else ()
    conflicts_raw = frontmatter.get("conflicts_with", [])
    conflicts = tuple(conflicts_raw) if isinstance(conflicts_raw, list) else ()
    caps_raw = frontmatter.get("capabilities", [])
    caps_list = (
        list(caps_raw)
        if isinstance(caps_raw, list) and caps_raw
        else [category, sub_name, role_hint]
    )
    if frontmatter.get("hook_silent_zero_fallback"):
        caps_list.append("hook_silent_zero_fallback")
    caps = tuple(caps_list)

    scripts = _discover_skill_scripts(module_root, skill_file.parent)
    fm_hooks = tuple(frontmatter.get("frontmatter_hooks", ()))
    disable_model = str(frontmatter.get("disable-model-invocation", "")).lower() == "true"

    fm_write = frontmatter.get("filesystem_write")
    allow_write = (
        str(fm_write).lower() == "true" if fm_write is not None else (role_hint == "builder")
    )
    fm_exec = frontmatter.get("subprocess_exec")
    allow_exec = (
        str(fm_exec).lower() == "true"
        if fm_exec is not None
        else (bool(scripts) or role_hint in ("builder", "verifier"))
    )

    base_boundary = extra_boundary or PermissionBoundary(
        allowed_tools=("Read", "Grep", "Glob", "Bash")
        if role_hint == "builder"
        else ("Read", "Grep", "Glob"),
        allowed_paths=(str(module_root),),
        hooks=fm_hooks,
        filesystem_read=True,
        filesystem_write=allow_write,
        subprocess_exec=allow_exec,
        network_access=False,
        browser_automation=("browse" in sub_name or "qa" in sub_name),
        execution_authority=False,
    )
    if fm_hooks and extra_boundary is not None:
        merged_hooks = tuple(dict.fromkeys([*extra_boundary.hooks, *fm_hooks]))
        base_boundary = replace(extra_boundary, hooks=merged_hooks)

    hosts = supported_hosts or tuple(detect_repo_supported_hosts(module_root))

    return SkillUnitSpec(
        skill_id=skill_id,
        name=sub_name,
        module_id=module_id,
        category=category,
        adapter=adapter_name,
        relative_path=rel_path,
        content_sha256=sha256_hex,
        enabled=True,
        description=description,
        role_hint=role_hint,
        design_stage=design_stage,
        dependencies=deps,
        conflicts_with=conflicts,
        capabilities=caps,
        mechanical_rules=mechanical,
        advisory_digest=advisory_digest,
        executable_scripts=scripts,
        supported_hosts=hosts,
        disable_model_invocation=disable_model,
        boundary=base_boundary,
    )


def _is_host_mirror_path(rel_posix: str) -> str | None:
    for prefix, host_tag in _HOST_MIRROR_PREFIXES.items():
        if rel_posix.startswith(prefix):
            return host_tag
    return None


def discover_skill_files(module_root: Path) -> list[Path]:
    """Find standard skill files inside *module_root* in deterministic canonical order.

    Supports both `SKILL.md` and lowercase `skill.md` (e.g., `graphify/skill.md`),
    plus `.claude/skills/*/SKILL.md` (e.g., `ui-ux-pro-max-skill`), while
    deduplicating multi-host mirrors (`.agents/skills/<name>`, `.cursor/skills/<name>`,
    `.claude/skills/<name>`, `cli/assets/skills/<name>`) when a repository ships
    mirrored copies of the same skill for multiple hosts (e.g., `impeccable`).
    """
    candidates: list[Path] = []
    seen_resolved: set[Path] = set()
    canonical_names_seen: dict[str, str] = {}

    # Ordered from canonical source locations to host-specific mirror locations
    search_tiers: tuple[tuple[str, bool], ...] = (
        ("skills/*/SKILL.md", False),
        ("skills/*/skill.md", False),
        ("skills/*/*/SKILL.md", False),
        ("skills/*/*/skill.md", False),
        ("*/SKILL.md", False),
        ("*/skill.md", False),
        (".agents/skills/*/SKILL.md", True),
        (".agent/skills/*/SKILL.md", True),
        (".claude/skills/*/SKILL.md", True),
        (".cursor/skills/*/SKILL.md", True),
        (".gemini/skills/*/SKILL.md", True),
        ("SKILL.md", False),
        ("skill.md", False),
        ("AGENTS.md", False),
    )

    for pattern, is_mirror_tier in search_tiers:
        for path in sorted(module_root.glob(pattern)):
            if path.is_symlink() or not path.is_file():
                continue
            rel_parts = path.relative_to(module_root).parts
            if "deprecated" in rel_parts:
                continue
            # Skip hidden folders unless they are one of the known host skill directories
            if (
                rel_parts
                and rel_parts[0].startswith(".")
                and rel_parts[0]
                not in (
                    ".agents",
                    ".agent",
                    ".claude",
                    ".cursor",
                    ".gemini",
                )
            ):
                continue
            resolved = path.resolve()
            if resolved in seen_resolved:
                continue

            sub_key = (
                path.parent.name.strip().lower()
                if path.parent != module_root
                else path.name.lower()
            )
            if is_mirror_tier and sub_key in canonical_names_seen:
                # Already discovered canonical or higher-priority host copy of this skill
                continue

            seen_resolved.add(resolved)
            canonical_names_seen[sub_key] = str(path.relative_to(module_root))
            candidates.append(path)

    if not candidates and (module_root / "README.md").is_file():
        readme = module_root / "README.md"
        if not readme.is_symlink():
            candidates.append(readme)
    return candidates


def load_agent_skills_module(
    source_path: Path,
    *,
    module_id: str | None = None,
    version: str | None = None,
) -> ModuleRecord:
    """Discover and build a `ModuleRecord` from any Agent Skills directory."""
    root = source_path.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"module source must be a directory: {source_path}")
    mod_id = (module_id or root.name).strip().lower().replace(" ", "-")
    skill_files = discover_skill_files(root)
    if not skill_files:
        raise ValueError(f"no SKILL.md, AGENTS.md, or README.md found in {root}")

    resolved_version = version or detect_repo_version(root)
    license_spdx = detect_repo_license(root)
    hosts = tuple(detect_repo_supported_hosts(root))

    skills: dict[str, SkillUnitSpec] = {}
    tree_hasher = hashlib.sha256()
    for sfile in skill_files:
        unit = parse_skill_unit(
            root,
            mod_id,
            sfile,
            adapter_name="agent-skills",
            supported_hosts=hosts,
        )
        if unit.skill_id in skills:
            raise ValueError(f"duplicate_skill_id: {unit.skill_id}")
        skills[unit.skill_id] = unit
        tree_hasher.update(f"{unit.skill_id}:{unit.content_sha256}\n".encode())

    return ModuleRecord(
        module_id=mod_id,
        source_path=str(root),
        adapter="agent-skills",
        version=resolved_version,
        git_commit=_git_head_sha(root),
        tree_sha256=tree_hasher.hexdigest(),
        enabled=True,
        license_spdx=license_spdx,
        skills=skills,
    )


def disclose_skill_body(module: ModuleRecord, skill_id: str) -> str:
    """Progressive Disclosure: read the full markdown body ONLY when the skill is explicitly activated."""
    unit = module.skills.get(skill_id)
    if unit is None:
        raise KeyError(f"unknown skill_id: {skill_id}")
    if not module.enabled or not unit.enabled:
        raise PermissionError(f"skill {skill_id} is disabled and cannot be disclosed")
    root = Path(module.source_path).resolve(strict=True)
    target = root / unit.relative_path
    _ensure_safe_subpath(root, target)
    raw = target.read_bytes()
    if hashlib.sha256(raw).hexdigest() != unit.content_sha256:
        raise RuntimeError(f"MID_RUN_SKILL_DRIFT: {skill_id} content hash changed since lock")
    return raw.decode("utf-8", errors="replace")
