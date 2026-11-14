"""Phase 2.0 — Module Contract for the HyoDo Universal Skill Harness.

Defines host-side contracts for hot-swappable skills, plugins, and external
evaluators. HyoDo Core (`hyodo/`) remains completely untouched when new
skills or adapters are added.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FACTORY_REGISTRY_SCHEMA = "hyodo.factory-registry/v1"
FACTORY_LOCK_SCHEMA = "hyodo.factory-lock/v1"
FACTORY_PROFILE_SCHEMA = "hyodo.factory-profile/v1"
TRUST_STATE_SCHEMA = "hyodo.factory-trust-state/v1"
HOST_TASTE_SCHEMA = "hyodo.host-taste/v1"
# An approval *request* built by the factory for the host's own approval
# authority. HyoDo never issues the approval itself.
FACTORY_APPROVAL_REQUEST_SCHEMA = "hyodo.factory-approval-request/v1"
HOST_TASTE_REL_PATH = Path(".hyodo") / "factory" / "host_taste.json"

SKILL_CATEGORIES = (
    "engineering",
    "orchestration",
    "simplification",
    "design",
    "craft",
    "quality",
    "security",
    "knowledge",
    "research",
    "office",
    "creative",
    "evaluation",
)

DESIGN_STAGES = ("architect", "craft", "gatekeep")

ADAPTER_KINDS = ("agent-skills", "claude-plugin", "external-evaluator")

ROLE_HINTS = ("builder", "verifier", "observer", "router")

EVAL_VERDICTS = ("HELPED", "NEUTRAL", "HURT", "INCONCLUSIVE")

CAPABILITY_STATES = (
    "VERIFIED",
    "UNVERIFIED",
    "MISSING",
    "DEGRADED",
    "REDUNDANT",
    "UNKNOWN",
)

GAP_ROOT_CAUSES = (
    "NONE",
    "CAPABILITY_MISSING",
    "WIRING_DISCONNECTED",
    "VERIFICATION_MISSING",
    "ENVIRONMENT_OR_SYNTAX_DEGRADED",
    "DUPLICATE_SLOT",
)


def utc_now_iso() -> str:
    """Return the current UTC time as an ISO-8601 `...Z` string (second precision)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


TRUST_STAGES = (
    "DISCOVER",
    "VERIFY",
    "MANUAL",
    "SHADOW",
    "TRUSTED",
    "AUTO_RUN",
)


@dataclass(frozen=True)
class PermissionBoundary:
    """Explicit runtime permission boundary for a module or skill.

    Never grants merge/deploy authority; `execution_authority` is always False.
    `factory/runner.py` enforces `subprocess_exec` (pre-exec gate) and
    `filesystem_write=False` inside the workspace only (POSIX write bits plus
    snapshot rollback). `network_access=False`, `browser_automation=False` and
    the `allowed_paths` / `allowed_tools` allowlists are NOT enforced by the
    runner; they are advisory and reported as `UNENFORCED` (see
    `boundary_enforcement_report`).
    """

    allowed_tools: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    hooks: tuple[str, ...] = ()
    mcp_servers: tuple[str, ...] = ()
    filesystem_read: bool = True
    filesystem_write: bool = False
    subprocess_exec: bool = False
    network_access: bool = False
    browser_automation: bool = False
    execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.execution_authority is not False:
            raise ValueError(
                "PERMISSION_BOUNDARY_INVALID: external skills and evaluators may never claim execution_authority=True"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed_tools": list(self.allowed_tools),
            "allowed_paths": list(self.allowed_paths),
            "hooks": list(self.hooks),
            "mcp_servers": list(self.mcp_servers),
            "filesystem_read": self.filesystem_read,
            "filesystem_write": self.filesystem_write,
            "subprocess_exec": self.subprocess_exec,
            "network_access": self.network_access,
            "browser_automation": self.browser_automation,
            "execution_authority": self.execution_authority,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> PermissionBoundary:
        return cls(
            allowed_tools=tuple(raw.get("allowed_tools", ())),
            allowed_paths=tuple(raw.get("allowed_paths", ())),
            hooks=tuple(raw.get("hooks", ())),
            mcp_servers=tuple(raw.get("mcp_servers", ())),
            filesystem_read=bool(raw.get("filesystem_read", True)),
            filesystem_write=bool(raw.get("filesystem_write", False)),
            subprocess_exec=bool(raw.get("subprocess_exec", False)),
            network_access=bool(raw.get("network_access", False)),
            browser_automation=bool(raw.get("browser_automation", False)),
            execution_authority=bool(raw.get("execution_authority", False)),
        )


@dataclass(frozen=True)
class SkillUnitSpec:
    """One independently toggleable skill inside a module (e.g. `gstack/qa`).

    Separates mechanical rules (`require file:`, `forbid pattern:`, `ruff:`)
    from semantic/advisory guidance (`advisory_digest`), supporting
    Progressive Disclosure so full markdown bodies are loaded only on activation.
    """

    skill_id: str
    name: str
    module_id: str
    category: str
    adapter: str
    relative_path: str
    content_sha256: str
    enabled: bool = True
    description: str = ""
    role_hint: str = "builder"
    design_stage: str | None = None
    dependencies: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    mechanical_rules: tuple[str, ...] = ()
    advisory_digest: str | None = None
    executable_scripts: tuple[str, ...] = ()
    supported_hosts: tuple[str, ...] = ()
    disable_model_invocation: bool = False
    boundary: PermissionBoundary = field(default_factory=PermissionBoundary)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["dependencies"] = list(self.dependencies)
        data["conflicts_with"] = list(self.conflicts_with)
        data["capabilities"] = list(self.capabilities)
        data["mechanical_rules"] = list(self.mechanical_rules)
        data["executable_scripts"] = list(self.executable_scripts)
        data["supported_hosts"] = list(self.supported_hosts)
        data["boundary"] = self.boundary.to_dict()
        return data

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> SkillUnitSpec:
        boundary_raw = raw.get("boundary")
        return cls(
            skill_id=str(raw["skill_id"]),
            name=str(raw["name"]),
            module_id=str(raw["module_id"]),
            category=str(raw.get("category", "engineering")),
            adapter=str(raw.get("adapter", "agent-skills")),
            relative_path=str(raw["relative_path"]),
            content_sha256=str(raw["content_sha256"]),
            enabled=bool(raw.get("enabled", True)),
            description=str(raw.get("description", "")),
            role_hint=str(raw.get("role_hint", "builder")),
            design_stage=raw.get("design_stage"),
            dependencies=tuple(raw.get("dependencies", ())),
            conflicts_with=tuple(raw.get("conflicts_with", ())),
            capabilities=tuple(raw.get("capabilities", ())),
            mechanical_rules=tuple(raw.get("mechanical_rules", ())),
            advisory_digest=raw.get("advisory_digest"),
            executable_scripts=tuple(raw.get("executable_scripts", ())),
            supported_hosts=tuple(raw.get("supported_hosts", ())),
            disable_model_invocation=bool(raw.get("disable_model_invocation", False)),
            boundary=PermissionBoundary.from_dict(boundary_raw)
            if isinstance(boundary_raw, dict)
            else PermissionBoundary(),
        )


@dataclass(frozen=True)
class ModuleRecord:
    """A registered external skill package, plugin bundle, or evaluator."""

    module_id: str
    source_path: str
    adapter: str
    version: str
    git_commit: str | None
    tree_sha256: str
    enabled: bool
    skills: dict[str, SkillUnitSpec]
    license_spdx: str = "UNOBSERVED"
    installed_at: str = field(default_factory=utc_now_iso)
    # Observed origin at add/update time: source path, git remote/commit/dirty
    # state, and the whole-module file tree digest. Empty for locks written
    # before origin recording existed (reported by `doctor`).
    origin: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_id": self.module_id,
            "source_path": self.source_path,
            "adapter": self.adapter,
            "version": self.version,
            "git_commit": self.git_commit,
            "tree_sha256": self.tree_sha256,
            "enabled": self.enabled,
            "license_spdx": self.license_spdx,
            "installed_at": self.installed_at,
            "origin": dict(self.origin),
            "skills": {k: v.to_dict() for k, v in sorted(self.skills.items())},
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ModuleRecord:
        skills_raw = raw.get("skills", {})
        skills = {
            k: SkillUnitSpec.from_dict(v) for k, v in skills_raw.items() if isinstance(v, dict)
        }
        return cls(
            module_id=str(raw["module_id"]),
            source_path=str(raw["source_path"]),
            adapter=str(raw.get("adapter", "agent-skills")),
            version=str(raw.get("version", "0.1.0")),
            git_commit=raw.get("git_commit"),
            tree_sha256=str(raw["tree_sha256"]),
            enabled=bool(raw.get("enabled", True)),
            license_spdx=str(raw.get("license_spdx", "UNOBSERVED")),
            # A missing install time is unknown, not "now".
            installed_at=str(raw.get("installed_at", "UNOBSERVED")),
            origin=dict(raw["origin"]) if isinstance(raw.get("origin"), dict) else {},
            skills=skills,
        )


@dataclass(frozen=True)
class ProfileSpec:
    """Task profile selecting active categories, host taste rules, and resolving orchestrator conflicts."""

    name: str
    description: str
    active_categories: tuple[str, ...]
    preferred_skills: tuple[str, ...] = ()
    excluded_skills: tuple[str, ...] = ()
    single_orchestrator: bool = True
    require_independent_verifier: bool = True
    personal_taste_rules: tuple[str, ...] = ()
    inferred_taste_hypotheses: tuple[str, ...] = ()
    domain_taste_focus: tuple[str, ...] = ()


def recommend_skill_lifecycle_action(
    verdict: str,
    virtue_signals: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Map a `hyodo.skill-eval/v1` verdict + 6-virtue signals to a non-authoritative recommendation.

    Never expands permissions or removes safety fences.
    """
    normalized = verdict if verdict in EVAL_VERDICTS else "INCONCLUSIVE"
    action_map = {
        "HELPED": "KEEP_ENABLED",
        "NEUTRAL": "OPTIONAL_BY_COST",
        "HURT": "CANDIDATE_DISABLE",
        "INCONCLUSIVE": "NEEDS_MORE_PAIRED_TRIALS",
    }
    virtues = dict(virtue_signals or {})
    return {
        "verdict": normalized,
        "recommended_action": action_map[normalized],
        "virtue_signals": virtues,
        "authority_expanded": False,
        "safety_fence_modified": False,
    }
