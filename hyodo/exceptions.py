"""Auditable, fail-closed scan exceptions for local workspaces.

Exceptions are deliberately narrow: general syntax scans may omit an exact
workspace-relative glob, while safety findings require both a path glob and a
``category/label`` rule match.  A malformed configured file is an observation
failure, never a clean scan.

The exceptions file is authored by the repository, so it cannot approve
itself: a checkout could otherwise suppress its own safety findings. A file is
applied only when an operator approved its exact digest -- recorded in per-user
state by ``hyodo safe --approve-exceptions`` -- or when the environment pins
that digest in ``HYODO_SCAN_EXCEPTIONS_DIGEST``. Until then nothing in it is
applied and the scan reports ``exceptions_status: unapproved``.
"""

from __future__ import annotations

import fnmatch
import hashlib
import os
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import tomllib  # pyright: ignore[reportMissingImports]
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]

from hyodo.user_state import (
    read_json,
    workspace_identity,
    workspace_state_path,
    write_json_private,
)

SCAN_EXCEPTIONS_SCHEMA = "hyodo.scan-exceptions/v1"
SCAN_EXCEPTIONS_RELATIVE_PATH = Path(".hyodo") / "scan-exceptions.toml"
SCAN_EXCEPTIONS_APPROVAL_STATE_NAME = "scan-exceptions-approval.json"
SCAN_EXCEPTIONS_APPROVAL_SCHEMA = "hyodo.scan-exceptions-approval/v1"
SCAN_EXCEPTIONS_DIGEST_ENV_VAR = "HYODO_SCAN_EXCEPTIONS_DIGEST"

#: No exceptions file exists.
EXCEPTIONS_NONE = "none"
#: The file's exact digest was approved by the operator (or pinned by env).
EXCEPTIONS_APPROVED = "approved"
#: The file exists but its digest was never approved; nothing in it applies.
EXCEPTIONS_UNAPPROVED = "unapproved"


class ScanExceptionsConfigError(ValueError):
    """Raised when a configured scan-exceptions file cannot be trusted."""


@dataclass(frozen=True)
class GeneralException:
    """A documented private/non-code path excluded from general syntax scans."""

    path: str
    reason: str


@dataclass(frozen=True)
class SafetyException:
    """A documented false-positive exception for one safety rule and path."""

    path: str
    rule: str
    reason: str


@dataclass(frozen=True)
class ScanExceptionsConfig:
    """Parsed local scan-exceptions policy."""

    general: tuple[GeneralException, ...]
    safety: tuple[SafetyException, ...]
    #: ``none`` / ``approved`` / ``unapproved`` -- see the module docstring.
    status: str = EXCEPTIONS_NONE
    #: ``sha256:<hex>`` of the exceptions file when one exists.
    digest: str | None = None
    #: Entries present in the file but not applied because it is unapproved.
    withheld: int = 0


def _required_string(item: dict[str, Any], field: str, table: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ScanExceptionsConfigError(f"{table}.{field} must be a non-empty string")
    return value.strip()


def _safe_relative_glob(value: str, table: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ScanExceptionsConfigError(
            f"{table}.path must be a relative glob inside the workspace"
        )
    return value


def _tables(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key, [])
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ScanExceptionsConfigError(f"{key} must be an array of tables")
    return value


def parse_scan_exceptions(root: Path) -> ScanExceptionsConfig:
    """Parse ``.hyodo/scan-exceptions.toml`` without checking approval.

    Used to show an operator what they would approve. Scans must use
    `load_scan_exceptions`, which applies nothing unapproved.
    """
    path = root / SCAN_EXCEPTIONS_RELATIVE_PATH
    if not path.exists():
        return ScanExceptionsConfig(general=(), safety=())
    try:
        raw = path.read_bytes()
        data = tomllib.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise ScanExceptionsConfigError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != SCAN_EXCEPTIONS_SCHEMA:
        raise ScanExceptionsConfigError(f"schema must equal {SCAN_EXCEPTIONS_SCHEMA!r}")

    general = tuple(
        GeneralException(
            path=_safe_relative_glob(
                _required_string(item, "path", "general_exceptions"), "general_exceptions"
            ),
            reason=_required_string(item, "reason", "general_exceptions"),
        )
        for item in _tables(data, "general_exceptions")
    )
    safety = tuple(
        SafetyException(
            path=_safe_relative_glob(
                _required_string(item, "path", "safety_exceptions"), "safety_exceptions"
            ),
            rule=_required_string(item, "rule", "safety_exceptions"),
            reason=_required_string(item, "reason", "safety_exceptions"),
        )
        for item in _tables(data, "safety_exceptions")
    )
    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
    return ScanExceptionsConfig(
        general=general, safety=safety, status=EXCEPTIONS_UNAPPROVED, digest=digest
    )


def _approved_digests(root: Path) -> dict[str, Any]:
    data, _error = read_json(workspace_state_path(root, SCAN_EXCEPTIONS_APPROVAL_STATE_NAME))
    if (
        not isinstance(data, dict)
        or data.get("schema") != SCAN_EXCEPTIONS_APPROVAL_SCHEMA
        or data.get("workspace_id") != workspace_identity(root)
        or not isinstance(data.get("approved"), dict)
    ):
        return {}
    return data["approved"]


def load_scan_exceptions(root: Path) -> ScanExceptionsConfig:
    """Load the exceptions a scan may apply.

    The file is opt-in. Once it exists, malformed schema or entries are errors
    so a typo cannot silently make a scan look healthier than it is. A
    well-formed file whose digest was not approved applies nothing: the result
    is empty with ``status == "unapproved"`` and ``withheld`` counting what
    was not applied.
    """
    parsed = parse_scan_exceptions(root)
    if parsed.digest is None:
        return parsed
    pinned = os.environ.get(SCAN_EXCEPTIONS_DIGEST_ENV_VAR, "").strip()
    if parsed.digest == pinned or parsed.digest in _approved_digests(root):
        return replace(parsed, status=EXCEPTIONS_APPROVED)
    return ScanExceptionsConfig(
        general=(),
        safety=(),
        status=EXCEPTIONS_UNAPPROVED,
        digest=parsed.digest,
        withheld=len(parsed.general) + len(parsed.safety),
    )


def approve_scan_exceptions(root: Path, digest: str, *, by: str) -> Path:
    """Record operator approval of one exceptions-file digest in user state."""
    approved = _approved_digests(root)
    approved[digest] = {"approved_at": datetime.now(timezone.utc).isoformat(), "by": by}
    return write_json_private(
        root,
        SCAN_EXCEPTIONS_APPROVAL_STATE_NAME,
        {
            "schema": SCAN_EXCEPTIONS_APPROVAL_SCHEMA,
            "workspace_id": workspace_identity(root),
            "approved": approved,
        },
    )


def _relative_path(path: Path, root: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def is_general_path_excluded(path: Path, root: Path, config: ScanExceptionsConfig) -> bool:
    """Return whether a configured general exception matches *path*."""
    relative = _relative_path(path, root)
    return relative is not None and any(
        fnmatch.fnmatchcase(relative, item.path) for item in config.general
    )


def safety_exception_reason(
    path: str | None, rule: str, root: Path, config: ScanExceptionsConfig
) -> str | None:
    """Return the recorded reason only for an exact path-and-rule exception."""
    if path is None:
        return None
    relative = _relative_path(Path(path), root)
    if relative is None:
        return None
    for item in config.safety:
        if item.rule == rule and fnmatch.fnmatchcase(relative, item.path):
            return item.reason
    return None
