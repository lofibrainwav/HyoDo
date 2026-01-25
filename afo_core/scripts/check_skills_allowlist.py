from __future__ import annotations

import os
import sys
from pathlib import Path

import yaml

"""Skills Allowlist CI Gate Validator.

Hard-fail checker for skills_allowlist.yaml structure validation.
Exit codes:
  0 = valid
  1 = structure error
  2 = missing dependency
"""


def fail(msg: str, code: int = 1) -> None:
    """Print error and exit with code."""
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    """Validate skills_allowlist.yaml structure."""
    path = Path(
        os.environ.get(
            "AFO_SKILLS_ALLOWLIST_PATH",
            "config/skills_allowlist.yaml",
        )
    )

    try:
        pass  # Placeholder
    except ImportError:
        fail("missing dependency: pyyaml (import yaml failed)", 2)

    if not path.exists():
        fail(f"allowlist not found: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    # Check required keys
    for k in ("approved_skills", "blocked_skills", "fallback_rules"):
        if k not in data:
            fail(f"missing key: {k}")

    approved = data["approved_skills"] or []
    blocked = data["blocked_skills"] or []
    fallback = data["fallback_rules"] or []

    # Type validation
    if not isinstance(approved, list) or not all(isinstance(x, str) for x in approved):
        fail("approved_skills must be a list[str]")
    if not isinstance(blocked, list) or not all(isinstance(x, str) for x in blocked):
        fail("blocked_skills must be a list[str]")
    if not isinstance(fallback, list) or not all(isinstance(x, dict) for x in fallback):
        fail("fallback_rules must be a list[dict]")

    # Duplicate check
    approved_set = set(approved)
    blocked_set = set(blocked)

    if len(approved_set) != len(approved):
        fail("approved_skills has duplicates")
    if len(blocked_set) != len(blocked):
        fail("blocked_skills has duplicates")

    # Overlap check
    overlap = sorted(approved_set & blocked_set)
    if overlap:
        fail(f"approved_skills overlaps blocked_skills: {overlap}")

    print("OK: skills_allowlist.yaml structure is valid")


if __name__ == "__main__":
    main()
