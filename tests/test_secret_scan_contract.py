"""The secret scan must mean the same thing on every event, and its baseline
must never be able to hide a secret that is present today.

The job is called "Historical and working-tree secret scan", but the action it
used derived its scope from the triggering event: a push to main scanned one
commit while a manual run scanned the whole history. The same tree could pass
or fail depending on how the run started, so a green tick on main was evidence
about one commit, not about the history the name promised.

These tests pin the repaired contract: one full-history scan, one working-tree
scan, neither conditioned on the event, plus a planted-secret check proving the
baseline suppresses only what it names.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "security.yml"
BASELINE_PATH = REPO_ROOT / ".gitleaksignore"

#: gitleaks names a finding differently depending on the scan. A history scan
#: produces ``<commit sha>:<path>:<rule id>:<line>``; a ``--no-git`` scan has no
#: commit and produces ``<path>:<rule id>:<line>``. Both name one line of one
#: file under one rule, which is the property that matters: anything shorter --
#: a bare path, a glob, a rule name -- would suppress a class rather than a
#: finding, and could hide a secret added later.
HISTORY_FINGERPRINT = re.compile(r"^[0-9a-f]{40}:[^:]+:[^:]+:\d+$")
WORKING_TREE_FINGERPRINT = re.compile(r"^[^:]+:[^:]+:\d+$")


def _names_one_finding(entry: str) -> bool:
    return bool(HISTORY_FINGERPRINT.match(entry) or WORKING_TREE_FINGERPRINT.match(entry))


def _secrets_job() -> dict:
    data = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return data["jobs"]["secrets"]


def _run_steps() -> list[tuple[str, str]]:
    return [
        (step.get("name", "<unnamed>"), step["run"])
        for step in _secrets_job()["steps"]
        if "run" in step
    ]


def test_job_still_claims_history_and_working_tree() -> None:
    assert _secrets_job()["name"] == "Historical and working-tree secret scan"


def test_history_and_working_tree_are_both_scanned() -> None:
    scripts = dict(_run_steps())

    history = scripts.get("Scan full history")
    assert history is not None, "no full-history scan step"
    assert "detect" in history
    assert "--no-git" not in history, "the history scan must read git history"

    working_tree = scripts.get("Scan working tree")
    assert working_tree is not None, "no working-tree scan step"
    assert "--no-git" in working_tree, "the working-tree scan must not read git history"


def test_no_scan_step_is_conditioned_on_the_triggering_event() -> None:
    # Event-derived scope is the drift this contract exists to prevent: a step
    # skipped on push would restore the split the job name denies. A condition
    # that only keeps later scans running after an earlier failure is the
    # opposite -- it produces more evidence, not less.
    for step in _secrets_job()["steps"]:
        condition = step.get("if")
        if condition is None:
            continue
        assert "github.event" not in condition, f"step {step.get('name')!r} depends on the event"
        assert "github.ref" not in condition, f"step {step.get('name')!r} depends on the ref"


def test_every_scan_reports_even_after_an_earlier_failure() -> None:
    """A failed history scan must not hide the working-tree result or the
    planted-secret check; each one is separate evidence."""
    steps = {step.get("name"): step for step in _secrets_job()["steps"]}
    for name in ("Scan working tree", "Baseline cannot hide a current secret"):
        condition = steps[name].get("if", "")
        assert "cancelled()" in condition, f"{name} would be skipped after an earlier failure"


def test_scanner_is_pinned_by_digest() -> None:
    image = _secrets_job()["env"]["GITLEAKS_IMAGE"]
    assert "@sha256:" in image, "the scanner must be pinned by digest, not by tag"


def test_a_planted_current_secret_must_be_reported() -> None:
    scripts = dict(_run_steps())
    planted = scripts.get("Baseline cannot hide a current secret")
    assert planted is not None, "no planted-secret regression step"

    # The planted key is assembled from separate prefix/body literals at run
    # time; a complete token-shaped literal in the workflow would become a
    # working-tree finding itself.
    assert 'prefix="ghp_"' in planted
    assert 'body="Ab1Cd2Ef3Gh4Ij5Kl6Mn7Op8Qr9St0UvWxYz"' in planted
    assert 'key="${prefix}${body}"' in planted
    # Never spell the assembled PAT-shaped value in this test source: the
    # external history scan would correctly treat the test itself as a finding.
    assert "/dev/urandom" not in planted
    assert ".gitleaksignore" in planted, "the check must run against the real baseline"
    assert "exit 1" in planted, "an unreported plant must fail the job"


def test_baseline_suppresses_only_named_findings() -> None:
    """A fingerprint names one finding in one historical commit. A bare path, a
    glob or a rule name would blanket-suppress future secrets, which is the one
    thing a baseline must never do."""
    entries = [
        line.strip()
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert entries, "baseline is empty"
    for entry in entries:
        assert _names_one_finding(entry), f"not a single-finding fingerprint: {entry}"
        assert "*" not in entry, f"glob in baseline: {entry}"


def test_baseline_entries_are_mount_independent() -> None:
    """A working-tree fingerprint carries the source path. Scanning an absolute
    mount point would bake ``/repo`` into every entry and break the moment the
    scan runs anywhere else."""
    for name, run in _run_steps():
        if "detect" in run:
            assert "--source=." in run, f"{name} does not scan a relative source"
    entries = [
        line.strip()
        for line in BASELINE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    for entry in entries:
        assert not entry.startswith("/"), f"absolute path in baseline: {entry}"
