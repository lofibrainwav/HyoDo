from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_release_plan import init_checkout
from test_release_prepare import write_minimal_repo

from scripts.release.pipeline import PipelineExternalError, push_candidate, run_pipeline


def test_pipeline_is_zero_write_and_stops_at_plan(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "release/4.12.0")
    before = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    receipt = run_pipeline(tmp_path, "4.12.0")

    after = {
        path.relative_to(tmp_path): path.read_bytes()
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert receipt["result"] == "PASS"
    assert receipt["stage"] == "PLANNED"
    assert receipt["zero_write"] is True
    assert receipt["external_mutation"] is False
    assert receipt["mutations"] == []
    assert before == after
    json.dumps(receipt)


def test_pipeline_blocks_non_release_branch(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "main")

    receipt = run_pipeline(tmp_path, "4.12.0")

    assert receipt["result"] == "BLOCK"
    assert receipt["stage"] == "BLOCKED"
    assert receipt["plan"]["result"] == "BLOCK"


def test_pipeline_verification_failure_is_fail_closed(tmp_path: Path, monkeypatch) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "release/4.12.0")

    class Failed:
        returncode = 2
        stdout = "tests failed"
        stderr = "verification error"

    monkeypatch.setattr("scripts.release.pipeline._run_verification", lambda root: Failed())
    receipt = run_pipeline(tmp_path, "4.12.0", verify=True)

    assert receipt["result"] == "BLOCK"
    assert receipt["stage"] == "BLOCKED"
    assert receipt["stages"]["verify"] == "BLOCK"
    assert receipt["external_mutation"] is False


def test_external_stages_require_local_verification(tmp_path: Path) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "release/4.12.0")

    receipt = run_pipeline(tmp_path, "4.12.0", execute=True)

    assert receipt["result"] == "BLOCK"
    assert receipt["stage"] == "BLOCKED"
    assert receipt["external_mutation"] is False
    assert receipt["residuals"] == ["external stages require --verify"]


def test_push_candidate_refuses_remote_head_mismatch(tmp_path: Path, monkeypatch) -> None:
    write_minimal_repo(tmp_path)
    init_checkout(tmp_path, "feat/candidate")

    class Pushed:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("scripts.release.pipeline.subprocess.run", lambda *args, **kwargs: Pushed())
    monkeypatch.setattr("scripts.release.pipeline._branch", lambda root: "feat/candidate")
    monkeypatch.setattr("scripts.release.pipeline._remote_branch_sha", lambda root, branch: "wrong")

    with pytest.raises(PipelineExternalError, match="RECONCILIATION_REQUIRED"):
        push_candidate(tmp_path, candidate_sha="planned")
