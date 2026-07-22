"""Auditable, fail-closed scan exceptions for local workspaces.

Exceptions are deliberately narrow: general syntax scans may omit an exact
workspace-relative glob, while safety findings require both a path glob and a
``category/label`` rule match.  A malformed configured file is an observation
failure, never a clean scan.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib  # type: ignore[no-redef]


SCAN_EXCEPTIONS_SCHEMA = "hyodo.scan-exceptions/v1"
SCAN_EXCEPTIONS_RELATIVE_PATH = Path(".hyodo") / "scan-exceptions.toml"


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


def load_scan_exceptions(root: Path) -> ScanExceptionsConfig:
    """Load ``.hyodo/scan-exceptions.toml`` or return an empty policy.

    The file is opt-in. Once it exists, malformed schema or entries are errors
    so a typo cannot silently make a scan look healthier than it is.
    """
    path = root / SCAN_EXCEPTIONS_RELATIVE_PATH
    if not path.exists():
        return ScanExceptionsConfig(general=(), safety=())
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
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
    return ScanExceptionsConfig(general=general, safety=safety)


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
