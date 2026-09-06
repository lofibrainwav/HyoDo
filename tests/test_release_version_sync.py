from __future__ import annotations

from pathlib import Path

from scripts.release.check_version_sync import main

PLUGIN_JSON = """{{
  "name": "hyodo",
  "version": "{version}"
}}
"""

DOCKERFILE = """# HyoDo - model-agnostic quality gates for AI-assisted development

FROM python:3.12-slim

LABEL maintainer="AFO Kingdom"
LABEL version="{version}"
LABEL description="HyoDo - AI Code Quality Automation"
"""


def write_synced_repo(root: Path, version: str = "4.12.0") -> None:
    (root / "hyodo").mkdir(parents=True)
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "VERSION").write_text(f"{version}\n")
    (root / "pyproject.toml").write_text(f"""[project]\nname = "hyodo"\nversion = "{version}"\n""")
    (root / "hyodo" / "__init__.py").write_text(
        f"""from __future__ import annotations\n\n__version__ = "{version}"\n"""
    )
    (root / "Dockerfile").write_text(DOCKERFILE.format(version=version))
    (root / ".claude-plugin" / "plugin.json").write_text(PLUGIN_JSON.format(version=version))


def test_all_sources_synced_exits_zero(tmp_path: Path, capsys) -> None:
    write_synced_repo(tmp_path)

    code = main(argv=[], root=tmp_path)

    captured = capsys.readouterr()
    assert code == 0
    assert "OK: version 4.12.0 synchronized" in captured.out


def test_dockerfile_label_mismatch_exits_one_and_names_dockerfile(tmp_path: Path, capsys) -> None:
    write_synced_repo(tmp_path)
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(dockerfile.read_text().replace('version="4.12.0"', 'version="4.0.1"'))

    code = main(argv=[], root=tmp_path)

    captured = capsys.readouterr()
    assert code == 1
    assert "Dockerfile" in captured.err
    assert "4.0.1" in captured.err


def test_plugin_manifest_mismatch_exits_one_and_names_plugin_json(tmp_path: Path, capsys) -> None:
    write_synced_repo(tmp_path)
    plugin = tmp_path / ".claude-plugin" / "plugin.json"
    plugin.write_text(PLUGIN_JSON.format(version="4.0.1"))

    code = main(argv=[], root=tmp_path)

    captured = capsys.readouterr()
    assert code == 1
    assert ".claude-plugin/plugin.json" in captured.err
    assert "4.0.1" in captured.err


def test_expected_version_mismatch_exits_one(tmp_path: Path, capsys) -> None:
    write_synced_repo(tmp_path)

    code = main(argv=["9.9.9"], root=tmp_path)

    captured = capsys.readouterr()
    assert code == 1
    assert "expected 9.9.9" in captured.err


def test_missing_plugin_manifest_exits_one(tmp_path: Path, capsys) -> None:
    write_synced_repo(tmp_path)
    (tmp_path / ".claude-plugin" / "plugin.json").unlink()

    code = main(argv=[], root=tmp_path)

    captured = capsys.readouterr()
    assert code == 1
    assert ".claude-plugin/plugin.json" in captured.err
