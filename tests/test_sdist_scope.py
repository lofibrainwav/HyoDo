from __future__ import annotations

import io
import tarfile
from pathlib import Path

import pytest

from scripts.release.verify_sdist_scope import allowed_roots, verify_sdist_scope


def write_pyproject(path: Path) -> None:
    path.write_text(
        """
[tool.hatch.build.targets.sdist]
only-include = ["hyodo", "tests", "README.md", "schemas"]
""".strip()
        + "\n",
        encoding="utf-8",
    )


def write_sdist(path: Path, names: list[str]) -> None:
    with tarfile.open(path, "w:gz") as archive:
        for name in names:
            payload = b"x"
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))


def test_allowed_roots_come_from_pyproject_plus_hatch_metadata(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    write_pyproject(pyproject)
    assert allowed_roots(pyproject) == {
        ".gitignore",
        "hyodo",
        "tests",
        "README.md",
        "schemas",
        "PKG-INFO",
    }


def test_declared_public_sdist_scope_passes_regardless_of_compressed_size(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    write_pyproject(pyproject)
    sdist = tmp_path / "hyodo.tar.gz"
    write_sdist(
        sdist,
        [
            "hyodo-4.20.0/hyodo/__init__.py",
            "hyodo-4.20.0/tests/test_public.py",
            "hyodo-4.20.0/README.md",
            "hyodo-4.20.0/PKG-INFO",
            "hyodo-4.20.0/.gitignore",
        ],
    )
    root, members = verify_sdist_scope(sdist, pyproject)
    assert root == "hyodo-4.20.0"
    assert members == 5


def test_undeclared_top_level_path_fails(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    write_pyproject(pyproject)
    sdist = tmp_path / "hyodo.tar.gz"
    write_sdist(sdist, ["hyodo-4.20.0/docs/private.md"])
    with pytest.raises(ValueError, match="undeclared public paths"):
        verify_sdist_scope(sdist, pyproject)


def test_afo_core_fails_even_if_build_config_were_relaxed(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        "[tool.hatch.build.targets.sdist]\nonly-include = [\"afo_core\"]\n",
        encoding="utf-8",
    )
    sdist = tmp_path / "hyodo.tar.gz"
    write_sdist(sdist, ["hyodo-4.20.0/afo_core/private.py"])
    with pytest.raises(ValueError, match="includes afo_core"):
        verify_sdist_scope(sdist, pyproject)


def test_path_traversal_fails(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    write_pyproject(pyproject)
    sdist = tmp_path / "hyodo.tar.gz"
    write_sdist(sdist, ["hyodo-4.20.0/../escape.txt"])
    with pytest.raises(ValueError, match="unsafe paths"):
        verify_sdist_scope(sdist, pyproject)


def test_multiple_archive_roots_fail(tmp_path: Path) -> None:
    pyproject = tmp_path / "pyproject.toml"
    write_pyproject(pyproject)
    sdist = tmp_path / "hyodo.tar.gz"
    write_sdist(sdist, ["hyodo-4.20.0/hyodo/a.py", "other-root/hyodo/b.py"])
    with pytest.raises(ValueError, match="exactly one archive root"):
        verify_sdist_scope(sdist, pyproject)
