"""Contract tests for durable release evidence and publish ordering."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / ".github" / "workflows" / "release-evidence.yml"
PUBLISH = ROOT / ".github" / "workflows" / "publish.yml"


def _load(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def _runs(steps: list[dict]) -> str:
    return "\n".join(str(step.get("run", "")) for step in steps)


def test_release_evidence_is_manual_and_leaves_release_draft() -> None:
    data = _load(EVIDENCE)
    triggers = data["on"]
    runs = _runs(data["jobs"]["attach-assets"]["steps"])

    assert set(triggers) == {"workflow_dispatch"}
    assert set(triggers["workflow_dispatch"]["inputs"]) == {"tag"}
    assert "gh release edit" not in runs
    assert "expects an unpublished draft Release" in runs


def test_release_evidence_uses_least_privilege_jobs() -> None:
    data = _load(EVIDENCE)
    jobs = data["jobs"]

    assert data["permissions"] == {"contents": "read"}
    assert jobs["attach-assets"]["permissions"] == {"contents": "write"}
    assert "permissions" not in jobs["build-evidence"]


def test_release_evidence_is_non_destructive_and_checksum_verified() -> None:
    data = _load(EVIDENCE)
    jobs = data["jobs"]
    build_runs = _runs(jobs["build-evidence"]["steps"])
    attach_runs = _runs(jobs["attach-assets"]["steps"])

    assert "verify_git_tag.py" in build_runs
    assert "sha256sum -c sbom.cyclonedx.json.sha256" in build_runs
    assert "--clobber" not in attach_runs
    assert "partial release evidence exists" in attach_runs
    assert "refusing post-publish mutation" in attach_runs
    assert "gh release upload" in attach_runs
    assert "gh release download" in attach_runs
    assert "cmp -s dist/sbom.cyclonedx.json" in attach_runs
    assert "sha256sum -c sbom.cyclonedx.json.sha256" in attach_runs


def test_pypi_publish_starts_only_from_published_release_or_recovery_dispatch() -> None:
    data = _load(PUBLISH)
    triggers = data["on"]
    build_runs = _runs(data["jobs"]["build"]["steps"])

    assert set(triggers) == {"release", "workflow_dispatch"}
    assert triggers["release"]["types"] == ["published"]
    assert "push" not in triggers
    assert "published GitHub Release" in build_runs
    assert "sbom.cyclonedx.json.sha256" in build_runs
    assert "sha256sum -c sbom.cyclonedx.json.sha256" in build_runs


def test_external_actions_are_sha_pinned() -> None:
    for path in (EVIDENCE, PUBLISH):
        data = _load(path)
        uses = [
            step["uses"]
            for job in data["jobs"].values()
            for step in job["steps"]
            if "uses" in step
        ]
        assert uses
        for action in uses:
            _, ref = action.rsplit("@", 1)
            assert re.fullmatch(r"[0-9a-f]{40}", ref), action
