"""Update every version-bearing source in one validated operation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

try:
    from scripts.release.check_version_sync import VersionSyncError, collect_sources
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from check_version_sync import VersionSyncError, collect_sources


class VersionSourceUpdateError(RuntimeError):
    """Raised when version sources cannot be validated or updated."""


_JSON_FIELDS: dict[str, tuple[tuple[str, ...], ...]] = {
    ".claude-plugin/plugin.json": (("version",),),
    "server.json": (("version",), ("packages", "0", "version")),
    ".claude-plugin/marketplace.json": (("plugins", "0", "version"),),
}


def _replace_once(text: str, old: str, new: str, *, path: str) -> str:
    count = text.count(old)
    if count != 1:
        raise VersionSourceUpdateError(f"{path}: expected exactly one version value, found {count}")
    return text.replace(old, new, 1)


def _get_field(data: Any, path: tuple[str, ...], *, source: str) -> Any:
    current = data
    for part in path:
        try:
            current = current[int(part)] if isinstance(current, list) else current[part]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            joined = ".".join(path)
            raise VersionSourceUpdateError(f"{source}: missing version field {joined}") from exc
    return current


def _render_json_update(path: Path, old: str, new: str, fields: tuple[tuple[str, ...], ...]) -> str:
    source = str(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise VersionSourceUpdateError(f"{source}: cannot read valid JSON") from exc

    for field in fields:
        actual = _get_field(data, field, source=source)
        if actual != old:
            joined = ".".join(field)
            raise VersionSourceUpdateError(
                f"{source}: {joined} is {actual!r}, expected synchronized version {old!r}"
            )
    for field in fields:
        parent = data
        for part in field[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        final = field[-1]
        if isinstance(parent, list):
            parent[int(final)] = new
        else:
            parent[final] = new
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def synchronized_version(root: Path) -> str:
    """Return the shared version after validating all seven sources."""
    root = root.resolve()
    try:
        sources = collect_sources(root)
    except VersionSyncError as exc:
        raise VersionSourceUpdateError(str(exc)) from exc

    old_version = sources["VERSION"]
    if any(version != old_version for version in sources.values()):
        details = ", ".join(f"{label}={version}" for label, version in sources.items())
        raise VersionSourceUpdateError(f"version sources are not synchronized: {details}")
    return old_version


def update_version_sources(root: Path, new_version: str) -> str:
    """Validate and update all seven version-bearing repository sources."""
    root = root.resolve()
    old_version = synchronized_version(root)

    rendered: dict[Path, str] = {
        root / "VERSION": f"{new_version}\n",
        root / "pyproject.toml": _replace_once(
            (root / "pyproject.toml").read_text(encoding="utf-8"),
            f'version = "{old_version}"',
            f'version = "{new_version}"',
            path="pyproject.toml",
        ),
        root / "hyodo" / "__init__.py": _replace_once(
            (root / "hyodo" / "__init__.py").read_text(encoding="utf-8"),
            f'__version__ = "{old_version}"',
            f'__version__ = "{new_version}"',
            path="hyodo/__init__.py",
        ),
        root / "Dockerfile": _replace_once(
            (root / "Dockerfile").read_text(encoding="utf-8"),
            f'LABEL version="{old_version}"',
            f'LABEL version="{new_version}"',
            path="Dockerfile",
        ),
    }
    for relative, fields in _JSON_FIELDS.items():
        path = root / relative
        rendered[path] = _render_json_update(path, old_version, new_version, fields)

    for path, text in rendered.items():
        path.write_text(text, encoding="utf-8")
    return old_version
