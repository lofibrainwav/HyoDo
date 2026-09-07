"""Untracked local pairing lifecycle for the M5-B secure loopback bridge.

Mirrors :mod:`hyodo.policy_trust`'s untracked-store pattern: a workspace-local
``.hyodo/pairing.json`` file records the pairing lifecycle for the optional
MCP loopback/tailscale bridge without ever storing the bearer token itself —
only its sha256 digest is persisted.

This module owns no gate, policy, or transport logic. It answers exactly one
question: does a presented bearer token currently pair with this workspace?
Every answer fails closed: an unreadable or missing file is never treated as
PAIRED.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

PAIRING_SCHEMA_ID = "hyodo.pairing/v1"
PAIRING_RELATIVE_PATH = Path(".hyodo") / "pairing.json"
_TOKEN_BYTES = 32
_REQUIRED_STRING_FIELDS = ("workspace_id", "device_id", "root", "token_digest", "created_at")


class PairingState(str, Enum):
    """The four observable pairing states. UNOBSERVED is a fail-closed state,
    never treated as authenticated."""

    PAIRED = "PAIRED"
    REVOKED = "REVOKED"
    UNPAIRED = "UNPAIRED"
    UNOBSERVED = "UNOBSERVED"


@dataclass(frozen=True)
class PairingRecord:
    """One workspace's pairing record. Never carries the bearer token itself."""

    schema: str
    workspace_id: str
    device_id: str
    root: str
    token_digest: str
    created_at: str
    revoked_at: str | None = None
    last_seen_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the JSON-serializable form persisted to ``pairing.json``."""
        return {
            "schema": self.schema,
            "workspace_id": self.workspace_id,
            "device_id": self.device_id,
            "root": self.root,
            "token_digest": self.token_digest,
            "created_at": self.created_at,
            "revoked_at": self.revoked_at,
            "last_seen_at": self.last_seen_at,
        }


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _path(root: Path) -> Path:
    return root / PAIRING_RELATIVE_PATH


def _parse(raw: Any) -> PairingRecord | None:
    if not isinstance(raw, dict) or raw.get("schema") != PAIRING_SCHEMA_ID:
        return None
    for field_name in _REQUIRED_STRING_FIELDS:
        value = raw.get(field_name)
        if not isinstance(value, str) or not value:
            return None
    revoked_at = raw.get("revoked_at")
    if revoked_at is not None and not isinstance(revoked_at, str):
        return None
    last_seen_at = raw.get("last_seen_at")
    if last_seen_at is not None and not isinstance(last_seen_at, str):
        return None
    return PairingRecord(
        schema=raw["schema"],
        workspace_id=raw["workspace_id"],
        device_id=raw["device_id"],
        root=raw["root"],
        token_digest=raw["token_digest"],
        created_at=raw["created_at"],
        revoked_at=revoked_at,
        last_seen_at=last_seen_at,
    )


def _load_with_error(root: Path) -> tuple[PairingRecord | None, str | None]:
    """Load the pairing record, distinguishing missing from malformed state.

    Returns ``(record, error)`` where ``error`` is one of
    ``None | "pairing_missing" | "pairing_invalid"``.
    """
    path = _path(root)
    if not path.exists():
        return None, "pairing_missing"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "pairing_invalid"
    record = _parse(raw)
    if record is None:
        return None, "pairing_invalid"
    return record, None


def load_pairing(root: Path) -> PairingRecord | None:
    """Return the current pairing record, or ``None`` if missing or invalid.

    Callers that need to distinguish "no pairing yet" from "the pairing file
    is corrupt" should use :func:`pairing_state` instead, which reports the
    dedicated ``UNOBSERVED`` state for the latter.
    """
    record, _error = _load_with_error(root.expanduser().resolve())
    return record


def _save(root: Path, record: PairingRecord) -> Path:
    path = _path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def create_pairing(root: Path) -> tuple[PairingRecord, str]:
    """Create (or replace) the pairing for *root* and return ``(record, token)``.

    The token is 32 bytes of urlsafe randomness from :mod:`secrets`. It is
    returned exactly once here and is never written to disk — only its
    sha256 digest (``token_digest``) is persisted. Replacing an existing
    pairing keeps the same ``device_id`` (stable per machine/workspace) but
    issues a new ``workspace_id`` and token, matching "revoke, then re-pair"
    semantics for a fresh grant.
    """
    resolved = root.expanduser().resolve()
    token = secrets.token_urlsafe(_TOKEN_BYTES)
    previous, _error = _load_with_error(resolved)
    device_id = previous.device_id if previous is not None else str(uuid.uuid4())
    record = PairingRecord(
        schema=PAIRING_SCHEMA_ID,
        workspace_id=str(uuid.uuid4()),
        device_id=device_id,
        root=str(resolved),
        token_digest=_digest(token),
        created_at=datetime.now(timezone.utc).isoformat(),
        revoked_at=None,
        last_seen_at=None,
    )
    _save(resolved, record)
    return record, token


def revoke_pairing(root: Path) -> PairingRecord | None:
    """Mark the current pairing revoked (idempotent).

    Returns the updated record, or ``None`` when there is nothing to revoke
    (no pairing file present, or the file is invalid). Never raises.
    """
    resolved = root.expanduser().resolve()
    record, _error = _load_with_error(resolved)
    if record is None:
        return None
    updated = PairingRecord(
        schema=record.schema,
        workspace_id=record.workspace_id,
        device_id=record.device_id,
        root=record.root,
        token_digest=record.token_digest,
        created_at=record.created_at,
        revoked_at=record.revoked_at or datetime.now(timezone.utc).isoformat(),
        last_seen_at=record.last_seen_at,
    )
    _save(resolved, updated)
    return updated


def touch_last_seen(root: Path) -> None:
    """Best-effort: stamp ``last_seen_at`` on the current pairing.

    Never raises — a ledger/receipt write failure must not take down a
    request that has already passed authentication.
    """
    resolved = root.expanduser().resolve()
    try:
        record, _error = _load_with_error(resolved)
        if record is None:
            return
        updated = PairingRecord(
            schema=record.schema,
            workspace_id=record.workspace_id,
            device_id=record.device_id,
            root=record.root,
            token_digest=record.token_digest,
            created_at=record.created_at,
            revoked_at=record.revoked_at,
            last_seen_at=datetime.now(timezone.utc).isoformat(),
        )
        _save(resolved, updated)
    except OSError:
        pass


def pairing_state(root: Path) -> PairingState:
    """Return the pairing state for *root* without checking any token.

    Used by read-only surfaces (``pairing show``, the connector contract)
    that report state but never authenticate a caller.
    """
    record, error = _load_with_error(root.expanduser().resolve())
    if error == "pairing_invalid":
        return PairingState.UNOBSERVED
    if record is None:
        return PairingState.UNPAIRED
    if record.revoked_at is not None:
        return PairingState.REVOKED
    return PairingState.PAIRED


def verify_token(root: Path, token: str) -> PairingState:
    """Fail-closed pairing verification for one presented bearer token.

    Every call re-reads the pairing file from disk, so a revoke made by a
    concurrent ``hyodo mcp revoke`` takes effect on the very next request —
    no server restart required. A missing digest match on an otherwise
    active pairing reports ``UNPAIRED``: the presented token simply does not
    belong to this workspace's paired caller, and this module never returns
    ``PAIRED`` on ambiguity.
    """
    resolved = root.expanduser().resolve()
    record, error = _load_with_error(resolved)
    if error == "pairing_invalid":
        return PairingState.UNOBSERVED
    if record is None:
        return PairingState.UNPAIRED
    if record.revoked_at is not None:
        return PairingState.REVOKED
    if not secrets.compare_digest(record.token_digest, _digest(token)):
        return PairingState.UNPAIRED
    return PairingState.PAIRED
