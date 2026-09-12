from __future__ import annotations

import json
import subprocess
from pathlib import Path

from scripts.release import sync_release_notes as sync


def completed(*, code: int = 0, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(["gh"], code, stdout=stdout, stderr="")


def test_check_reports_observed_when_remote_matches(tmp_path: Path, monkeypatch) -> None:
    path = sync.canonical_notes(tmp_path, "4.20.0")
    path.parent.mkdir(parents=True)
    path.write_text("# notes\n", encoding="utf-8")
    monkeypatch.setattr(sync, "_run", lambda *args, **kwargs: completed(stdout=json.dumps({"body": "# notes\r\n"})))

    assert sync.main(["4.20.0", "--root", str(tmp_path)]) == 0


def test_check_reports_drift_without_mutating(tmp_path: Path, monkeypatch) -> None:
    path = sync.canonical_notes(tmp_path, "4.20.0")
    path.parent.mkdir(parents=True)
    path.write_text("new\n", encoding="utf-8")
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: str, **kwargs):
        calls.append(args)
        return completed(stdout=json.dumps({"body": "old\n"}))

    monkeypatch.setattr(sync, "_run", fake_run)
    assert sync.main(["4.20.0", "--root", str(tmp_path)]) == 1
    assert all("edit" not in call for call in calls)


def test_missing_remote_evidence_is_unobserved(tmp_path: Path, monkeypatch) -> None:
    path = sync.canonical_notes(tmp_path, "4.20.0")
    path.parent.mkdir(parents=True)
    path.write_text("notes\n", encoding="utf-8")
    monkeypatch.setattr(sync, "_run", lambda *args, **kwargs: None)

    assert sync.main(["4.20.0", "--root", str(tmp_path)]) == 2


def test_apply_edits_then_requires_matching_readback(tmp_path: Path, monkeypatch) -> None:
    path = sync.canonical_notes(tmp_path, "4.20.0")
    path.parent.mkdir(parents=True)
    path.write_text("new\n", encoding="utf-8")
    views = iter(["old\n", "new\n"])
    calls: list[tuple[str, ...]] = []

    def fake_run(*args: str, **kwargs):
        calls.append(args)
        if "view" in args:
            return completed(stdout=json.dumps({"body": next(views)}))
        assert "edit" in args
        return completed()

    monkeypatch.setattr(sync, "_run", fake_run)
    assert sync.main(["4.20.0", "--root", str(tmp_path), "--apply"]) == 0
    assert any("edit" in call for call in calls)
    assert sum("view" in call for call in calls) == 2


def test_apply_never_claims_success_without_post_write_readback(tmp_path: Path, monkeypatch) -> None:
    path = sync.canonical_notes(tmp_path, "4.20.0")
    path.parent.mkdir(parents=True)
    path.write_text("new\n", encoding="utf-8")
    view_count = 0

    def fake_run(*args: str, **kwargs):
        nonlocal view_count
        if "view" in args:
            view_count += 1
            if view_count == 1:
                return completed(stdout=json.dumps({"body": "old\n"}))
            return None
        return completed()

    monkeypatch.setattr(sync, "_run", fake_run)
    assert sync.main(["4.20.0", "--root", str(tmp_path), "--apply"]) == 2
