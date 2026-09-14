#!/usr/bin/env python3
"""Fail closed when the derived orchestration map can drift into fake SSOT."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "docs" / "VERIFICATION_ORCHESTRATION.md"
CONTAINER_WORKFLOW = ROOT / ".github" / "workflows" / "container-proof.yml"


def main() -> int:
    orchestration = MAP.read_text(encoding="utf-8")
    workflow = CONTAINER_WORKFLOW.read_text(encoding="utf-8")
    failures: list[str] = []

    if "DERIVED OPERATIONS MAP — NOT PRODUCT SSOT" not in orchestration:
        failures.append("orchestration map must identify itself as derived, not SSOT")
    if "| Current state |" in orchestration:
        failures.append("live state must not be committed in the procedure map")
    if "…" in orchestration:
        failures.append("abbreviated identifiers are forbidden in the map")
    if re.search(r"(?<![0-9a-f])[0-9a-f]{7,39}(?![0-9a-f])", orchestration):
        failures.append("short hexadecimal identifiers are forbidden in the map")
    if "github.event.pull_request.head.sha" not in workflow:
        failures.append("container proof must bind receipts to the PR head SHA")
    if 'echo "candidate_sha=${CANDIDATE_SHA}"' not in workflow:
        failures.append("container proof must emit candidate_sha in its receipt")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("PASS: orchestration map and candidate-head receipt contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
