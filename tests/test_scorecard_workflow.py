"""Guard: the OpenSSF Scorecard workflow parses, publishes its results, and
pins every action by commit SHA.

Same posture as the rest of this repository's workflows (see
`tests/test_publish_workflow_shell_safety.py`): a floating tag can be
repointed by whoever controls the upstream action, so every `uses:` here must
be a 40-character commit SHA, never a tag or branch name.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "scorecard.yml"

# `owner/repo/action@<40-hex-sha>` — a tag like `@v2.4.4` would not match.
SHA_PIN_RE = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _load() -> dict:
    return yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))


def _uses_values(data: dict) -> list[str]:
    values: list[str] = []
    for job in data["jobs"].values():
        for step in job.get("steps", []):
            if "uses" in step:
                values.append(step["uses"])
    return values


def test_scorecard_workflow_is_valid_yaml() -> None:
    data = _load()
    assert data["jobs"]


def test_publish_results_is_enabled() -> None:
    data = _load()
    scorecard_steps = [
        step
        for job in data["jobs"].values()
        for step in job.get("steps", [])
        if step.get("uses", "").startswith("ossf/scorecard-action@")
    ]
    assert scorecard_steps, "no ossf/scorecard-action step found in scorecard.yml"
    for step in scorecard_steps:
        assert step.get("with", {}).get("publish_results") is True


def test_every_uses_is_sha_pinned() -> None:
    data = _load()
    offenders = [u for u in _uses_values(data) if not SHA_PIN_RE.match(u)]
    assert offenders == [], f"uses: not SHA-pinned in scorecard.yml: {offenders}"
