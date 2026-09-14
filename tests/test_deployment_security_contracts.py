"""Regression contracts for public security surfaces."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_security_workflow_keeps_all_external_actions_sha_pinned() -> None:
    workflow = (REPO_ROOT / ".github" / "workflows" / "security.yml").read_text(encoding="utf-8")

    uses = [line.strip() for line in workflow.splitlines() if line.strip().startswith("uses:")]
    assert uses
    assert all("@" in line and len(line.rsplit("@", 1)[1].split()[0]) == 40 for line in uses)
    assert "dependency-review-action" in workflow
