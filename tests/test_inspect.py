"""Tests for `hyodo inspect` (Stage 2 package 2-B, field-deployment absorption).

Covers the pure engine in `hyodo/inspect.py` and the `hyodo inspect` CLI
surface in `hyodo/cli/main.py`. The five spec test-plan rows come first, then
the additional rows from the implementation brief (ignore globs, symlinks,
determinism, contiguous chunk byte ranges, remote inventory, write failure).
"""

from __future__ import annotations

import json
import os

import pytest
from typer.testing import CliRunner

from hyodo.cli.main import app
from hyodo.inspect import (
    RemoteInventoryError,
    load_remote_inventory,
    render_report_json,
    render_report_md,
    run_inspect,
    write_manifests,
)

runner = CliRunner()

FAKE_AWS_KEY = "AKIAABCDEFGHIJKLMNOP"


# --- Spec test-plan rows (docs/superpowers/specs/.../2-B table) -----------


def test_fde_evidence_spine_coverage_is_3_3():
    """`hyodo inspect examples/fde-evidence-spine` reports coverage [3, 3]."""
    result = run_inspect("examples/fde-evidence-spine", root=".")
    assert result.folder_manifest["coverage"] == [3, 3]
    assert len(result.folder_manifest["files"]) == 3
    assert result.folder_manifest["unreadable"] == []


def test_unreadable_file_listed_and_counted_in_expected(tmp_path):
    """An unreadable file is listed under `unreadable` and still counts toward expected."""
    readable = tmp_path / "a.txt"
    readable.write_text("hello\n", encoding="utf-8")
    blocked = tmp_path / "blocked.txt"
    blocked.write_text("secretless\n", encoding="utf-8")
    blocked.chmod(0o000)
    try:
        if os.access(blocked, os.R_OK):
            pytest.skip("running as a user that bypasses file permissions (e.g. root)")
        result = run_inspect(str(tmp_path), root=tmp_path)
    finally:
        blocked.chmod(0o644)

    observed, expected = result.folder_manifest["coverage"]
    assert expected == 2
    assert observed == 1
    reasons = {u["path"]: u["reason"] for u in result.folder_manifest["unreadable"]}
    assert any(p.endswith("blocked.txt") for p in reasons)
    assert reasons[next(p for p in reasons if p.endswith("blocked.txt"))].startswith("read_error:")


def test_no_chunk_entry_ever_carries_text_or_body_key():
    """No entry in chunks-manifest.json ever carries a text/body key."""
    result = run_inspect("examples/fde-evidence-spine", root=".")
    for chunk in result.chunks_manifest["chunks"]:
        assert set(chunk.keys()) == {"chunk_id", "file_digest", "byte_range", "chunk_digest"}
        assert "text" not in chunk
        assert "body" not in chunk


def test_secret_shaped_file_excluded_from_chunks_reported_by_digest_only(tmp_path):
    """A safe-flagged secret-shaped file is excluded from chunking, reported by digest+location."""
    secret_file = tmp_path / "leaked.env"
    secret_file.write_text(f"aws_key = {FAKE_AWS_KEY}\n", encoding="utf-8")
    clean_file = tmp_path / "clean.txt"
    clean_file.write_text("nothing to see here\n", encoding="utf-8")

    result = run_inspect(str(tmp_path), root=tmp_path)

    secret_entries = [f for f in result.folder_manifest["files"] if f["secret_shaped"]]
    assert len(secret_entries) == 1
    assert secret_entries[0]["path"].endswith("leaked.env")
    assert "digest" in secret_entries[0]
    assert secret_entries[0]["digest"]
    # Excluded from chunking.
    secret_digest = secret_entries[0]["digest"]
    assert all(c["file_digest"] != secret_digest for c in result.chunks_manifest["chunks"])
    # Still counted as observed (it was digested).
    observed, expected = result.folder_manifest["coverage"]
    assert observed == expected == 2


def test_missing_path_exits_1_with_no_manifest_written(tmp_path):
    """A missing/non-directory `<path>` exits 1 with no manifest written."""
    missing = tmp_path / "does-not-exist"
    result = runner.invoke(app, ["inspect", str(missing), "--root", str(tmp_path)])
    assert result.exit_code == 1
    assert not (tmp_path / ".hyodo").exists()


def test_non_directory_path_exits_1(tmp_path):
    """A file (not a directory) given as `<path>` also exits 1, no manifest written."""
    a_file = tmp_path / "just_a_file.txt"
    a_file.write_text("x", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(a_file), "--root", str(tmp_path)])
    assert result.exit_code == 1
    assert not (tmp_path / ".hyodo").exists()


# --- Additional brief-required rows ----------------------------------------


def test_ignore_glob_listed_but_excluded_from_chunks_and_expected(tmp_path):
    (tmp_path / "keep.txt").write_text("keep me\n", encoding="utf-8")
    (tmp_path / "skip.log").write_text("noisy log\n", encoding="utf-8")

    result = run_inspect(str(tmp_path), root=tmp_path, ignore=["*.log"])

    entries = {f["path"].split("/")[-1]: f for f in result.folder_manifest["files"]}
    assert entries["skip.log"]["ignored"] is True
    assert entries["skip.log"]["ignore_reason"] == "pattern:*.log"
    assert entries["keep.txt"]["ignored"] is False

    # Excluded from coverage's expected count.
    observed, expected = result.folder_manifest["coverage"]
    assert expected == 1
    assert observed == 1

    # Excluded from chunks.
    ignored_digest = entries["skip.log"]["digest"]
    assert all(c["file_digest"] != ignored_digest for c in result.chunks_manifest["chunks"])


def test_symlink_outside_root_is_unreadable(tmp_path):
    outside = tmp_path.parent / f"outside-target-{tmp_path.name}.txt"
    outside.write_text("outside content\n", encoding="utf-8")
    root_dir = tmp_path / "root"
    root_dir.mkdir()
    link = root_dir / "escape.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")

    try:
        result = run_inspect(str(root_dir), root=root_dir)
        unreadable = result.folder_manifest["unreadable"]
        assert any(u["reason"] == "symlink_outside_root" for u in unreadable)
        # The unreadable entry names the symlink's OWN path, never the
        # outside target's path (the bug this test guards against).
        entry = next(u for u in unreadable if u["reason"] == "symlink_outside_root")
        assert entry["path"] == "escape.txt"
        assert "outside-target" not in entry["path"]
        observed, expected = result.folder_manifest["coverage"]
        assert expected == 1
        assert observed == 0
    finally:
        outside.unlink(missing_ok=True)


def test_symlink_outside_root_under_shared_root_ancestor(tmp_path):
    """`--root` is an ancestor of `<path>`; the reported path stays the symlink's own."""
    outside = tmp_path / "outside-target.txt"
    outside.write_text("outside content\n", encoding="utf-8")
    sub_dir = tmp_path / "project" / "sub"
    sub_dir.mkdir(parents=True)
    link = sub_dir / "escape.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")

    result = run_inspect(str(sub_dir), root=tmp_path)
    unreadable = result.folder_manifest["unreadable"]
    entry = next(u for u in unreadable if u["reason"] == "symlink_outside_root")
    assert entry["path"] == "project/sub/escape.txt"


def test_symlink_inside_root_to_sibling_file_creates_two_distinct_entries(tmp_path):
    """A same-root symlink to a file gets its own entry; the target keeps its own too."""
    target_file = tmp_path / "regular.txt"
    target_file.write_text("shared content\n", encoding="utf-8")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(target_file)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")

    result = run_inspect(str(tmp_path), root=tmp_path)
    files = result.folder_manifest["files"]
    by_path = {f["path"]: f for f in files}

    assert set(by_path) == {"regular.txt", "link.txt"}
    assert by_path["regular.txt"]["symlink_target"] is None
    assert by_path["link.txt"]["symlink_target"] == "regular.txt"
    # Same content -> same digest, but they are two distinct entries.
    assert by_path["regular.txt"]["digest"] == by_path["link.txt"]["digest"]

    observed, expected = result.folder_manifest["coverage"]
    assert observed == expected == 2


def test_dir_symlink_unreadable_path_is_symlinks_own_path(tmp_path):
    real_dir = tmp_path / "real_dir"
    real_dir.mkdir()
    (real_dir / "inner.txt").write_text("inner\n", encoding="utf-8")
    link = tmp_path / "dir_link"
    try:
        link.symlink_to(real_dir, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported in this environment")

    result = run_inspect(str(tmp_path), root=tmp_path)
    unreadable = result.folder_manifest["unreadable"]
    entry = next(u for u in unreadable if u["reason"] == "symlink_dir_skipped")
    assert entry["path"] == "dir_link"
    assert "real_dir" not in entry["path"]


def test_determinism_two_runs_identical_except_generated_at(tmp_path):
    (tmp_path / "a.txt").write_text("aaa\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("bbb bbb bbb\n", encoding="utf-8")

    first = run_inspect(str(tmp_path), root=tmp_path)
    second = run_inspect(str(tmp_path), root=tmp_path)

    fm1 = dict(first.folder_manifest)
    fm2 = dict(second.folder_manifest)
    fm1.pop("generated_at")
    fm2.pop("generated_at")
    assert fm1 == fm2
    assert first.chunks_manifest == second.chunks_manifest


def test_chunk_byte_ranges_cover_whole_file_contiguously(tmp_path):
    big = tmp_path / "big.bin"
    big.write_bytes(os.urandom(4096 * 2 + 137))

    result = run_inspect(str(tmp_path), root=tmp_path)
    chunks = sorted(result.chunks_manifest["chunks"], key=lambda c: c["byte_range"][0])
    assert len(chunks) == 3
    expected_start = 0
    for chunk in chunks:
        start, end = chunk["byte_range"]
        assert start == expected_start
        expected_start = end
    assert expected_start == 4096 * 2 + 137


def test_binary_file_is_chunked_not_marked_unreadable(tmp_path):
    (tmp_path / "image.bin").write_bytes(bytes(range(256)) * 4)
    result = run_inspect(str(tmp_path), root=tmp_path)
    assert result.folder_manifest["unreadable"] == []
    assert len(result.chunks_manifest["chunks"]) >= 1


def test_remote_inventory_happy_path(tmp_path):
    inv = tmp_path / "drive-inventory.json"
    inv.write_text(
        json.dumps(
            {
                "schema": "hyodo.remote-inventory/v1",
                "source": "drive:Finance-2026",
                "items": [
                    {
                        "id": "abc123",
                        "name": "Q3 report.pdf",
                        "mime_type": "application/pdf",
                        "modified_at": "2026-08-01T00:00:00+00:00",
                        "declared_digest": "deadbeefcafe",
                        "revision": "7",
                        "shared_outside": True,
                    },
                    {"id": "def456", "name": "notes.txt"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "local.txt").write_text("local content\n", encoding="utf-8")

    result = run_inspect(str(tmp_path), root=tmp_path, remote_inventory_paths=[str(inv)])

    remote = result.folder_manifest["remote"]
    assert len(remote) == 1
    row = remote[0]
    assert row["source"] == "drive:Finance-2026"
    assert row["items_listed"] == 2
    assert row["items_with_declared_digest"] == 1
    assert row["items_shared_outside"] == 1

    # Never enters coverage, never produces chunks: the walked tree here has
    # two real files (local.txt and the inventory file itself, since it lives
    # under tmp_path); the remote inventory's declared items are separate.
    observed, expected = result.folder_manifest["coverage"]
    assert observed == expected == 2
    assert len(result.chunks_manifest["chunks"]) == 2


def test_remote_inventory_malformed_raises_before_any_write(tmp_path):
    bad_inv = tmp_path / "bad-inventory.json"
    bad_inv.write_text(json.dumps({"schema": "wrong-schema", "source": "x"}), encoding="utf-8")
    (tmp_path / "local.txt").write_text("hi\n", encoding="utf-8")

    with pytest.raises(RemoteInventoryError):
        run_inspect(str(tmp_path), root=tmp_path, remote_inventory_paths=[str(bad_inv)])

    # CLI path: exit 1, no manifest written.
    result = runner.invoke(
        app,
        [
            "inspect",
            str(tmp_path),
            "--root",
            str(tmp_path),
            "--remote-inventory",
            str(bad_inv),
        ],
    )
    assert result.exit_code == 1
    assert not (tmp_path / ".hyodo").exists()


def test_load_remote_inventory_missing_file_raises(tmp_path):
    with pytest.raises(RemoteInventoryError):
        load_remote_inventory(str(tmp_path / "nope.json"))


def test_write_failure_exits_2_when_hyodo_dir_is_a_file(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")
    blocker = tmp_path / ".hyodo"
    blocker.write_text("not a directory", encoding="utf-8")

    result = runner.invoke(app, ["inspect", str(tmp_path), "--root", str(tmp_path)])
    assert result.exit_code == 2


def test_write_failure_exits_2_when_root_read_only(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")
    tmp_path.chmod(0o500)
    try:
        if os.access(tmp_path, os.W_OK):
            pytest.skip("running as a user that bypasses directory permissions (e.g. root)")
        result = runner.invoke(app, ["inspect", str(tmp_path), "--root", str(tmp_path)])
        assert result.exit_code == 2
    finally:
        tmp_path.chmod(0o700)


def test_report_json_is_the_folder_manifest():
    result = run_inspect("examples/fde-evidence-spine", root=".")
    payload = json.loads(render_report_json(result))
    assert payload == result.folder_manifest


def test_report_md_contains_coverage_line():
    result = run_inspect("examples/fde-evidence-spine", root=".")
    text = render_report_md(result)
    assert "3/3 files digested" in text


def test_cli_report_md_default(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")
    result = runner.invoke(app, ["inspect", str(tmp_path), "--root", str(tmp_path)])
    assert result.exit_code == 0
    assert "1/1 files digested" in result.output
    assert (tmp_path / ".hyodo" / "folder-manifest.json").exists()
    assert (tmp_path / ".hyodo" / "chunks-manifest.json").exists()


def test_cli_report_json(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")
    result = runner.invoke(
        app, ["inspect", str(tmp_path), "--root", str(tmp_path), "--report", "json"]
    )
    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["schema"] == "hyodo.folder-manifest/v1"


def test_write_manifests_roundtrip(tmp_path):
    (tmp_path / "a.txt").write_text("hi\n", encoding="utf-8")
    result = run_inspect(str(tmp_path), root=tmp_path)
    folder_path, chunks_path = write_manifests(result, tmp_path)
    assert json.loads(folder_path.read_text(encoding="utf-8")) == result.folder_manifest
    assert json.loads(chunks_path.read_text(encoding="utf-8")) == result.chunks_manifest


def test_changed_during_inspect_reported_without_failing(tmp_path, monkeypatch):
    """Simulate a whole-file digest mismatch between pass 1 and pass 2."""
    target = tmp_path / "a.txt"
    target.write_text("original\n", encoding="utf-8")

    from hyodo import inspect as inspect_mod

    call_count = {"n": 0}
    real_path_read_bytes = inspect_mod.Path.read_bytes

    def flaky_read_bytes(self):
        call_count["n"] += 1
        if self == target and call_count["n"] > 1:
            return b"changed content\n"
        return real_path_read_bytes(self)

    monkeypatch.setattr(inspect_mod.Path, "read_bytes", flaky_read_bytes)
    result = run_inspect(str(tmp_path), root=tmp_path)

    assert "changed_during_inspect" in result.folder_manifest
    changed = result.folder_manifest["changed_during_inspect"]
    assert len(changed) == 1
    assert changed[0]["path"].endswith("a.txt")
    assert result.warnings
    assert any("changed during inspect" in w for w in result.warnings)
