"""The release pipeline must make a wrong-order publication impossible.

v4.21.2 was tagged and its GitHub Release was published by hand before the SBOM
evidence was attached. This repository uses immutable releases, so the Release
could never take the assets afterwards, and PyPI correctly refused the upload.
The workflows guarded PyPI; nothing guarded the one irreversible step.

These tests pin the publication half of the state machine and the pipeline
stage that owns it. Every wrong order below must be refused *before* the
irreversible call, and the fake remote records every mutation so a refusal that
still mutated would be caught.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.release import pipeline
from scripts.release.release_state import (
    RELEASE_STATES,
    ReleaseOrderError,
    require_state,
    start_publication_receipt,
    transition,
    validate_receipt,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "9.9.9"
TAG = f"v{VERSION}"
MAIN_SHA = "a" * 40

PUBLICATION_ORDER = [
    "MERGED",
    "TAGGED",
    "DRAFT_CREATED",
    "EVIDENCE_BUILT",
    "EVIDENCE_ATTACHED",
    "DRAFT_VERIFIED",
    "PUBLISHED",
    "PYPI_PUBLISHED",
    "PROVENANCE_VERIFIED",
    "INSTALL_VERIFIED",
    "READBACK_VERIFIED",
]
SBOM_ASSETS = ["sbom.cyclonedx.json", "sbom.cyclonedx.json.sha256"]
MUTATIONS = {"create_tag", "create_draft_release", "run_release_evidence", "publish_release"}


class FakeRemote:
    """In-memory GitHub + PyPI that behaves like the real gates, and logs calls."""

    def __init__(self, *, tag: dict | None = None, release: dict | None = None) -> None:
        self.tag = tag
        self.release = release
        self.calls: list[str] = []
        self.evidence_jobs = {"build-evidence": "success", "attach-assets": "success"}
        self.assets_verify = True
        self.drop_assets_before_publish = False

    # -- observations ---------------------------------------------------
    def observe_main(self) -> dict[str, str]:
        return {"sha": MAIN_SHA, "version": VERSION}

    def observe_tag(self, tag: str) -> dict | None:
        return self.tag

    def observe_release(self, tag: str) -> dict | None:
        if self.release is None:
            return None
        if self.drop_assets_before_publish and "verify_release_assets" in self.calls:
            return {**self.release, "assets": []}
        return dict(self.release)

    def verify_release_assets(self, tag: str) -> dict[str, Any]:
        self.calls.append("verify_release_assets")
        ok = self.assets_verify and self.release is not None
        return {"ok": ok and set(SBOM_ASSETS) <= set(self.release["assets"]), "detail": "fake"}

    # -- mutations ------------------------------------------------------
    def create_tag(self, tag: str, commit: str) -> None:
        self.calls.append("create_tag")
        self.tag = {"commit": commit, "verified": True}

    def create_draft_release(self, tag: str, notes: Path) -> None:
        self.calls.append("create_draft_release")
        self.release = {"draft": True, "assets": [], "immutable": False}

    def run_release_evidence(self, tag: str) -> dict[str, Any]:
        self.calls.append("run_release_evidence")
        # Mirrors release-evidence.yml: it only attaches to a draft.
        if self.release is None or not self.release["draft"]:
            return {
                "run_id": "1",
                "jobs": {"build-evidence": "success", "attach-assets": "failure"},
            }
        if self.evidence_jobs["attach-assets"] == "success":
            self.release["assets"] = list(SBOM_ASSETS)
        return {"run_id": "1", "jobs": dict(self.evidence_jobs)}

    def publish_release(self, tag: str) -> None:
        self.calls.append("publish_release")
        self.release = {**self.release, "draft": False, "immutable": True}

    def wait_publish_workflow(self, tag: str) -> dict[str, Any]:
        self.calls.append("wait_publish_workflow")
        return {
            "run_id": "2",
            "jobs": {"build": "success", "publish": "success", "verify": "success"},
        }

    def verify_pypi(self, version: str) -> dict[str, Any]:
        self.calls.append("verify_pypi")
        return {"provenance": True, "install": True, "detail": "fake"}

    def verify_release_chain(self, version: str) -> dict[str, Any]:
        self.calls.append("verify_release_chain")
        return {"ok": True, "detail": "fake"}

    def mutations(self) -> list[str]:
        return [call for call in self.calls if call in MUTATIONS]


def _run(remote: FakeRemote, **kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("notes", REPO_ROOT / "CHANGELOG.md")
    return pipeline.run_publication(VERSION, remote, **kwargs)


def _authorized(**kwargs: Any) -> dict[str, Any]:
    return {
        "execute": True,
        "authorize_ref": "human-approval-1",
        "authorize_sha": MAIN_SHA,
        **kwargs,
    }


# --- the state machine ------------------------------------------------------


def test_publication_states_are_explicit_and_ordered() -> None:
    start = RELEASE_STATES.index("MERGED")
    assert list(RELEASE_STATES[start:]) == PUBLICATION_ORDER


@pytest.mark.parametrize(
    "current", ["MERGED", "TAGGED", "DRAFT_CREATED", "EVIDENCE_BUILT", "EVIDENCE_ATTACHED"]
)
def test_publishing_before_the_draft_is_verified_is_an_invalid_transition(current: str) -> None:
    receipt = start_publication_receipt(VERSION, MAIN_SHA, "main readback")
    for state in PUBLICATION_ORDER[1 : PUBLICATION_ORDER.index(current) + 1]:
        receipt = transition(receipt, state, f"evidence for {state}")
    with pytest.raises(ValueError, match=f"{current} -> PUBLISHED"):
        transition(receipt, "PUBLISHED", "hand-published release")


def test_publication_receipt_validates_from_merged() -> None:
    receipt = start_publication_receipt(VERSION, MAIN_SHA, "main readback")
    for state in PUBLICATION_ORDER[1:]:
        receipt = transition(receipt, state, f"evidence for {state}")
    validate_receipt(receipt)
    assert receipt["state"] == "READBACK_VERIFIED"


def test_require_state_refuses_the_wrong_state() -> None:
    receipt = start_publication_receipt(VERSION, MAIN_SHA, "main readback")
    with pytest.raises(ReleaseOrderError, match="publish release requires DRAFT_VERIFIED"):
        require_state(receipt, "DRAFT_VERIFIED", "publish release")


def test_merge_stage_no_longer_claims_publication_readback() -> None:
    # After merge the pipeline has only read main back. READBACK_VERIFIED now
    # means the whole publication chain was read back, so it must not appear here.
    assert pipeline.post_merge_stage({"result": "PASS"}) == "MERGED"
    assert pipeline.post_merge_stage({"result": "BLOCK"}) == "BLOCKED"


# --- wrong orders the pipeline must refuse before the irreversible call ----


def test_replaying_4_21_2_is_refused_without_any_mutation() -> None:
    # The exact 4.21.2 remote: signed tag, Release already published, no SBOM.
    remote = FakeRemote(
        tag={"commit": MAIN_SHA, "verified": True},
        release={"draft": False, "assets": [], "immutable": True},
    )
    receipt = _run(remote, **_authorized())
    assert receipt["result"] == "BLOCK"
    assert receipt["state"] == "TAGGED"
    assert "already published" in " ".join(receipt["residuals"])
    assert remote.mutations() == []


def test_publish_is_refused_when_evidence_failed_to_attach() -> None:
    remote = FakeRemote()
    remote.evidence_jobs = {"build-evidence": "success", "attach-assets": "failure"}
    receipt = _run(remote, **_authorized())
    assert receipt["result"] == "BLOCK"
    assert receipt["state"] == "EVIDENCE_BUILT"
    assert "publish_release" not in remote.calls


def test_publish_is_refused_when_the_digest_does_not_verify() -> None:
    remote = FakeRemote()
    remote.assets_verify = False
    receipt = _run(remote, **_authorized())
    assert receipt["state"] == "EVIDENCE_ATTACHED"
    assert "publish_release" not in remote.calls


def test_publish_reobserves_the_draft_immediately_before_publishing() -> None:
    remote = FakeRemote()
    remote.drop_assets_before_publish = True
    receipt = _run(remote, **_authorized())
    assert receipt["state"] == "DRAFT_VERIFIED"
    assert receipt["result"] == "BLOCK"
    assert "publish_release" not in remote.calls


def test_publish_waits_for_human_authority() -> None:
    remote = FakeRemote()
    receipt = _run(remote, execute=True)
    assert receipt["state"] == "DRAFT_VERIFIED"
    assert receipt["stage"] == "WAITING_APPROVAL"
    assert "publish_release" not in remote.calls


def test_authority_for_another_commit_cannot_publish() -> None:
    remote = FakeRemote()
    receipt = _run(remote, **_authorized(authorize_sha="b" * 40))
    assert receipt["stage"] == "RECONCILIATION_REQUIRED"
    assert "publish_release" not in remote.calls


def test_a_tag_on_another_commit_blocks_before_the_draft() -> None:
    remote = FakeRemote(tag={"commit": "c" * 40, "verified": True})
    receipt = _run(remote, **_authorized())
    assert receipt["state"] == "MERGED"
    assert remote.mutations() == []


def test_an_unverified_tag_blocks_before_the_draft() -> None:
    remote = FakeRemote(tag={"commit": MAIN_SHA, "verified": False})
    receipt = _run(remote, **_authorized())
    assert receipt["state"] == "MERGED"
    assert remote.mutations() == []


def test_version_mismatch_blocks_at_merged() -> None:
    remote = FakeRemote()
    receipt = pipeline.run_publication("9.9.8", remote, notes=REPO_ROOT / "CHANGELOG.md")
    assert receipt["result"] == "BLOCK"
    assert remote.mutations() == []


# --- dry run and happy path -------------------------------------------------


def test_dry_run_performs_no_external_mutation() -> None:
    remote = FakeRemote()
    receipt = _run(remote)
    assert receipt["mode"] == "dry-run"
    assert remote.mutations() == []
    assert receipt["state"] == "DRAFT_VERIFIED"
    assert [m["kind"] for m in receipt["planned_mutations"]] == [
        "create_tag",
        "create_draft_release",
        "run_release_evidence",
    ]
    assert all(entry["simulated"] for entry in receipt["history"][1:])


def test_happy_path_walks_every_state_in_order() -> None:
    remote = FakeRemote()
    receipt = _run(remote, **_authorized())
    assert receipt["result"] == "PASS"
    assert [entry["state"] for entry in receipt["history"]] == PUBLICATION_ORDER
    assert remote.mutations() == [
        "create_tag",
        "create_draft_release",
        "run_release_evidence",
        "publish_release",
    ]
    validate_receipt(receipt)


# --- the workflows are wired to these states -------------------------------


def _jobs(workflow: str) -> dict[str, Any]:
    text = (REPO_ROOT / ".github" / "workflows" / workflow).read_text(encoding="utf-8")
    return yaml.safe_load(text)["jobs"]


def test_workflow_jobs_map_onto_the_publication_states() -> None:
    for workflow, mapping in pipeline.WORKFLOW_STATES.items():
        jobs = _jobs(workflow)
        for job, state in mapping.items():
            assert job in jobs, f"{workflow} has no job {job!r} for {state}"
            assert state in PUBLICATION_ORDER

    evidence = _jobs("release-evidence.yml")
    assert evidence["attach-assets"]["needs"] == "build-evidence"
    publish = _jobs("publish.yml")
    assert publish["publish"]["needs"] == "build"
    assert set(publish["verify"]["needs"]) == {"build", "publish"}
