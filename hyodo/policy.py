"""Local policy gate for agent events (FDE Evidence Spine).

Policy is loadable from ``.hyodo/policy.toml`` (schema ``hyodo.policy/v1``).
Missing or malformed policy is **unobserved**, never silent ALLOW.

HyoDo emits a decision object; the agent runtime must enforce DENY.

Schema ``hyodo.policy/v1`` follows an optional-fields-only convention: every
field added to this schema id defaults to a value that preserves prior
behavior when absent. The Phase 1-A ``web``, ``ask_tools``, ``ask_threshold``,
and ``trust`` fields follow that contract.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from hyodo.events import credential_shaped_path
from hyodo.policy_trust import effective_trust_level, load_policy_trust

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]  # pyright: ignore[reportMissingImports]

POLICY_SCHEMA_ID = "hyodo.policy/v1"
POLICY_RELATIVE_PATH = Path(".hyodo") / "policy.toml"
_BUILTIN_WEB_TOOLS = frozenset({"web_fetch", "browser", "http", "fetch", "WebFetch", "WebSearch"})
_SAFE_HTTP_METHODS = frozenset({"GET", "HEAD"})


class PolicyConfigError(ValueError):
    """Raised when policy.toml exists but fails structural validation."""


@dataclass(frozen=True)
class WebPolicy:
    """Web boundary for tools HyoDo judges as web-classified."""

    allowed_domains: tuple[str, ...] = ()
    allow_non_get: bool = False
    allow_credential_paths: bool = False


@dataclass(frozen=True)
class TrustPolicy:
    """Caps, but never grants, operator-controlled policy trust."""

    max_level: int = 3


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
    #: Off by default because ledgers recorded before 1-B never declared an
    #: opening intent. Reports can opt into requiring a human mission prompt.
    require_mission_prompt: bool = False
    web: WebPolicy | None = None
    ask_tools: tuple[str, ...] = ()
    ask_threshold: int | None = None
    trust: TrustPolicy | None = None

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
    #: (observed, expected) boundary surfaces actually checked for this event.
    #: Integers only — never a ratio, percentage, or probability.
    coverage: tuple[int, int] = (0, 0)
    #: rule-id-shaped identifiers of every discretionary condition this event
    #: tripped, e.g. ("web_domain_unlisted:api.example.com",). Empty when none.
    external_variables: tuple[str, ...] = ()
    #: The effective trust level (min(cap, granted)) used to reach this decision.
    trust_level: int = 1

    def as_dict(self) -> dict[str, Any]:
        """Serialize the decision for ledger stamping and JSON CLI output.

        ``evaluated_by`` marks this as a *measured* decision. A PolicyDecision can only
        come from :func:`evaluate_policy`, so its presence in the ledger is proof HyoDo
        ran the policy rather than trusting the caller.

        Honesty rule: this dict may never grow a ``probability`` or ``confidence``
        key. "How sure are we" is answered as ``coverage`` — an integer
        ``observed / expected`` pair — never as a float.
        """
        return {
            "decision": self.decision,
            "rule_id": self.rule_id,
            "reason": self.reason,
            "evaluated_by": POLICY_SCHEMA_ID,
            "coverage": list(self.coverage),
            "external_variables": list(self.external_variables),
            "trust_level": self.trust_level,
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

    require_mission_prompt = raw.get("require_mission_prompt", False)
    if not isinstance(require_mission_prompt, bool):
        raise PolicyConfigError(f"{path}: require_mission_prompt must be a boolean")
    require_declared_paths = raw.get("require_declared_paths", False)
    if not isinstance(require_declared_paths, bool):
        raise PolicyConfigError(f"{path}: require_declared_paths must be a boolean")

    web_raw = raw.get("web")
    web: WebPolicy | None = None
    if web_raw is not None:
        if not isinstance(web_raw, dict):
            raise PolicyConfigError(f"{path}: [web] must be a table")
        allowed_domains_raw = web_raw.get("allowed_domains", [])
        if not isinstance(allowed_domains_raw, list) or not all(
            isinstance(domain, str) and domain for domain in allowed_domains_raw
        ):
            raise PolicyConfigError(
                f"{path}: web.allowed_domains must be a list of non-empty strings"
            )
        allow_non_get = web_raw.get("allow_non_get", False)
        if not isinstance(allow_non_get, bool):
            raise PolicyConfigError(f"{path}: web.allow_non_get must be a boolean")
        allow_credential_paths = web_raw.get("allow_credential_paths", False)
        if not isinstance(allow_credential_paths, bool):
            raise PolicyConfigError(f"{path}: web.allow_credential_paths must be a boolean")
        web = WebPolicy(
            allowed_domains=tuple(allowed_domains_raw),
            allow_non_get=allow_non_get,
            allow_credential_paths=allow_credential_paths,
        )

    ask_tools_raw = raw.get("ask_tools", [])
    if not isinstance(ask_tools_raw, list) or not all(
        isinstance(tool, str) and tool for tool in ask_tools_raw
    ):
        raise PolicyConfigError(f"{path}: ask_tools must be a list of non-empty strings")
    ask_threshold = raw.get("ask_threshold")
    if ask_threshold is not None and (
        not isinstance(ask_threshold, int) or isinstance(ask_threshold, bool) or ask_threshold < 0
    ):
        raise PolicyConfigError(f"{path}: ask_threshold must be a non-negative integer")

    trust_raw = raw.get("trust")
    trust: TrustPolicy | None = None
    if trust_raw is not None:
        if not isinstance(trust_raw, dict):
            raise PolicyConfigError(f"{path}: [trust] must be a table")
        max_level = trust_raw.get("max_level", 3)
        if not isinstance(max_level, int) or isinstance(max_level, bool) or not 0 <= max_level <= 3:
            raise PolicyConfigError(f"{path}: trust.max_level must be an integer between 0 and 3")
        trust = TrustPolicy(max_level=max_level)

    return PolicyConfig(
        schema=schema,
        max_steps=max_steps,
        allowed_tools=allowed_tools,
        blocked_path_globs=blocked,
        require_declared_paths=require_declared_paths,
        require_mission_prompt=require_mission_prompt,
        web=web,
        ask_tools=tuple(ask_tools_raw),
        ask_threshold=ask_threshold,
        trust=trust,
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


def _is_web_classified(tool_name: str | None, policy: PolicyConfig) -> bool:
    """Return whether a tool is subject to the web/discretionary boundary."""
    return isinstance(tool_name, str) and (
        tool_name in _BUILTIN_WEB_TOOLS or tool_name in policy.ask_tools
    )


def _domain_allowed(domain: str, allowed_domains: tuple[str, ...]) -> bool:
    """Return whether a domain matches an exact or wildcard allowlist entry."""
    return any(fnmatch.fnmatch(domain, pattern) for pattern in allowed_domains)


def _compute_coverage(
    policy: PolicyConfig,
    kind: Any,
    tool_name: str | None,
    paths: list[Any],
    urls: list[Any],
    method: str | None,
    observed_steps: int | None,
    root: Path | None,
    *,
    effective_level: int,
) -> tuple[int, int]:
    """Return observed/expected counts for applicable boundary surfaces."""
    is_tool_event = kind in ("tool_call", "tool_result")
    expected = 0
    observed = 0
    tool_identity_expected = is_tool_event and (
        policy.allowlist_active
        or bool(policy.ask_tools)
        or (isinstance(tool_name, str) and tool_name in _BUILTIN_WEB_TOOLS)
    )
    if tool_identity_expected:
        expected += 1
        if isinstance(tool_name, str) and tool_name:
            observed += 1
    path_boundary_expected = bool(policy.blocked_path_globs) or root is not None
    if path_boundary_expected:
        expected += 1
        if paths or not policy.require_declared_paths:
            observed += 1
    web_boundary_expected = policy.web is not None and _is_web_classified(tool_name, policy)
    if web_boundary_expected:
        expected += 1
        urls_fully_declared = bool(urls) and all(
            isinstance(item, dict)
            and isinstance(item.get("domain"), str)
            and bool(item.get("domain"))
            for item in urls
        )
        if urls_fully_declared and method is not None:
            observed += 1
    step_boundary_expected = policy.max_steps is not None or effective_level >= 2
    if step_boundary_expected:
        expected += 1
        if observed_steps is not None:
            observed += 1
    return observed, expected


def _resolve_trust_level(
    trust_policy: TrustPolicy | None,
    root: Path | None,
    external_variables: tuple[str, ...],
) -> tuple[int, str | None]:
    """Resolve effective trust and report an unverifiable grant when relevant."""
    if trust_policy is None:
        return 1, None
    lookup_root = root if root is not None else Path.cwd()
    state, error = load_policy_trust(lookup_root)
    if error is not None:
        return (0, "trust_grant_unobserved") if external_variables else (0, None)
    return effective_trust_level(trust_policy.max_level, state), None


def evaluate_policy(
    event: dict[str, Any],
    policy: PolicyConfig,
    *,
    observed_steps: int | None = None,
    root: Path | None = None,
) -> PolicyDecision:
    """Evaluate a validated event against policy without silent authorization.

    ``observed_steps`` is read from the ledger, never trusted from the event.
    ``root`` is keyword-only and optional for backward compatibility; it is used
    for project-boundary checks and the untracked policy trust store.
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
    paths = paths if isinstance(paths, list) else []
    method = tool.get("method") if isinstance(tool, dict) else None
    urls = tool.get("urls") if isinstance(tool, dict) else None
    urls = urls if isinstance(urls, list) else []
    is_tool_event = kind in ("tool_call", "tool_result")
    web_classified = is_tool_event and _is_web_classified(tool_name, policy)

    if is_tool_event and policy.allowlist_active:
        allowed = policy.allowed_tools or ()
        if not isinstance(tool_name, str) or tool_name not in allowed:
            return PolicyDecision(
                decision="DENY",
                rule_id="tool_not_allowed",
                reason=f"tool {tool_name!r} not in allowed_tools",
            )

    if policy.require_declared_paths and policy.blocked_path_globs and is_tool_event and not paths:
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id="data_boundary_undeclared",
            reason="tool declared no paths; blocked_path_globs cannot be checked",
        )

    if policy.blocked_path_globs and paths:
        for path_value in paths:
            if not isinstance(path_value, str):
                continue
            matched = _path_blocked(path_value, policy.blocked_path_globs)
            if matched is not None:
                return PolicyDecision(
                    decision="DENY",
                    rule_id="data_boundary",
                    reason=f"path {path_value!r} matched blocked glob {matched!r}",
                )

    if policy.max_steps is not None and observed_steps is None:
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id="max_steps",
            reason="ledger step count unavailable; max_steps cannot be enforced",
        )

    if web_classified and policy.web is not None:
        if (
            isinstance(method, str)
            and method not in _SAFE_HTTP_METHODS
            and not policy.web.allow_non_get
        ):
            return PolicyDecision(
                decision="DENY",
                rule_id="web_non_get_denied",
                reason=f"method {method!r} is not GET/HEAD and allow_non_get is false",
            )
        if not policy.web.allow_credential_paths:
            for entry in urls:
                if isinstance(entry, dict) and (
                    entry.get("credential_shaped") is True
                    or (
                        isinstance(entry.get("path"), str) and credential_shaped_path(entry["path"])
                    )
                ):
                    return PolicyDecision(
                        decision="DENY",
                        rule_id="web_credential_path_denied",
                        reason=(
                            f"url path {entry['path']!r} matches a credential-shaped "
                            "pattern and allow_credential_paths is false"
                            if isinstance(entry.get("path"), str)
                            else f"url digest {entry.get('digest')} on "
                            f"{entry.get('domain')} is credential-shaped"
                        ),
                    )

            if any(
                not isinstance(entry, dict)
                or (
                    not isinstance(entry.get("path"), str)
                    and not isinstance(entry.get("credential_shaped"), bool)
                )
                for entry in urls
            ):
                return PolicyDecision(
                    decision="UNOBSERVED",
                    rule_id="web_credential_path_unobserved",
                    reason="URL path unavailable; credential path boundary cannot be checked",
                )

    external_variables: list[str] = []
    unobserved_boundary: str | None = None
    if web_classified and policy.web is not None:
        if not urls:
            unobserved_boundary = "web_boundary_undeclared"
        else:
            for entry in urls:
                if not isinstance(entry, dict):
                    unobserved_boundary = "web_boundary_undeclared"
                    continue
                domain = entry.get("domain")
                if not isinstance(domain, str) or not domain:
                    unobserved_boundary = "web_boundary_undeclared"
                    continue
                if not _domain_allowed(domain, policy.web.allowed_domains):
                    external_variables.append(f"web_domain_unlisted:{domain}")
            if method is None:
                unobserved_boundary = "web_boundary_undeclared"

    if root is not None:
        for path_value in paths:
            if not isinstance(path_value, str) or not path_value:
                continue
            candidate = Path(path_value)
            resolved = candidate if candidate.is_absolute() else root / candidate
            try:
                resolved.resolve().relative_to(root.resolve())
            except ValueError:
                external_variables.append(f"path_outside_root:{path_value}")

    if is_tool_event and _is_web_classified(tool_name, policy):
        external_variables.append(f"ask_tools:{tool_name}")

    if unobserved_boundary is not None:
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id=unobserved_boundary,
            reason="web boundary configured but tool.urls/tool.method were not fully declared",
            coverage=_compute_coverage(
                policy,
                kind,
                tool_name,
                paths,
                urls,
                method,
                observed_steps,
                root,
                effective_level=1,
            ),
            external_variables=tuple(external_variables),
            trust_level=1,
        )

    trust_level, trust_error = _resolve_trust_level(policy.trust, root, tuple(external_variables))
    coverage = _compute_coverage(
        policy,
        kind,
        tool_name,
        paths,
        urls,
        method,
        observed_steps,
        root,
        effective_level=trust_level,
    )
    if trust_error is not None:
        return PolicyDecision(
            decision="UNOBSERVED",
            rule_id=trust_error,
            reason="trust grant missing or unreadable; cannot verify the level needed to soften ASK",
            coverage=coverage,
            external_variables=tuple(external_variables),
            trust_level=trust_level,
        )

    if external_variables:
        detail = f"{len(external_variables)} external variable(s): {', '.join(external_variables)}"
        if policy.ask_threshold is not None:
            qualifier = "above" if len(external_variables) > policy.ask_threshold else "at/below"
            detail += f" ({qualifier} configured threshold {policy.ask_threshold})"
        if trust_level >= 2 and observed_steps is None:
            rule_id = "autorun_level3" if trust_level >= 3 else "autorun_level2"
            return PolicyDecision(
                decision="UNOBSERVED",
                rule_id=rule_id,
                reason=f"trust level {trust_level} requires an observed ledger step count",
                coverage=coverage,
                external_variables=tuple(external_variables),
                trust_level=trust_level,
            )
        if trust_level >= 3 and observed_steps is not None:
            return PolicyDecision(
                decision="ALLOW",
                rule_id="autorun_level3",
                reason=f"trust level 3 (full delegation): {detail}",
                coverage=coverage,
                external_variables=tuple(external_variables),
                trust_level=trust_level,
            )
        if (
            trust_level >= 2
            and observed_steps is not None
            and all(
                value.startswith("path_outside_root:") or value.startswith("ask_tools:")
                for value in external_variables
            )
        ):
            return PolicyDecision(
                decision="ALLOW",
                rule_id="autorun_level2",
                reason=f"trust level 2 (inside configured boundary): {detail}",
                coverage=coverage,
                external_variables=tuple(external_variables),
                trust_level=trust_level,
            )
        return PolicyDecision(
            decision="ASK",
            rule_id="external_variable",
            reason=detail,
            coverage=coverage,
            external_variables=tuple(external_variables),
            trust_level=trust_level,
        )

    return PolicyDecision(
        decision="ALLOW",
        rule_id=None,
        reason=None,
        coverage=coverage,
        external_variables=(),
        trust_level=trust_level,
    )


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
