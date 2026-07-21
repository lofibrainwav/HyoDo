"""Local policy gate for agent events (FDE Evidence Spine).

Policy is loadable from ``.hyodo/policy.toml`` (schema ``hyodo.policy/v1``).
Missing or malformed policy is **unobserved**, never silent ALLOW.

HyoDo emits a decision object; the agent runtime must enforce DENY.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]

POLICY_SCHEMA_ID = "hyodo.policy/v1"
POLICY_RELATIVE_PATH = Path(".hyodo") / "policy.toml"


class PolicyConfigError(ValueError):
    """Raised when policy.toml exists but fails structural validation."""


@dataclass(frozen=True)
class PolicyConfig:
    """Parsed agent policy."""

    schema: str
    max_steps: int | None
    allowed_tools: tuple[str, ...] | None  # None = no allowlist restriction
    blocked_path_globs: tuple[str, ...]

    @property
    def allowlist_active(self) -> bool:
        """True when ``allowed_tools`` is set (including empty = deny all tools)."""
        return self.allowed_tools is not None


@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating one event against a policy."""

    decision: str  # ALLOW | DENY | ASK | UNOBSERVED
    rule_id: str | None
    reason: str | None

    def as_dict(self) -> dict[str, Any]:
        """Serialize the decision for ledger stamping and JSON CLI output."""
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
        }


def load_policy_config(path: Path) -> PolicyConfig:
    """Load and validate a policy.toml. Raises PolicyConfigError on bad shape."""
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PolicyConfigError(f"{path}: unreadable ({exc})") from exc
    try:
        raw = tomllib.loads(raw_text)
    except Exception as exc:  # tomllib.TOMLDecodeError
        raise PolicyConfigError(f"{path}: invalid TOML ({exc})") from exc
    if not isinstance(raw, dict):
        raise PolicyConfigError(f"{path}: root must be a table")

    schema = raw.get("schema")
    if schema != POLICY_SCHEMA_ID:
        raise PolicyConfigError(
            f"{path}: unsupported schema {schema!r}; expected {POLICY_SCHEMA_ID!r}"
        )

    max_steps = raw.get("max_steps")
    if max_steps is not None and (
        not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 0
    ):
        raise PolicyConfigError(f"{path}: max_steps must be a non-negative integer")

    allowed_tools: tuple[str, ...] | None
    if "allowed_tools" not in raw:
        allowed_tools = None
    else:
        tools = raw["allowed_tools"]
        if not isinstance(tools, list) or not all(isinstance(t, str) and t for t in tools):
            raise PolicyConfigError(f"{path}: allowed_tools must be a list of non-empty strings")
        # Empty list = allowlist active with zero tools → all tool events DENY.
        allowed_tools = tuple(tools)

    blocked: tuple[str, ...] = ()
    if "blocked_path_globs" in raw:
        globs = raw["blocked_path_globs"]
        if not isinstance(globs, list) or not all(isinstance(g, str) and g for g in globs):
            raise PolicyConfigError(
                f"{path}: blocked_path_globs must be a list of non-empty strings"
            )
        blocked = tuple(globs)

    return PolicyConfig(
        schema=schema,
        max_steps=max_steps,
        allowed_tools=allowed_tools,
        blocked_path_globs=blocked,
    )


def try_load_policy(path: Path) -> tuple[PolicyConfig | None, str | None]:
    """Load policy without raising. Returns ``(config, error_code)``."""
    if not path.exists():
        return None, "policy_missing"
    try:
        return load_policy_config(path), None
    except PolicyConfigError:
        return None, "policy_invalid"


def _path_blocked(path: str, globs: tuple[str, ...]) -> str | None:
    """Return matching glob if *path* is blocked, else None."""
    # Normalize for matching: strip file:// and collapse redundant separators lightly.
    candidate = path.replace("\\", "/")
    for pattern in globs:
        if fnmatch.fnmatch(candidate, pattern):
            return pattern
        # Also match basename-only patterns against full path segments.
        if fnmatch.fnmatch(candidate.split("/")[-1], pattern):
            return pattern
    return None


def evaluate_policy(event: dict[str, Any], policy: PolicyConfig) -> PolicyDecision:
    """Evaluate a **validated** event against *policy*. Never returns silent pass on tools."""
    step = event.get("step_index")
    if (
        policy.max_steps is not None
        and isinstance(step, int)
        and not isinstance(step, bool)
        and step > policy.max_steps
    ):
        return PolicyDecision(
            decision="DENY",
            rule_id="max_steps",
            reason=f"step_index {step} exceeds max_steps {policy.max_steps}",
        )

    kind = event.get("kind")
    tool = event.get("tool") if isinstance(event.get("tool"), dict) else {}
    tool_name = tool.get("name") if isinstance(tool, dict) else None
    paths = tool.get("paths") if isinstance(tool, dict) else None
    if not isinstance(paths, list):
        paths = []

    if kind in ("tool_call", "tool_result") and policy.allowlist_active:
        allowed = policy.allowed_tools or ()
        if not isinstance(tool_name, str) or tool_name not in allowed:
            return PolicyDecision(
                decision="DENY",
                rule_id="tool_not_allowed",
                reason=f"tool {tool_name!r} not in allowed_tools",
            )

    if policy.blocked_path_globs and paths:
        for p in paths:
            if not isinstance(p, str):
                continue
            matched = _path_blocked(p, policy.blocked_path_globs)
            if matched is not None:
                return PolicyDecision(
                    decision="DENY",
                    rule_id="data_boundary",
                    reason=f"path {p!r} matched blocked glob {matched!r}",
                )

    return PolicyDecision(decision="ALLOW", rule_id=None, reason=None)


def apply_decision_to_event(event: dict[str, Any], decision: PolicyDecision) -> dict[str, Any]:
    """Return a shallow-copied event with ``policy`` set from *decision*."""
    out = dict(event)
    out["policy"] = decision.as_dict()
    return out
