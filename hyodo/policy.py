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
    #: Opt-in strict mode. ``blocked_path_globs`` can only inspect paths the caller
    #: *declared*; a tool event with ``paths: []`` sails past it. Turning this on makes
    #: that silence UNOBSERVED instead of ALLOW. It is off by default because plenty of
    #: legitimate tools (search, http, …) touch no paths, and flagging all of them would
    #: push operators to delete blocked_path_globs entirely — a worse outcome.
    require_declared_paths: bool = False

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
        """Serialize the decision for ledger stamping and JSON CLI output.

        ``evaluated_by`` marks this as a *measured* decision. A PolicyDecision can only
        come from :func:`evaluate_policy`, so its presence in the ledger is proof HyoDo
        ran the policy rather than trusting the caller.
        """
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "evaluated_by": POLICY_SCHEMA_ID,
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

    require_declared_paths = raw.get("require_declared_paths", False)
    if not isinstance(require_declared_paths, bool):
        raise PolicyConfigError(f"{path}: require_declared_paths must be a boolean")

    return PolicyConfig(
        schema=schema,
        max_steps=max_steps,
        allowed_tools=allowed_tools,
        blocked_path_globs=blocked,
        require_declared_paths=require_declared_paths,
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
    if candidate.startswith("file://"):
        candidate = candidate[len("file://") :]
    while candidate.startswith("./"):
        candidate = candidate[2:]
    for pattern in globs:
        if fnmatch.fnmatch(candidate, pattern):
            return pattern
        # fnmatch has no "**" concept: it expands to ".*", so "**/.env" needs a literal
        # slash and therefore misses a root-level ".env". Retry against the tail so the
        # documented recursive pattern also covers depth zero.
        if pattern.startswith("**/") and fnmatch.fnmatch(candidate, pattern[3:]):
            return pattern
        # Also match basename-only patterns against full path segments.
        if fnmatch.fnmatch(candidate.split("/")[-1], pattern):
            return pattern
    return None


def evaluate_policy(
    event: dict[str, Any],
    policy: PolicyConfig,
    *,
    observed_steps: int | None = None,
) -> PolicyDecision:
    """Evaluate a **validated** event against *policy*. Never returns silent pass on tools.

    ``observed_steps`` is how many events this run already has **in the ledger**. It is
    the only authoritative step count: ``event["step_index"]`` is self-reported by the
    caller and a caller that keeps sending ``step_index: 0`` would otherwise run forever.
    When ``max_steps`` is configured but the ledger was not observed, the result is
    ``UNOBSERVED`` rather than ``ALLOW`` — unenforceable is not permitted.
    """
    if (
        policy.max_steps is not None
        and observed_steps is not None
        and observed_steps >= policy.max_steps
    ):
        return PolicyDecision(
            decision="DENY",
            rule_id="max_steps",
            reason=(
                f"run already has {observed_steps} recorded step(s); "
                f"max_steps {policy.max_steps} would be exceeded"
            ),
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

    if (
        policy.require_declared_paths
        and policy.blocked_path_globs
        and kind in ("tool_call", "tool_result")
        and not paths
    ):
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id="data_boundary_undeclared",
            reason="tool declared no paths; blocked_path_globs cannot be checked",
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

    if policy.max_steps is not None and observed_steps is None:
        # A step budget exists but we could not count the ledger. Refusing to call
        # this ALLOW is the whole point: unobserved is not healthy.
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id="max_steps",
            reason="ledger step count unavailable; max_steps cannot be enforced",
        )

    return PolicyDecision(decision="ALLOW", rule_id=None, reason=None)


def apply_decision_to_event(event: dict[str, Any], decision: PolicyDecision) -> dict[str, Any]:
    """Return a shallow-copied event with ``policy`` set from *decision*.

    This is the **only** path that may write a measured decision: it stamps
    ``evaluated_by`` so readers can tell a HyoDo-computed decision apart from one a
    caller merely asserted (which validate_event parks under ``policy.claimed``).
    """
    out = dict(event)
    stamped = decision.as_dict()
    claimed = event.get("policy")
    if isinstance(claimed, dict) and "claimed" in claimed:
        stamped["claimed"] = claimed["claimed"]
    out["policy"] = stamped
    return out
