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

#: ``<commit sha>:<path>:<rule id>:<line>`` -- gitleaks' fingerprint form. Only
#: this shape names one finding; anything shorter would suppress a class.
FINGERPRINT = re.compile(r"^[0-9a-f]{40}:[^:]+:[^:]+:\d+$")


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
    scripts = {name: run for name, run in _run_steps()}

    history = scripts.get("Scan full history")
    assert history is not None, "no full-history scan step"
    assert "detect" in history
    assert "--no-git" not in history, "the history scan must read git history"

    working_tree = scripts.get("Scan working tree")
    assert working_tree is not None, "no working-tree scan step"
    assert "--no-git" in working_tree, "the working-tree scan must not read git history"


def test_no_scan_step_is_conditioned_on_the_triggering_event() -> None:
    # Event-derived scope is the drift this contract exists to prevent: a step
    # skipped on push would restore the split the job name denies.
    for step in _secrets_job()["steps"]:
        assert "if" not in step, f"step {step.get('name')!r} is conditional"


def test_scanner_is_pinned_by_digest() -> None:
    image = _secrets_job()["env"]["GITLEAKS_IMAGE"]
    assert "@sha256:" in image, "the scanner must be pinned by digest, not by tag"


def test_a_planted_current_secret_must_be_reported() -> None:
    scripts = {name: run for name, run in _run_steps()}
    planted = scripts.get("Baseline cannot hide a current secret")
    assert planted is not None, "no planted-secret regression step"

    # The planted key is built at run time; a literal here would make this file
    # itself a finding in the working-tree scan.
    assert "/dev/urandom" in planted
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
        assert FINGERPRINT.match(entry), f"not a single-finding fingerprint: {entry}"
        assert "*" not in entry, f"glob in baseline: {entry}"
