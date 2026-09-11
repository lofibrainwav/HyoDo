from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.release.prepare_release import ReleasePrepError, prepare_release

HEADER = """# Changelog

All notable changes to HyoDo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

HISTORY = """## [4.11.0] - 2026-09-03

Previous release.

### Added

- Existing history must stay intact.
"""

PLUGIN_JSON = """{
  "name": "hyodo",
  "version": "{version}"
}
"""

SERVER_JSON = """{
  "name": "io.github.lofibrainwav/hyodo",
  "version": "{version}",
  "packages": [
    {"identifier": "hyodo", "version": "{version}"}
  ]
}
"""

MARKETPLACE_JSON = """{
  "name": "hyodo",
  "plugins": [
    {"name": "hyodo", "version": "{version}"}
  ]
}
"""


def write_minimal_repo(root: Path, version: str = "4.11.0") -> None:
    (root / "hyodo").mkdir()
    (root / "docs" / "releases").mkdir(parents=True)
    (root / "VERSION").write_text(f"{version}\n")
    (root / "pyproject.toml").write_text(
        f"""[project]
name = "hyodo"
version = "{version}"
"""
    )
    (root / "hyodo" / "__init__.py").write_text(
        f"""from __future__ import annotations

__version__ = "{version}"
"""
    )
    (root / "Dockerfile").write_text(f'LABEL version="{version}"\n')
    (root / ".claude-plugin").mkdir()
    (root / ".claude-plugin" / "plugin.json").write_text(PLUGIN_JSON.replace("{version}", version))
    (root / "server.json").write_text(SERVER_JSON.replace("{version}", version))
    (root / ".claude-plugin" / "marketplace.json").write_text(
        MARKETPLACE_JSON.replace("{version}", version)
    )
    (root / "CHANGELOG.md").write_text(HEADER + HISTORY)


def test_prepare_release_updates_all_version_sources(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)

    prepare_release(tmp_path, "4.12.0", today="2026-09-05")

    assert (tmp_path / "VERSION").read_text() == "4.12.0\n"
    assert 'version = "4.12.0"' in (tmp_path / "pyproject.toml").read_text()
    assert '__version__ = "4.12.0"' in (tmp_path / "hyodo" / "__init__.py").read_text()
    assert 'version="4.12.0"' in (tmp_path / "Dockerfile").read_text()
    assert (
        json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text())["version"] == "4.12.0"
    )
    server = json.loads((tmp_path / "server.json").read_text())
    assert server["version"] == "4.12.0"
    assert server["packages"][0]["version"] == "4.12.0"
    marketplace = json.loads((tmp_path / ".claude-plugin" / "marketplace.json").read_text())
    assert marketplace["plugins"][0]["version"] == "4.12.0"


def test_prepare_release_inserts_changelog_section_after_header(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)

    prepare_release(tmp_path, "4.12.0", today="2026-09-05")

    changelog = (tmp_path / "CHANGELOG.md").read_text()
    assert changelog.startswith(HEADER + "## [4.12.0] - 2026-09-05\n")
    assert changelog.index("## [4.12.0]") < changelog.index("## [4.11.0]")


def test_prepare_release_preserves_existing_changelog_history(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)

    prepare_release(tmp_path, "4.12.0", today="2026-09-05")

    changelog = (tmp_path / "CHANGELOG.md").read_text()
    assert HISTORY in changelog
    assert "Existing history must stay intact." in changelog


def test_prepare_release_creates_release_notes_file(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)

    prepare_release(tmp_path, "4.12.0", today="2026-09-05")

    release_note = tmp_path / "docs" / "releases" / "4.12.0.md"
    assert release_note.exists()
    text = release_note.read_text()
    assert text.startswith("# HyoDo 4.12.0 Release Notes\n")
    assert "Signed verified tag" in text
    assert "PyPI provenance verified" in text
    # A receipt written before the chain runs states UNOBSERVED, never a
    # checkbox: an unticked box asserts "did not happen" and is false the
    # moment the release succeeds, which is how 4.19.1 shipped claiming a
    # chain it had already completed.
    assert "UNOBSERVED" in text
    assert "- [ ]" not in text


def test_prepare_release_refuses_duplicate_release_note(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    (tmp_path / "docs" / "releases" / "4.12.0.md").write_text("existing\n")

    with pytest.raises(ReleasePrepError, match="already exists"):
        prepare_release(tmp_path, "4.12.0", today="2026-09-05")


@pytest.mark.parametrize("bad_version", ["v4.12.0", "4.12", "4.12.0-dev", " 4.12.0"])
def test_prepare_release_requires_plain_semver_without_v_prefix(
    tmp_path: Path, bad_version: str
) -> None:
    write_minimal_repo(tmp_path)

    with pytest.raises(ReleasePrepError, match="plain semver"):
        prepare_release(tmp_path, bad_version, today="2026-09-05")


def test_prepare_release_refuses_duplicate_changelog_section(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(HEADER + "## [4.12.0] - 2026-09-05\n\nExisting.\n\n" + HISTORY)

    with pytest.raises(ReleasePrepError, match="already contains"):
        prepare_release(tmp_path, "4.12.0", today="2026-09-05")


def test_prepare_release_fails_when_version_sources_are_already_divergent(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "hyodo"\nversion = "4.10.0"\n')

    with pytest.raises(ReleasePrepError, match="version sources are not synchronized"):
        prepare_release(tmp_path, "4.12.0", today="2026-09-05")


def test_prepare_release_rejects_divergent_extended_version_source(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    (tmp_path / "server.json").write_text(SERVER_JSON.replace("{version}", "4.10.0"))

    with pytest.raises(ReleasePrepError, match="version sources are not synchronized"):
        prepare_release(tmp_path, "4.12.0", today="2026-09-05")
