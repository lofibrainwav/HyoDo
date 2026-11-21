"""Independent P0 cross-check suite for the hyodo inspect chunk pass.

Ported from a separately written repair candidate (40 cases across the eval,
inspect and cross-lane files) so two independent implementations are held to
the same observable contract. Runs against the real modules; nothing is stubbed
unless a test says so.
"""

from pathlib import Path

import pytest

from hyodo import inspect as ins


def run(root):
    return ins.run_inspect(str(root), root=root)


@pytest.mark.parametrize("change", ["io_error", "changed_clean", "changed_secret"])
def test_mutated_file_is_not_complete_or_chunked(tmp_path, monkeypatch, change):
    target = tmp_path / "a.txt"
    target.write_bytes(b"original")
    (tmp_path / "b.txt").write_bytes(b"stable")
    read = Path.read_bytes
    calls = 0

    def second_read(path):
        nonlocal calls
        if path == target:
            calls += 1
            if calls == 2:
                if change == "io_error":
                    raise PermissionError("synthetic")
                return b"AKIA" + b"ABCDEFGHIJKLMNOP" if change == "changed_secret" else b"new bytes"
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", second_read)
    r = run(tmp_path)
    assert calls == 2
    assert r.folder_manifest["coverage"] == [1, 2]
    assert {x["path"] for x in r.folder_manifest["unreadable"]} == {"a.txt"}
    assert {x["path"] for x in r.folder_manifest["files"]} == {"b.txt"}
    assert [x["file_digest"] for x in r.chunks_manifest["chunks"]] == [
        ins.content_digest(b"stable")
    ]
    assert r.warnings
    if change != "io_error":
        assert len(r.folder_manifest["changed_during_inspect"]) == 1


def test_short_digest_collision_does_not_mask_change(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_bytes(b"original")
    read = Path.read_bytes
    calls = 0

    def mutate(path):
        nonlocal calls
        if path == target:
            calls += 1
            if calls == 2:
                return b"changed"
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", mutate)
    monkeypatch.setattr(ins, "content_digest", lambda _: "000000000000")
    r = run(tmp_path)
    assert r.folder_manifest["coverage"] == [0, 1]
    assert r.folder_manifest["changed_during_inspect"]
    assert not r.chunks_manifest["chunks"]


def test_stable_and_chunks(tmp_path):
    data = b"a" * 9000
    (tmp_path / "a.txt").write_bytes(data)
    (tmp_path / "empty").write_bytes(b"")
    r = run(tmp_path)
    assert r.folder_manifest["coverage"] == [2, 2]
    assert not r.warnings
    chunks = r.chunks_manifest["chunks"]
    assert len(chunks) == 4
    assert [c["byte_range"] for c in chunks][:3] == [[0, 4096], [4096, 8192], [8192, 9000]]
    assert all(set(c) == {"chunk_id", "file_digest", "byte_range", "chunk_digest"} for c in chunks)
    assert all(
        c["chunk_digest"] == ins.content_digest(data[slice(*c["byte_range"])]) for c in chunks[:3]
    )


def test_secret_and_ignored(tmp_path):
    (tmp_path / "secret.txt").write_text("AKIA" + "ABCDEFGHIJKLMNOP")
    (tmp_path / "skip.log").write_text("irrelevant")
    r = ins.run_inspect(str(tmp_path), root=tmp_path, ignore=["*.log"])
    assert r.folder_manifest["coverage"] == [1, 1]
    assert len(r.folder_manifest["files"]) == 2
    assert not r.chunks_manifest["chunks"]


def test_first_read_error(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_text("a")
    read = Path.read_bytes

    def fail(path):
        if path == target:
            raise PermissionError("synthetic")
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", fail)
    r = run(tmp_path)
    assert r.folder_manifest["coverage"] == [0, 1]
    assert r.folder_manifest["unreadable"][0]["reason"] == "read_error:PermissionError"


def test_existing_change_warning_contract(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_bytes(b"original")
    read = Path.read_bytes
    calls = 0

    def mutate(path):
        nonlocal calls
        if path == target:
            calls += 1
            if calls > 1:
                return b"changed"
        return read(path)

    monkeypatch.setattr(Path, "read_bytes", mutate)
    r = run(tmp_path)
    assert len(r.folder_manifest["changed_during_inspect"]) == 1
    assert any("changed during inspect" in w for w in r.warnings)


def test_same_content_stable(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"same")
    (tmp_path / "b.txt").write_bytes(b"same")
    r = run(tmp_path)
    assert r.folder_manifest["coverage"] == [2, 2]
    assert len(r.chunks_manifest["chunks"]) == 2
