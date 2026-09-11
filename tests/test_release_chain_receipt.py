"""The release chain receipt must never claim more, or less, than was measured.

`docs/releases/4.19.1.md` shipped with every chain item as `- [ ]` while the
tag was signed, the Release published, the SBOM attached and the package on
PyPI. The document said nothing had happened; all of it had.

An unchecked box is not a neutral placeholder. In a task list it asserts "not
done", so it is false from the moment the chain runs, and nothing brings a
writer back to it. `UNOBSERVED` carries the state the project already uses for
exactly this: not measured yet, which stays true until somebody measures.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.release.verify_release_chain import (
    CHAIN_STEPS,
    ChainStep,
    install_smoke_step,
    matching_run,
    receipt_drift,
    render_receipt,
    tag_step,
)

ROOT = Path(__file__).resolve().parent.parent


def _observed(name: str, evidence: str) -> ChainStep:
    return ChainStep(name=name, state="OBSERVED", evidence=evidence)


def _unobserved(name: str) -> ChainStep:
    return ChainStep(name=name, state="UNOBSERVED", evidence=None)


# --- the template may not ship promises ----------------------------------


def test_the_release_note_template_ships_no_unchecked_checkbox() -> None:
    # The rot starts here: `prepare_release` writes the receipt before the
    # chain runs, so anything shaped like "not done" is wrong the moment it
    # is. This is the regression guard for the 4.19.1 defect.
    template = (ROOT / "scripts" / "release" / "prepare_release.py").read_text(encoding="utf-8")
    assert "- [ ]" not in template


def test_a_freshly_prepared_receipt_reads_unobserved_not_false() -> None:
    steps = [_unobserved(step) for step in CHAIN_STEPS]
    receipt = render_receipt(steps, measured_at=None)
    assert "UNOBSERVED" in receipt
    assert "- [ ]" not in receipt
    assert "- [x]" not in receipt


# --- a measured receipt names its evidence -------------------------------


def test_an_observed_step_must_carry_the_evidence_that_observed_it() -> None:
    # The completed receipts in this repo name durable artifacts -- a tag and
    # its commit, a workflow run id. A bare tick is the thing that rots; the
    # identifier is what makes it checkable later.
    receipt = render_receipt(
        [_observed("Signed verified tag", "`v4.19.1` -> `a0a5dba`")],
        measured_at="2026-09-10T23:40:00Z",
    )
    assert "OBSERVED" in receipt
    assert "v4.19.1" in receipt
    assert "a0a5dba" in receipt


def test_an_observed_step_without_evidence_is_rejected() -> None:
    # Claiming OBSERVED with nothing to point at is exactly the assertion the
    # receipt exists to prevent.
    with pytest.raises(ValueError, match="evidence"):
        ChainStep(name="Signed verified tag", state="OBSERVED", evidence=None).validate()


def test_a_measured_receipt_records_when_it_was_measured() -> None:
    receipt = render_receipt(
        [_observed("Install smoke", "run `34542461485`")], measured_at="2026-09-10T23:40:00Z"
    )
    assert "2026-09-10T23:40:00Z" in receipt


# --- drift between the document and what was measured --------------------


def test_drift_is_reported_when_the_document_lags_the_measurement() -> None:
    document = render_receipt([_unobserved("Signed verified tag")], measured_at=None)
    measured = [_observed("Signed verified tag", "`v4.19.1` -> `a0a5dba`")]
    drift = receipt_drift(document, measured)
    assert drift, "a receipt saying UNOBSERVED for a step that was measured must report drift"
    assert "Signed verified tag" in drift[0]


def test_no_drift_when_the_document_already_matches() -> None:
    measured = [_observed("Signed verified tag", "`v4.19.1` -> `a0a5dba`")]
    document = render_receipt(measured, measured_at="2026-09-10T23:40:00Z")
    assert receipt_drift(document, measured) == []


# --- the shipped receipts ------------------------------------------------


def test_no_shipped_chain_receipt_still_uses_an_unchecked_box() -> None:
    # Scoped to the chain receipt, which is the section `prepare_release`
    # generates and the section that claims release state. 4.12.0 also ships
    # unchecked boxes, but under "First real release receipt checklist" --
    # an imperative plan written before the first release ever ran ("Create
    # a signed annotated tag", "Paste the receipt into issue #129"). Ticking
    # those now would be inventing observations nobody made; the next test
    # covers it instead.
    offenders = []
    for note in sorted((ROOT / "docs" / "releases").glob("*.md")):
        text = note.read_text(encoding="utf-8")
        if "## Release chain receipt" not in text:
            continue
        chain = text.split("## Release chain receipt", 1)[1].split("\n## ", 1)[0]
        if "- [ ]" in chain:
            offenders.append(note.name)
    assert offenders == [], f"unchecked chain boxes still shipped in: {offenders}"


def test_the_4_12_0_checklist_cannot_be_misread_as_a_finished_receipt() -> None:
    # v4.12.0 shipped. Its checklist is entirely unticked, so a reader
    # arriving cold would conclude the release never happened. The boxes stay
    # as written -- nobody measured them and forging ticks is the exact
    # failure this file exists to prevent -- but the document must say which
    # it is.
    note = (ROOT / "docs" / "releases" / "4.12.0.md").read_text(encoding="utf-8")
    assert "never reconciled" in note.lower()


def test_the_4_19_1_receipt_matches_what_was_actually_measured() -> None:
    # Every one of these was read back off GitHub and PyPI before being
    # written down: the tag verifies, the Release is published and carries
    # both assets, and 4.19.1 is the version PyPI serves.
    note = (ROOT / "docs" / "releases" / "4.19.1.md").read_text(encoding="utf-8")
    chain = note.split("## Release chain receipt", 1)[-1]
    assert "UNOBSERVED" not in chain.split("## ")[0] or "OBSERVED" in chain
    assert "a0a5dba" in chain, "the signed tag's commit is the receipt's anchor"
    assert re.search(r"sbom\.cyclonedx\.json", chain), "the SBOM asset is named"
    assert "4.19.1" in chain


def test_live_host_callbacks_stay_unobserved_in_the_release_note() -> None:
    # The one claim 4.19.1 must keep refusing to make. Fixture verification
    # is not a live callback, and the note says so.
    note = (ROOT / "docs" / "releases" / "4.19.1.md").read_text(encoding="utf-8")
    assert "UNOBSERVED" in note


# --- a run id must belong to the version it is cited for -----------------


def test_a_workflow_run_is_only_cited_when_it_ties_to_this_version() -> None:
    # The first draft of this script took the newest successful run of each
    # workflow. That is not a measurement -- the newest run may belong to a
    # different release, and citing it would put a wrong identifier in a
    # receipt whose whole job is to be recheckable.
    runs = [
        {"databaseId": 2, "conclusion": "success", "headBranch": "v9.9.9", "headSha": "ffffffff"},
        {"databaseId": 1, "conclusion": "success", "headBranch": "v4.19.1", "headSha": "a0a5dbad"},
    ]
    assert matching_run(runs, tag="v4.19.1", commit="a0a5dbad") == "1"


def test_a_run_matches_on_the_tag_commit_when_it_ran_from_a_branch() -> None:
    # `release-evidence.yml` is dispatched from `main`, so its `headBranch`
    # never carries the tag. Its `headSha` does.
    runs = [
        {"databaseId": 7, "conclusion": "success", "headBranch": "main", "headSha": "a0a5dbadf30c"}
    ]
    assert matching_run(runs, tag="v4.19.1", commit="a0a5dbadf30cdae0") == "7"


def test_no_run_is_cited_when_none_ties_to_this_version() -> None:
    runs = [{"databaseId": 3, "conclusion": "success", "headBranch": "main", "headSha": "deadbeef"}]
    assert matching_run(runs, tag="v4.19.1", commit="a0a5dbad") is None


def test_a_failed_run_is_never_cited_even_when_it_matches() -> None:
    runs = [
        {"databaseId": 4, "conclusion": "failure", "headBranch": "v4.19.1", "headSha": "a0a5dbad"}
    ]
    assert matching_run(runs, tag="v4.19.1", commit="a0a5dbad") is None


# --- unverifiable is not unsigned ----------------------------------------


def test_a_signed_but_unverifiable_tag_says_so_instead_of_going_silent() -> None:
    # v4.16.0 through v4.19.0 all carry a signature block, but only v4.19.1
    # verifies on this machine -- the earlier signer is not in the local
    # allowed-signers file. A bare `UNOBSERVED` would read as "unsigned",
    # which is a different and much worse claim than "not verifiable here".
    step = tag_step(tag="v4.18.0", commit="00d2fcd", signed=True, verified=False)
    assert step.state == "UNOBSERVED"
    rendered = step.render()
    assert "signed" in rendered.lower()
    assert "v4.18.0" in rendered


def test_a_verified_tag_is_observed_with_its_commit() -> None:
    step = tag_step(tag="v4.19.1", commit="a0a5dba", signed=True, verified=True)
    assert step.state == "OBSERVED"
    assert "a0a5dba" in step.render()


def test_a_missing_tag_is_unobserved_without_claiming_anything_about_signing() -> None:
    # The step's own name carries the word "Signed", so the claim to check is
    # the evidence: with no tag there is nothing to say about a signature.
    step = tag_step(tag="v9.9.9", commit=None, signed=False, verified=False)
    assert step.state == "UNOBSERVED"
    assert step.evidence is None


# --- a past release stays observed after a newer one ships ---------------


def test_install_smoke_asks_whether_this_version_is_on_pypi_not_whether_it_is_latest() -> None:
    # The first draft compared against `info.version`, the newest release
    # PyPI serves. Every receipt then rotted the moment the next version
    # shipped: 4.19.1's step flipped to UNOBSERVED an hour after it was
    # measured OBSERVED, purely because 4.19.2 landed. That is the exact
    # decay this file exists to prevent, reintroduced one field over.
    step = install_smoke_step("4.19.1", wheel_sha256="c4a3cb7c68246ddf" + "0" * 48)
    assert step.state == "OBSERVED"
    assert "4.19.1" in step.render()


def test_install_smoke_names_the_artifact_rather_than_the_moment() -> None:
    # A digest is true forever. "PyPI serves 4.19.2" is true only until it
    # does not.
    step = install_smoke_step("4.19.2", wheel_sha256="d80d1c792178c1b1" + "0" * 48)
    assert "d80d1c792178c1b1" in step.render()


def test_install_smoke_is_unobserved_when_the_version_is_absent() -> None:
    step = install_smoke_step("9.9.9", wheel_sha256=None)
    assert step.state == "UNOBSERVED"
    assert step.evidence is None
