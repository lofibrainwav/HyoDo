"""Evidence-binding contracts for the `hyodo inspect` chunk pass.

The chunk pass re-reads every chunkable file. These tests pin down what
happens when that second read differs from the first:

- a second-read failure is recorded explicitly, never silently dropped;
- bytes that changed between passes are secret-scanned again before any
  chunk is built from them;
- every chunk's ``file_digest`` binds to a digest the manifest declares.
"""

from __future__ import annotations

import json

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


def _declared_digests(manifest):
    declared = {entry["digest"] for entry in manifest["files"]}
    declared |= {entry["digest_after"] for entry in manifest.get("changed_during_inspect", [])}
    return declared


def test_second_read_failure_is_explicitly_unobserved(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_text("stable\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("other\n", encoding="utf-8")
    _patch_second_read(monkeypatch, target, second=PermissionError("gone"))

    result = run_inspect(str(tmp_path), root=tmp_path)
    manifest = result.folder_manifest

    failures = manifest.get("unreadable_during_inspect")
    assert failures == [{"path": "a.txt", "reason": "read_error:PermissionError"}]
    assert any("a.txt" in line and "unreadable during inspect" in line for line in result.warnings)
    # The pass-1 digest is still reported; nothing is chunked from the missing read.
    a_digest = next(f["digest"] for f in manifest["files"] if f["path"] == "a.txt")
    assert all(c["file_digest"] != a_digest for c in result.chunks_manifest["chunks"])
    assert "unreadable during inspect: 1" in render_report_md(result)


def test_second_read_failure_keeps_exit_zero_contract(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_text("stable\n", encoding="utf-8")
    _patch_second_read(monkeypatch, target, second=OSError("flaky"))

    result = runner.invoke(app, ["inspect", str(tmp_path), "--root", str(tmp_path)])

    assert result.exit_code == 0, result.output
    folder = json.loads((tmp_path / ".hyodo" / "folder-manifest.json").read_text("utf-8"))
    assert folder["unreadable_during_inspect"][0]["path"] == "a.txt"


def test_bytes_that_become_secret_shaped_are_not_chunked(tmp_path, monkeypatch):
    target = tmp_path / "config.txt"
    target.write_text("harmless = 1\n", encoding="utf-8")
    secret_bytes = f"aws_key = {FAKE_AWS_KEY}\n".encode()
    _patch_second_read(monkeypatch, target, second=secret_bytes)

    result = run_inspect(str(tmp_path), root=tmp_path)
    manifest = result.folder_manifest

    changed = manifest["changed_during_inspect"]
    assert len(changed) == 1
    assert changed[0]["path"] == "config.txt"
    assert changed[0]["secret_shaped_after"] is True
    new_digest = changed[0]["digest_after"]
    assert all(c["file_digest"] != new_digest for c in result.chunks_manifest["chunks"])
    assert result.chunks_manifest["chunks"] == []
    assert any("secret-shaped" in line for line in result.warnings)


def test_changed_clean_bytes_are_scanned_and_bound(tmp_path, monkeypatch):
    target = tmp_path / "notes.txt"
    target.write_text("draft one\n", encoding="utf-8")
    _patch_second_read(monkeypatch, target, second=b"draft two\n")

    result = run_inspect(str(tmp_path), root=tmp_path)
    changed = result.folder_manifest["changed_during_inspect"]

    assert changed[0]["secret_shaped_after"] is False
    chunk_digests = {c["file_digest"] for c in result.chunks_manifest["chunks"]}
    assert chunk_digests == {changed[0]["digest_after"]}


def test_every_chunk_binds_to_a_declared_digest(tmp_path, monkeypatch):
    (tmp_path / "keep.txt").write_text("k" * 5000, encoding="utf-8")
    moving = tmp_path / "moving.txt"
    moving.write_text("before\n", encoding="utf-8")
    _patch_second_read(monkeypatch, moving, second=b"after, longer\n")

    result = run_inspect(str(tmp_path), root=tmp_path)

    declared = _declared_digests(result.folder_manifest)
    assert result.chunks_manifest["chunks"]
    assert all(c["file_digest"] in declared for c in result.chunks_manifest["chunks"])


def test_unchanged_run_has_no_new_keys(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")

    manifest = run_inspect(str(tmp_path), root=tmp_path).folder_manifest

    assert "unreadable_during_inspect" not in manifest
    assert "changed_during_inspect" not in manifest


def test_file_swapped_for_outside_symlink_is_not_chunked(tmp_path, monkeypatch):
    """A regular file replaced by a symlink to outside the tree between passes
    must not have the outside bytes chunked under the tree's manifest."""
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
    assert result.folder_manifest["unreadable_during_inspect"] == [
        {"path": "a.txt", "reason": "symlink_outside_root"}
    ]
