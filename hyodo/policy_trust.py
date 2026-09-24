"""Operator trust store for policy ASK escalation.

The tracked policy file only caps trust. Grants require explicit operator
approval and live in per-user state (`hyodo.user_state`), never in the
checkout: a repository could otherwise ship its own grant. A grant is bound to

- the workspace identity (the resolved checkout path),
- the digest of ``.hyodo/policy.toml`` at grant time,
- the scopes it was granted for, and
- a freshness window (``expires_at``).

A grant that fails any binding reads back as an error, and every consumer
resolves an error to trust level 0. A ``.hyodo/policy-trust.json`` inside the
checkout is never read.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from hyodo.user_state import (
    file_digest,
    read_json,
    workspace_identity,
    workspace_state_path,
    write_json_private,
)

POLICY_TRUST_SCHEMA_ID = "hyodo.policy-trust/v2"
#: The legacy checkout location. Never read; reported when present.
POLICY_TRUST_RELATIVE_PATH = Path(".hyodo") / "policy-trust.json"
POLICY_TRUST_STATE_NAME = "policy-trust.json"
POLICY_TRUST_ENV_VAR = "HYODO_POLICY_TRUST_ALL"
#: Kept local to avoid importing hyodo.policy, which imports this module.
_POLICY_FILE_RELATIVE_PATH = Path(".hyodo") / "policy.toml"
_POLICY_ABSENT_DIGEST = "absent"
_TRUTHY_ENV_VALUES = frozenset({"1", "true", "yes", "on"})
_MIN_LEVEL = 0
_MAX_LEVEL = 3

#: What a grant may be used for. A consumer names the scope it needs.
SCOPE_POLICY_ASK = "policy.ask"
SCOPE_EYE_KEEP = "eye.keep"
DEFAULT_GRANT_SCOPES = (SCOPE_POLICY_ASK, SCOPE_EYE_KEEP)
#: A grant stops counting after this long; the operator grants again.
POLICY_TRUST_MAX_AGE = timedelta(days=30)


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
    workspace_id: str = ""
    policy_digest: str = ""
    scopes: tuple[str, ...] = ()
    expires_at: str = ""


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


def policy_trust_path(root: Path) -> Path:
    """Return where *root*'s grant lives in per-user state."""
    return workspace_state_path(root, POLICY_TRUST_STATE_NAME)


def current_policy_digest(root: Path) -> str:
    """Digest of the policy file a grant is bound to (``absent`` when missing)."""
    path = root / _POLICY_FILE_RELATIVE_PATH
    if not path.exists():
        return _POLICY_ABSENT_DIGEST
    return file_digest(path) or "unreadable"


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _read_raw_policy_trust(root: Path) -> tuple[PolicyTrustState | None, str | None]:
    """Parse the stored grant without evaluating its bindings."""
    raw, error = read_json(policy_trust_path(root))
    if error == "missing":
        return None, "trust_missing"
    if error is not None or not isinstance(raw, dict):
        return None, "trust_invalid"
    if raw.get("schema") != POLICY_TRUST_SCHEMA_ID:
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
    scopes = raw.get("scopes")
    if not isinstance(scopes, list) or not all(isinstance(item, str) for item in scopes):
        return None, "trust_invalid"
    for key in ("workspace_id", "policy_digest", "expires_at"):
        if not isinstance(raw.get(key), str) or not raw[key]:
            return None, "trust_invalid"
    return (
        PolicyTrustState(
            level=current.level,
            granted_at=current.granted_at,
            granted_by=current.granted_by,
            history=tuple(history),
            workspace_id=raw["workspace_id"],
            policy_digest=raw["policy_digest"],
            scopes=tuple(scopes),
            expires_at=raw["expires_at"],
        ),
        None,
    )


def load_policy_trust(
    root: Path,
    *,
    scope: str = SCOPE_POLICY_ASK,
    now: datetime | None = None,
) -> tuple[PolicyTrustState | None, str | None]:
    """Load the grant for *root* and check every binding.

    Returns ``(state, None)`` only when the grant belongs to this workspace,
    was made against the current policy file, covers *scope*, and has not
    expired. Otherwise ``(None, reason)`` with one of ``trust_missing``,
    ``trust_invalid``, ``trust_workspace_mismatch``, ``trust_policy_changed``,
    ``trust_scope_mismatch``, or ``trust_expired``.
    """
    state, error = _read_raw_policy_trust(root)
    if state is None:
        return None, error
    if state.workspace_id != workspace_identity(root):
        return None, "trust_workspace_mismatch"
    if state.policy_digest != current_policy_digest(root):
        return None, "trust_policy_changed"
    if scope not in state.scopes:
        return None, "trust_scope_mismatch"
    expires = _parse_time(state.expires_at)
    granted = _parse_time(state.granted_at)
    moment = now or datetime.now(timezone.utc)
    if expires is None or granted is None:
        return None, "trust_invalid"
    if not granted <= moment < expires:
        return None, "trust_expired"
    return state, None


def _save_policy_trust(root: Path, state: PolicyTrustState) -> None:
    payload = {
        "schema": POLICY_TRUST_SCHEMA_ID,
        "workspace_id": state.workspace_id,
        "policy_digest": state.policy_digest,
        "scopes": list(state.scopes),
        "level": state.level,
        "granted_at": state.granted_at,
        "expires_at": state.expires_at,
        "granted_by": state.granted_by,
        "history": [
            {"level": item.level, "granted_at": item.granted_at, "granted_by": item.granted_by}
            for item in state.history
        ],
    }
    write_json_private(root, POLICY_TRUST_STATE_NAME, payload)


def grant_policy_trust(
    root: Path,
    level: int,
    *,
    by: str,
    scopes: tuple[str, ...] = DEFAULT_GRANT_SCOPES,
    now: datetime | None = None,
) -> PolicyTrustState:
    """Record a grant bound to this workspace, policy digest, scopes, and expiry."""
    if (
        not isinstance(level, int)
        or isinstance(level, bool)
        or not _MIN_LEVEL <= level <= _MAX_LEVEL
    ):
        raise ValueError(f"level must be between {_MIN_LEVEL} and {_MAX_LEVEL}, got {level}")
    previous, _error = _read_raw_policy_trust(root)
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
    moment = now or datetime.now(timezone.utc)
    state = PolicyTrustState(
        level=level,
        granted_at=moment.isoformat(),
        granted_by=by,
        history=history,
        workspace_id=workspace_identity(root),
        policy_digest=current_policy_digest(root),
        scopes=tuple(scopes),
        expires_at=(moment + POLICY_TRUST_MAX_AGE).isoformat(),
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
