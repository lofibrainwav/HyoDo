"""Untracked operator trust store for policy ASK escalation.

The tracked policy file only caps trust. Grants live in the untracked
``.hyodo/policy-trust.json`` store and require explicit operator approval.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_TRUST_SCHEMA_ID = "hyodo.policy-trust/v1"
POLICY_TRUST_RELATIVE_PATH = Path(".hyodo") / "policy-trust.json"
POLICY_TRUST_ENV_VAR = "HYODO_POLICY_TRUST_ALL"
_TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
_MIN_LEVEL = 0
_MAX_LEVEL = 3


@dataclass(frozen=True)
class PolicyTrustGrant:
    """One historical grant entry."""

    level: int
    granted_at: str
    granted_by: str


@dataclass(frozen=True)
class PolicyTrustState:
    """Current grant and prior grants read from disk."""

    level: int
    granted_at: str
    granted_by: str
    history: tuple[PolicyTrustGrant, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class PolicyTrustGrantDecision:
    """Whether a grant command is approved before it writes the store."""

    approved: bool
    reason: str
    via: str


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY_ENV_VALUES


def _is_noninteractive() -> bool:
    if _env_truthy("CI"):
        return True
    try:
        return not (sys.stdin.isatty() and sys.stdout.isatty())
    except (AttributeError, ValueError):
        return True


def default_granted_by() -> str:
    """Return the local identity recorded on an operator trust grant."""
    return os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"


def _parse_grant(raw: Any) -> PolicyTrustGrant | None:
    if not isinstance(raw, dict):
        return None
    level = raw.get("level")
    if (
        not isinstance(level, int)
        or isinstance(level, bool)
        or not _MIN_LEVEL <= level <= _MAX_LEVEL
        or not isinstance(raw.get("granted_at"), str)
        or not raw["granted_at"]
        or not isinstance(raw.get("granted_by"), str)
        or not raw["granted_by"]
    ):
        return None
    return PolicyTrustGrant(
        level=level,
        granted_at=raw["granted_at"],
        granted_by=raw["granted_by"],
    )


def load_policy_trust(root: Path) -> tuple[PolicyTrustState | None, str | None]:
    """Load the trust file, distinguishing missing from malformed state."""
    path = root / POLICY_TRUST_RELATIVE_PATH
    if not path.exists():
        return None, "trust_missing"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "trust_invalid"
    if not isinstance(raw, dict) or raw.get("schema") != POLICY_TRUST_SCHEMA_ID:
        return None, "trust_invalid"
    current = _parse_grant(raw)
    if current is None:
        return None, "trust_invalid"
    history_raw = raw.get("history", [])
    if not isinstance(history_raw, list):
        return None, "trust_invalid"
    history: list[PolicyTrustGrant] = []
    for entry in history_raw:
        parsed = _parse_grant(entry)
        if parsed is None:
            return None, "trust_invalid"
        history.append(parsed)
    return (
        PolicyTrustState(
            level=current.level,
            granted_at=current.granted_at,
            granted_by=current.granted_by,
            history=tuple(history),
        ),
        None,
    )


def _save_policy_trust(root: Path, state: PolicyTrustState) -> None:
    path = root / POLICY_TRUST_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": POLICY_TRUST_SCHEMA_ID,
        "level": state.level,
        "granted_at": state.granted_at,
        "granted_by": state.granted_by,
        "history": [
            {"level": item.level, "granted_at": item.granted_at, "granted_by": item.granted_by}
            for item in state.history
        ],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def grant_policy_trust(root: Path, level: int, *, by: str) -> PolicyTrustState:
    """Record a grant and retain the previous grant in history."""
    if (
        not isinstance(level, int)
        or isinstance(level, bool)
        or not _MIN_LEVEL <= level <= _MAX_LEVEL
    ):
        raise ValueError(f"level must be between {_MIN_LEVEL} and {_MAX_LEVEL}, got {level}")
    previous, _error = load_policy_trust(root)
    history = previous.history if previous is not None else ()
    if previous is not None:
        history = (
            *history,
            PolicyTrustGrant(
                level=previous.level,
                granted_at=previous.granted_at,
                granted_by=previous.granted_by,
            ),
        )
    state = PolicyTrustState(
        level=level,
        granted_at=datetime.now(timezone.utc).isoformat(),
        granted_by=by,
        history=history,
    )
    _save_policy_trust(root, state)
    return state


def effective_trust_level(max_level: int, granted: PolicyTrustState | None) -> int:
    """Return ``min(max_level, granted_level)`` or zero without a grant."""
    return min(max_level, granted.level if granted is not None else 0)


def _prompt_policy_trust_grant(level: int, by: str) -> bool:
    print(f"About to grant policy trust level {level} to {by!r}.")
    print("Levels 2-3 may auto-resolve ASK decisions and require a ledger record.")
    try:
        answer = input("Proceed? [y/N] ")
    except EOFError:
        return False
    return answer.strip().lower() in {"y", "yes"}


def resolve_policy_trust_grant(level: int, *, by: str, yes: bool) -> PolicyTrustGrantDecision:
    """Require an interactive or explicitly pre-approved trust grant."""
    if _is_noninteractive():
        if _env_truthy(POLICY_TRUST_ENV_VAR):
            return PolicyTrustGrantDecision(
                True,
                f"pre-approved via {POLICY_TRUST_ENV_VAR}",
                f"env:{POLICY_TRUST_ENV_VAR}",
            )
        return PolicyTrustGrantDecision(
            False,
            f"refusing to grant trust non-interactively; set {POLICY_TRUST_ENV_VAR}=1",
            "refused-noninteractive",
        )
    if yes or _prompt_policy_trust_grant(level, by):
        return PolicyTrustGrantDecision(True, "approved interactively", "prompt")
    return PolicyTrustGrantDecision(False, "declined interactively", "declined")
