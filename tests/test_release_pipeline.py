from __future__ import annotations

import json
from pathlib import Path

import pytest
from test_release_plan import init_checkout
from test_release_prepare import write_minimal_repo

from scripts.release.pipeline import (
    PipelineExternalError,
    _check_snapshot,
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


@pytest.mark.parametrize("reference", [" ", "\n", "UNOBSERVED", "UNKNOWN"])
def test_placeholder_reference_cannot_authorize(reference: str) -> None:
    result = _human_authority_gate(
        authorize_ref=reference,
        authorize_sha="abc123",
        current_pr_head="abc123",
        remote_candidate_sha="abc123",
        ci_verified_sha="abc123",
        verifier={"approved": True},
    )
    assert result["result"] != "PASS"


@pytest.mark.parametrize("head", ["", " ", "UNOBSERVED", "UNKNOWN"])
def test_equal_missing_heads_are_not_verified_identity(head: str) -> None:
    result = _human_authority_gate(
        authorize_ref="human:test:explicit-grant",
        authorize_sha=head,
        current_pr_head=head,
        remote_candidate_sha=head,
        ci_verified_sha=head,
        verifier={"approved": True},
    )
    assert result["result"] != "PASS"


@pytest.mark.parametrize(
    ("conclusions", "expected", "passed", "skipped"),
    [
        ([], "BLOCK", 0, 0),
        (["skipped"], "BLOCK", 0, 1),
        (["skipped", "skipped"], "BLOCK", 0, 2),
        (["success", "skipped"], "BLOCK", 1, 1),
        (["failure", "skipped"], "BLOCK", 0, 1),
        (["success"], "PASS", 1, 0),
        (["success", "success"], "PASS", 2, 0),
    ],
)
def test_ci_skips_are_counted_separately(
    tmp_path: Path, monkeypatch, conclusions, expected, passed, skipped
) -> None:
    monkeypatch.setattr(
        "scripts.release.pipeline._gh_json",
        lambda *args: {
            "check_runs": [
                {"name": f"check-{index}", "status": "completed", "conclusion": conclusion}
                for index, conclusion in enumerate(conclusions)
            ]
        },
    )
    result = _check_snapshot(tmp_path, slug="fixture/repo", sha="abc123")
    assert result["result"] == expected
    assert result["passed"] == passed
    assert len(result["skipped"]) == skipped


SERIAL = "Goodness - Serial Full Suite (main)"
DEP_REVIEW = "Pull request dependency review"


def _runs(*pairs: tuple[str, str, str]) -> dict[str, object]:
    return {
        "check_runs": [
            {"name": name, "status": status, "conclusion": conclusion}
            for name, status, conclusion in pairs
        ]
    }


@pytest.mark.parametrize(
    ("event", "runs", "expected"),
    [
        # 1. PR: the main-only serial suite skipped, everything else green.
        ("pull_request", [("a", "completed", "success"), (SERIAL, "completed", "skipped")], "PASS"),
        # 2. PR: any other skipped check still blocks.
        ("pull_request", [("a", "completed", "success"), ("b", "completed", "skipped")], "BLOCK"),
        (
            "pull_request",
            [
                ("a", "completed", "success"),
                (SERIAL, "completed", "skipped"),
                ("b", "completed", "skipped"),
            ],
            "BLOCK",
        ),
        # 3. The serial suite failing, cancelled, or timing out blocks.
        (
            "pull_request",
            [("a", "completed", "success"), (SERIAL, "completed", "failure")],
            "BLOCK",
        ),
        (
            "pull_request",
            [("a", "completed", "success"), (SERIAL, "completed", "cancelled")],
            "BLOCK",
        ),
        (
            "pull_request",
            [("a", "completed", "success"), (SERIAL, "completed", "timed_out")],
            "BLOCK",
        ),
        ("push", [("a", "completed", "success"), (SERIAL, "completed", "failure")], "BLOCK"),
        # 4. Pending waits.
        ("pull_request", [("a", "in_progress", None), (SERIAL, "completed", "skipped")], "WAIT"),
        ("push", [("a", "completed", "success"), (SERIAL, "queued", None)], "WAIT"),
        # 5. Zero checks never pass; nor does an all-N/A PR.
        ("pull_request", [], "BLOCK"),
        ("push", [], "BLOCK"),
        ("pull_request", [(SERIAL, "completed", "skipped")], "BLOCK"),
        # 6. Main push: the serial suite must actually succeed.
        ("push", [("a", "completed", "success"), (SERIAL, "completed", "success")], "PASS"),
        ("push", [("a", "completed", "success"), (SERIAL, "completed", "skipped")], "BLOCK"),
        ("push", [("a", "completed", "success")], "BLOCK"),
        # Push: only the named PR-only check may be skipped.
        (
            "push",
            [
                ("a", "completed", "success"),
                (SERIAL, "completed", "success"),
                (DEP_REVIEW, "completed", "skipped"),
            ],
            "PASS",
        ),
        (
            "push",
            [
                ("a", "completed", "success"),
                (SERIAL, "completed", "success"),
                ("b", "completed", "skipped"),
            ],
            "BLOCK",
        ),
        (
            "push",
            [
                ("a", "completed", "success"),
                (SERIAL, "completed", "success"),
                (DEP_REVIEW, "completed", "skipped"),
                ("b", "completed", "skipped"),
            ],
            "BLOCK",
        ),
        (
            "push",
            [
                ("a", "completed", "success"),
                (SERIAL, "completed", "success"),
                (DEP_REVIEW, "completed", "failure"),
            ],
            "BLOCK",
        ),
        # The N/A lists are per event: dependency review skipped on a PR blocks.
        (
            "pull_request",
            [
                ("a", "completed", "success"),
                (SERIAL, "completed", "skipped"),
                (DEP_REVIEW, "completed", "skipped"),
            ],
            "BLOCK",
        ),
    ],
)
def test_main_only_check_policy(tmp_path: Path, monkeypatch, event, runs, expected) -> None:
    calls: list[tuple[str, ...]] = []

    def fake_gh_json(*args: str) -> dict[str, object]:
        calls.append(args)
        return _runs(*runs)

    monkeypatch.setattr("scripts.release.pipeline._gh_json", fake_gh_json)
    result = _check_snapshot(tmp_path, slug="fixture/repo", sha="abc123", event=event)
    assert result["result"] == expected
    # Read the whole check set, not the API's default first page.
    assert calls[0][1].endswith("check-runs?per_page=100")


def test_pr_serial_skip_is_expected_na_not_a_skip(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "scripts.release.pipeline._gh_json",
        lambda *args: _runs(("a", "completed", "success"), (SERIAL, "completed", "skipped")),
    )
    result = _check_snapshot(tmp_path, slug="fixture/repo", sha="abc123")
    assert result["expected_na"] == [SERIAL]
    assert result["skipped"] == []


def test_unknown_ci_event_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown CI event"):
        _check_snapshot(tmp_path, slug="fixture/repo", sha="abc123", event="schedule")


def test_expected_na_table_matches_workflow_event_gates() -> None:
    """Each expected-N/A name is a job gated to run only on the other event."""
    import re

    from scripts.release.pipeline import EXPECTED_NA_BY_EVENT

    root = Path(__file__).resolve().parents[1]
    jobs: dict[str, str] = {}
    for workflow in (root / ".github" / "workflows").glob("*.yml"):
        text = workflow.read_text(encoding="utf-8")
        for match in re.finditer(
            r'^    name: "?(?P<name>[^"\n]+?)"?\n    if: (?P<cond>.+)$', text, re.M
        ):
            jobs[match["name"]] = match["cond"]
    gate_for = {
        "pull_request": "github.event_name == 'push'",
        "push": "github.event_name == 'pull_request'",
    }
    for event, names in EXPECTED_NA_BY_EVENT.items():
        for name in names:
            assert name in jobs, f"{name} not found as a gated job"
            assert jobs[name].startswith(gate_for[event]), (name, jobs[name])
