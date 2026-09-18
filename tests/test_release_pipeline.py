from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_release_plan import init_checkout
from test_release_prepare import write_minimal_repo

from scripts.release.pipeline import (
    PipelineExternalError,
    _human_authority_gate,
    push_candidate,
    run_pipeline,
)


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
    assert receipt["five_w_one_h"]["who"]["model"] == "UNOBSERVED"
    assert receipt["five_w_one_h"]["why"]["authority_ref"] == "UNOBSERVED"
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


def test_human_exact_head_authority_allows_merge_without_verifier() -> None:
    result = _human_authority_gate(
        authorize_ref="human:jay:2026-09-17",
        authorize_sha="abc123",
        current_pr_head="abc123",
        remote_candidate_sha="abc123",
        ci_verified_sha="abc123",
        verifier={"approved": False},
    )

    assert result["result"] == "PASS"
    assert result["stage"] == "AUTHORIZED"
    assert result["verifier"]["status"] == "UNVERIFIED"
    assert result["verifier"]["residual"] == "verifier_missing"


def test_human_authority_sha_mismatch_requires_reconciliation() -> None:
    result = _human_authority_gate(
        authorize_ref="human:jay:2026-09-17",
        authorize_sha="old-head",
        current_pr_head="new-head",
        remote_candidate_sha="new-head",
        ci_verified_sha="new-head",
        verifier={"approved": False},
    )

    assert result["result"] == "BLOCK"
    assert result["stage"] == "RECONCILIATION_REQUIRED"


def test_pr_head_move_invalidates_existing_human_authority() -> None:
    result = _human_authority_gate(
        authorize_ref="human:jay:2026-09-17",
        authorize_sha="approved-head",
        current_pr_head="moved-head",
        remote_candidate_sha="moved-head",
        ci_verified_sha="approved-head",
        verifier={"approved": False},
    )

    assert result["stage"] == "RECONCILIATION_REQUIRED"
    assert result["head_binding"]["authorized_sha"] == "approved-head"


def test_verifier_evidence_does_not_replace_human_authority() -> None:
    result = _human_authority_gate(
        authorize_ref=None,
        authorize_sha=None,
        current_pr_head="abc123",
        remote_candidate_sha="abc123",
        ci_verified_sha="abc123",
        verifier={
            "approved": True,
            "reviewer": "verifier-agent",
            "review_id": 7,
            "review_commit_sha": "abc123",
        },
    )

    assert result["result"] == "WAIT"
    assert result["stage"] == "WAITING_APPROVAL"
    assert result["verifier"]["status"] == "VERIFIED"
