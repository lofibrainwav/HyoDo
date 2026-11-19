"""Independent P0 cross-check suite for eval and inspect together.

Ported from a separately written repair candidate (40 cases across the eval,
inspect and cross-lane files) so two independent implementations are held to
the same observable contract. Runs against the real modules; nothing is stubbed
unless a test says so.
"""

import json
from pathlib import Path

from hyodo import eval as ev
from hyodo import inspect as ins


def test_persisted_partial_inventory_never_looks_complete(tmp_path, monkeypatch):
    target = tmp_path / "a.txt"
    target.write_bytes(b"first")
    (tmp_path / "b.txt").write_bytes(b"stable")
    orig = Path.read_bytes
    calls = 0

    def read(p):
        nonlocal calls
        if p == target:
            calls += 1
            if calls == 2:
                raise OSError("synthetic late read failure")
        return orig(p)

    monkeypatch.setattr(Path, "read_bytes", read)
    r = ins.run_inspect(str(tmp_path), root=tmp_path)
    fp, cp = ins.write_manifests(r, tmp_path)
    f = json.loads(fp.read_text())
    c = json.loads(cp.read_text())
    assert f["coverage"] == [1, 2]
    assert len(f["unreadable"]) == 1
    assert len(c["chunks"]) == 1
    assert "1/2 files digested" in ins.render_report_md(r)
    assert json.loads(ins.render_report_json(r)) == f
    assert ev.score_case("exact", f["coverage"], [2, 2])[0] is False


def test_unchanged_tree_published_and_evaluated(tmp_path):
    (tmp_path / "a.txt").write_bytes(b"stable")
    r = ins.run_inspect(str(tmp_path), root=tmp_path)
    fp, cp = ins.write_manifests(r, tmp_path)
    f = json.loads(fp.read_text())
    c = json.loads(cp.read_text())
    assert ev.score_case("exact", f["coverage"], [1, 1])[0] is True
    assert c["chunks"][0]["file_digest"] == f["files"][0]["digest"]
