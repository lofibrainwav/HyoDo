from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

try:
    from scripts.release.verify_release_chain import CHAIN_STEPS, ChainStep, render_receipt
    from scripts.release.version_sources import (
        VersionSourceUpdateError,
        synchronized_version,
        update_version_sources,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from verify_release_chain import CHAIN_STEPS, ChainStep, render_receipt
    from version_sources import (
        VersionSourceUpdateError,
        synchronized_version,
        update_version_sources,
    )

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")
CHANGELOG_HEADER_END = (
    "and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).\n\n"
)


class ReleasePrepError(RuntimeError):
    """Raised when release preparation would be unsafe or ambiguous."""


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


def _unmeasured_receipt() -> str:
    """A receipt written before the chain runs says UNOBSERVED, never "not done".

    An unchecked box asserts the step did not happen, so it is false from the
    moment the release succeeds and nothing brings a writer back to it --
    which is exactly how 4.19.1 shipped claiming a chain it had completed.
    """
    steps = [ChainStep(name=name, state="UNOBSERVED", evidence=None) for name in CHAIN_STEPS]
    return render_receipt(steps, measured_at=None)


def _release_notes(version: str) -> str:
    return f"""# HyoDo {version} Release Notes

## Intent

TODO: describe release intent.

{_unmeasured_receipt()}"""


def prepare_release(root: Path, version: str, *, today: str | None = None) -> None:
    if not VERSION_RE.fullmatch(version):
        raise ReleasePrepError("version must be plain semver like 4.12.1, without a v prefix")

    root = root.resolve()
    changelog = root / "CHANGELOG.md"
    release_note = root / "docs" / "releases" / f"{version}.md"
    release_date = today or date.today().isoformat()

    if release_note.exists():
        raise ReleasePrepError(f"{release_note} already exists")

    try:
        old_version = synchronized_version(root)
    except VersionSourceUpdateError as exc:
        raise ReleasePrepError(str(exc)) from exc
    if old_version == version:
        raise ReleasePrepError(f"VERSION is already {version}")

    changelog_text = changelog.read_text()
    marker = f"## [{version}]"
    if marker in changelog_text:
        raise ReleasePrepError(f"CHANGELOG.md already contains {marker}")
    if CHANGELOG_HEADER_END not in changelog_text:
        raise ReleasePrepError("CHANGELOG.md: expected changelog header marker not found")

    try:
        update_version_sources(root, version)
    except VersionSourceUpdateError as exc:
        raise ReleasePrepError(str(exc)) from exc
    changelog.write_text(
        changelog_text.replace(
            CHANGELOG_HEADER_END, CHANGELOG_HEADER_END + _release_section(version, release_date), 1
        )
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
