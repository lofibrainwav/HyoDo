from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
CHANGELOG_HEADER_END = (
    "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
)


class ReleasePrepError(RuntimeError):
    """Raised when release preparation would be unsafe or ambiguous."""


def _replace_once(text: str, old: str, new: str, *, path: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ReleasePrepError(f"{path}: expected exactly one {old!r}, found {count}")
    return text.replace(old, new, 1)


def _read_version_sources(root: Path) -> tuple[str, str, str]:
    version_file = (root / "VERSION").read_text().strip()
    pyproject = root / "pyproject.toml"
    init_file = root / "hyodo" / "__init__.py"

    pyproject_text = pyproject.read_text()
    init_text = init_file.read_text()

    pyproject_match = re.search(r'^version = "([^"]+)"$', pyproject_text, re.MULTILINE)
    init_match = re.search(r'^__version__ = "([^"]+)"$', init_text, re.MULTILINE)
    if pyproject_match is None:
        raise ReleasePrepError("pyproject.toml: project version not found")
    if init_match is None:
        raise ReleasePrepError("hyodo/__init__.py: __version__ not found")

    return version_file, pyproject_match.group(1), init_match.group(1)


def _require_synced_version_sources(root: Path) -> str:
    version_file, pyproject_version, init_version = _read_version_sources(root)
    versions = {version_file, pyproject_version, init_version}
    if len(versions) != 1:
        raise ReleasePrepError(
            "version sources are not synchronized: "
            f"VERSION={version_file}, pyproject.toml={pyproject_version}, "
            f"hyodo/__init__.py={init_version}"
        )
    return version_file


def _release_section(version: str, today: str) -> str:
    return f"""## [{version}] - {today}

Release preparation.

### Added

- TODO: summarize added behavior.

### Changed

- TODO: summarize changed behavior.

### Fixed

- TODO: summarize fixed behavior.

### Evidence

- TODO: attach release receipt evidence.

"""


def _release_notes(version: str) -> str:
    return f"""# HyoDo {version} Release Notes

## Intent

TODO: describe release intent.

## Release chain receipt

- [ ] Signed verified tag created.
- [ ] Draft GitHub Release created.
- [ ] Release evidence workflow completed.
- [ ] SBOM asset attached.
- [ ] SHA-256 receipt attached.
- [ ] Human published Release.
- [ ] PyPI OIDC publish completed.
- [ ] PyPI provenance verified.
- [ ] Install smoke passed.
"""


def prepare_release(root: Path, version: str, *, today: str | None = None) -> None:
    if not VERSION_RE.fullmatch(version):
        raise ReleasePrepError("version must be plain semver like 4.12.1, without a v prefix")

    root = root.resolve()
    version_file = root / "VERSION"
    pyproject = root / "pyproject.toml"
    init_file = root / "hyodo" / "__init__.py"
    changelog = root / "CHANGELOG.md"
    release_note = root / "docs" / "releases" / f"{version}.md"
    release_date = today or date.today().isoformat()

    if release_note.exists():
        raise ReleasePrepError(f"{release_note} already exists")

    old_version = _require_synced_version_sources(root)
    if old_version == version:
        raise ReleasePrepError(f"VERSION is already {version}")

    changelog_text = changelog.read_text()
    marker = f"## [{version}]"
    if marker in changelog_text:
        raise ReleasePrepError(f"CHANGELOG.md already contains {marker}")
    if CHANGELOG_HEADER_END not in changelog_text:
        raise ReleasePrepError("CHANGELOG.md: expected changelog header marker not found")

    version_file.write_text(f"{version}\n")
    pyproject.write_text(
        _replace_once(
            pyproject.read_text(),
            f'version = "{old_version}"',
            f'version = "{version}"',
            path="pyproject.toml",
        )
    )
    init_file.write_text(
        _replace_once(
            init_file.read_text(),
            f'__version__ = "{old_version}"',
            f'__version__ = "{version}"',
            path="hyodo/__init__.py",
        )
    )
    changelog.write_text(
        changelog_text.replace(CHANGELOG_HEADER_END, CHANGELOG_HEADER_END + _release_section(version, release_date), 1)
    )
    release_note.parent.mkdir(parents=True, exist_ok=True)
    release_note.write_text(_release_notes(version))


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a HyoDo release candidate.")
    parser.add_argument("version", help="Plain semver version, for example 4.12.1")
    parser.add_argument("--root", default=".", help="Repository root to update")
    args = parser.parse_args()
    try:
        prepare_release(Path(args.root), args.version)
    except ReleasePrepError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
