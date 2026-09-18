#!/usr/bin/env python3
"""Run the safe, single-entry release pipeline.

The default mode is a zero-write intake: observe the checkout and produce one
machine-readable receipt. ``--verify`` adds the repository verification suite
but still does not create branches, push, open PRs, or merge anything.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.release.plan_release import ReleasePlanError, plan_release
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from plan_release import ReleasePlanError, plan_release


def _now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _blocked(root: Path, version: str, reason: str) -> dict[str, Any]:
    return {
        "schema": "hyodo.release-pipeline/v1",
        "pipeline": "release",
        "release_id": f"hyodo-{version}",
        "observed_at": _now(),
        "root": str(root.resolve()),
        "version": version,
        "zero_write": True,
        "local_side_effects": False,
        "external_mutation": False,
        "stage": "BLOCKED",
        "result": "BLOCK",
        "residuals": [reason],
        "next_action": "resolve the measured block and rerun this command",
    }


def _run_verification(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/verify-public.sh"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def run_pipeline(
    root: Path,
    version: str,
    *,
    base_ref: str = "origin/main",
    verify: bool = False,
) -> dict[str, Any]:
    """Observe, plan, and optionally verify one candidate without external writes."""
    root = root.resolve()
    try:
        plan = plan_release(root, version, base_ref=base_ref)
    except ReleasePlanError as exc:
        return _blocked(root, version, str(exc))

    receipt: dict[str, Any] = {
        "schema": "hyodo.release-pipeline/v1",
        "pipeline": "release",
        "release_id": plan["release_id"],
        "observed_at": plan["observed_at"],
        "root": str(root),
        "version": version,
        "base_ref": base_ref,
        "base_sha": plan["base_sha"],
        "candidate_sha": plan["candidate_sha"],
        "branch": plan["branch"],
        "stages": {"observe": "PASS", "plan": plan["result"]},
        "plan": plan,
        "zero_write": not verify,
        "local_side_effects": verify,
        "external_mutation": False,
    }

    if plan["result"] != "PASS":
        receipt.update(
            {
                "stage": "BLOCKED",
                "result": "BLOCK",
                "residuals": plan["residuals"],
                "next_action": "resolve the plan block and rerun this command",
            }
        )
        return receipt

    receipt["stages"]["plan"] = "PASS"
    receipt["stage"] = "PLANNED"
    receipt["result"] = "PASS"
    receipt["residuals"] = []
    receipt["next_action"] = "rerun with --verify after explicit human authorization"

    if not verify:
        return receipt

    command = ["bash", "scripts/verify-public.sh"]
    completed = _run_verification(root)
    receipt["verification"] = {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
    }
    if completed.returncode != 0:
        receipt["stages"]["verify"] = "BLOCK"
        receipt["stage"] = "BLOCKED"
        receipt["result"] = "BLOCK"
        receipt["residuals"] = ["verify-public.sh failed"]
        receipt["next_action"] = "inspect verification output; no external mutation occurred"
        return receipt

    receipt["stages"]["verify"] = "PASS"
    receipt["stage"] = "VERIFIED"
    receipt["next_action"] = "human review is required before any future mutation adapter"
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the single-entry HyoDo release pipeline.")
    parser.add_argument("version", help="Plain semver version, for example 4.19.9")
    parser.add_argument("--root", default=".", help="Repository root to inspect")
    parser.add_argument("--base-ref", default="origin/main", help="Candidate base ref")
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run scripts/verify-public.sh after a passing plan; still no push or merge",
    )
    args = parser.parse_args(argv)
    receipt = run_pipeline(
        Path(args.root), args.version, base_ref=args.base_ref, verify=args.verify
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
