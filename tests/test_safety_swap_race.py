"""A checked directory swapped for an outward link must never be read through.

The scan checks containment with ``resolve()`` and reads later. These tests
swap the checked parent directory for a symlink to an outside directory in
that window (from inside ``is_scannable_file``, which runs between the two)
and require that the outside secret never reaches the corpus and that the
incomplete read is reported, not counted as scanned.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import hyodo.safety as safety

OUTSIDE_SECRET = "AKIAQWERTYUIOPASDFGH"  # matches the AWS key pattern


def _layout(tmp_path: Path) -> tuple[Path, Path]:
    root = tmp_path / "root"
    (root / "sub").mkdir(parents=True)
    (root / "sub" / "notes.txt").write_text("harmless\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "notes.txt").write_text(f"aws_key = {OUTSIDE_SECRET}\n", encoding="utf-8")
    return root, outside


def _swap_on_first_check(monkeypatch: pytest.MonkeyPatch, root: Path, outside: Path) -> None:
    real = safety.is_scannable_file
    swapped = {"done": False}

    def swap_then_check(path: Path) -> bool:
        result = real(path)
        if not swapped["done"]:
            swapped["done"] = True
            os.rename(root / "sub", root / "sub.moved")
            os.symlink(outside, root / "sub")
        return result

    monkeypatch.setattr(safety, "is_scannable_file", swap_then_check)


def test_working_tree_read_does_not_follow_swapped_parent(tmp_path, monkeypatch):
    root, outside = _layout(tmp_path)
    _swap_on_first_check(monkeypatch, root, outside)
    coverage: dict[str, int] = {}

    text, count = safety._read_working_tree_files(root, "?? sub/notes.txt\n", coverage=coverage)

    assert OUTSIDE_SECRET not in text
    assert count == 0
    assert coverage == {"scanned": 0, "total": 1, "unreadable": 1}


def test_directory_scan_does_not_follow_swapped_parent(tmp_path, monkeypatch):
    root, outside = _layout(tmp_path)
    _swap_on_first_check(monkeypatch, root, outside)

    corpus, source = safety.collect_scan_corpus(path=str(root), cwd=tmp_path)

    assert OUTSIDE_SECRET not in corpus
    assert source.startswith("error:read:")


def test_unreadable_working_tree_file_is_unobserved_not_clean():
    payload = safety._result_payload(
        "git status (no diff against HEAD)",
        [],
        False,
        scanned_files=1,
        total_scannable=1,
        scope="status",
        unreadable_files=1,
    )

    assert payload["coverage"] == "UNOBSERVED"


def test_contained_read_still_reads_plain_files(tmp_path):
    root, _outside = _layout(tmp_path)

    assert safety._read_contained_text(root, root / "sub" / "notes.txt") == "harmless\n"
