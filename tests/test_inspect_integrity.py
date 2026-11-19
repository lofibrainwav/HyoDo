"""Evidence-binding contracts for the `hyodo inspect` chunk pass.

Only bytes identical to the secret-scanned first-pass bytes are chunked. An
entry that changes, becomes unreadable, or is swapped for a symlink to
outside the tree between passes is not a complete observation: it moves from
``files`` to ``unreadable``, lowers ``coverage``, and gets no chunks.
"""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

from hyodo import inspect as inspect_mod
from hyodo.cli.main import app
from hyodo.inspect import render_report_md, run_inspect

runner = CliRunner()

# Assembled at runtime so secret scanners do not flag this test file itself.
FAKE_AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"


def _patch_second_read(monkeypatch, target, *, second):
    """Make the pass-2 read of *target* return *second* (bytes) or raise it."""
    real_read_bytes = inspect_mod.Path.read_bytes
    seen = {"n": 0}

    def read_bytes(self):
        if self == target:
            seen["n"] += 1
            if seen["n"] > 1:
                if isinstance(second, BaseException):
                    raise second
                return second
        return real_read_bytes(self)

    monkeypatch.setattr(inspect_mod.Path, "read_bytes", read_bytes)


@pytest.mark.parametrize(
    ("second", "reason"),
    [
        (PermissionError("gone"), "chunk_read_error:PermissionError"),
        (b"draft two\n", "changed_during_inspect"),
        (f"aws_key = {FAKE_AWS_KEY}\n".encode(), "changed_during_inspect"),
    ],
)
def test_unstable_entry_is_unobserved_not_chunked(tmp_path, monkeypatch, second, reason):
    target = tmp_path / "a.txt"
    target.write_text("stable one\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("other\n", encoding="utf-8")
    _patch_second_read(monkeypatch, target, second=second)

    result = run_inspect(str(tmp_path), root=tmp_path)
    manifest = result.folder_manifest

    assert manifest["coverage"] == [1, 2]
    assert manifest["unreadable"] == [{"path": "a.txt", "reason": reason}]
    assert [f["path"] for f in manifest["files"]] == ["b.txt"]
    b_digest = manifest["files"][0]["digest"]
    assert {c["file_digest"] for c in result.chunks_manifest["chunks"]} == {b_digest}
    assert any("a.txt" in line for line in result.warnings)
    assert "1/2 files digested" in render_report_md(result)


def test_unstable_entry_keeps_exit_zero_contract(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_text("stable\n", encoding="utf-8")
    _patch_second_read(monkeypatch, target, second=OSError("flaky"))

    result = runner.invoke(app, ["inspect", str(tmp_path), "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    folder = json.loads((tmp_path / ".hyodo" / "folder-manifest.json").read_text("utf-8"))
    assert folder["coverage"] == [0, 1]
    assert folder["unreadable"][0]["path"] == "a.txt"


def test_short_digest_collision_does_not_hide_a_change(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_bytes(b"original")
    _patch_second_read(monkeypatch, target, second=b"changed")
    monkeypatch.setattr(inspect_mod, "content_digest", lambda _data: "000000000000")

    result = run_inspect(str(tmp_path), root=tmp_path)

    assert result.folder_manifest["coverage"] == [0, 1]
    assert result.folder_manifest["changed_during_inspect"]
    assert result.chunks_manifest["chunks"] == []


def test_file_swapped_for_outside_symlink_is_not_chunked(tmp_path, monkeypatch):
    tree = tmp_path / "tree"
    tree.mkdir()
    target = tree / "a.txt"
    target.write_text("inside\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside bytes\n", encoding="utf-8")

    real_read_bytes = inspect_mod.Path.read_bytes
    seen = {"n": 0}

    def read_bytes(self):
        if self == target:
            seen["n"] += 1
            if seen["n"] == 1:
                data = real_read_bytes(self)
                target.unlink()
                target.symlink_to(outside)
                return data
        return real_read_bytes(self)

    monkeypatch.setattr(inspect_mod.Path, "read_bytes", read_bytes)
    result = run_inspect(str(tree), root=tree)

    assert result.chunks_manifest["chunks"] == []
    assert result.folder_manifest["coverage"] == [0, 1]
    assert result.folder_manifest["unreadable"] == [
        {"path": "a.txt", "reason": "chunk_symlink_outside_root"}
    ]


def test_every_chunk_binds_to_a_listed_file(tmp_path, monkeypatch):
    (tmp_path / "keep.txt").write_text("k" * 5000, encoding="utf-8")
    moving = tmp_path / "moving.txt"
    moving.write_text("before\n", encoding="utf-8")
    _patch_second_read(monkeypatch, moving, second=b"after, longer\n")

    result = run_inspect(str(tmp_path), root=tmp_path)

    declared = {entry["digest"] for entry in result.folder_manifest["files"]}
    assert result.chunks_manifest["chunks"]
    assert all(c["file_digest"] in declared for c in result.chunks_manifest["chunks"])


def test_stable_run_is_unchanged(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")

    result = run_inspect(str(tmp_path), root=tmp_path)

    assert result.folder_manifest["coverage"] == [1, 1]
    assert "changed_during_inspect" not in result.folder_manifest
    assert result.warnings == []
