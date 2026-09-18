#!/usr/bin/env python3
"""Plan a release without changing files, refs, or remote state.

The plan is intentionally narrower than ``prepare_release``: it validates the
candidate checkout and reports the exact release write-set, but never applies
the version, roadmap, changelog, or release-note mutations.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

try:
    from scripts.release.check_roadmap_sync import (
        RoadmapSyncError,
        baseline_version,
        has_release_entry,
        target_version,
    )
    from scripts.release.prepare_release import CHANGELOG_HEADER_END, VERSION_RE
    from scripts.release.release_state import start_receipt
    from scripts.release.version_sources import VersionSourceUpdateError, synchronized_version
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from check_roadmap_sync import (
        RoadmapSyncError,
        baseline_version,
        has_release_entry,
        target_version,
    )
    from prepare_release import CHANGELOG_HEADER_END, VERSION_RE
    from release_state import start_receipt
    from version_sources import VersionSourceUpdateError, synchronized_version


EXPECTED_WRITE_SET = (
    "ROADMAP.md",
    "VERSION",
    "pyproject.toml",
    "hyodo/__init__.py",
    ".claude-plugin/plugin.json",
    "server.json",
    ".claude-plugin/marketplace.json",
    "CHANGELOG.md",
    "docs/releases/<version>.md",
)


class ReleasePlanError(RuntimeError):
    """Raised when a release plan cannot be measured safely."""


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise ReleasePlanError(detail)
    return result.stdout.strip()


def _check(name: str, state: str, detail: str) -> dict[str, str]:
    return {"name": name, "state": state, "detail": detail}


def plan_release(
    root: Path,
    version: str,
    *,
    base_ref: str = "origin/main",
    push_target: str = "origin",
    pr_target: str = "main",
) -> dict[str, object]:
    root = root.resolve()
    checks: list[dict[str, str]] = []

    if not VERSION_RE.fullmatch(version):
        raise ReleasePlanError("version must be plain semver like 4.12.1, without a v prefix")
    if not (root / ".git").exists():
        raise ReleasePlanError(f"not a Git checkout: {root}")

    branch_result = subprocess.run(
        ["git", "-C", str(root), "symbolic-ref", "--quiet", "--short", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    branch = branch_result.stdout.strip()
    if branch_result.returncode != 0 or not branch:
        checks.append(_check("named_release_branch", "BLOCK", "detached HEAD"))
    elif branch.startswith("release/"):
        checks.append(_check("named_release_branch", "PASS", branch))
    else:
        checks.append(_check("named_release_branch", "BLOCK", f"expected release/*, got {branch}"))

    status = _git(root, "status", "--porcelain")
    checks.append(
        _check(
            "clean_worktree", "PASS" if not status else "BLOCK", "clean" if not status else "dirty"
        )
    )

    candidate_sha = _git(root, "rev-parse", "HEAD")
    base_sha = _git(root, "rev-parse", f"{base_ref}^{{commit}}")
    checks.append(
        _check(
            "candidate_based_on_base",
            "PASS" if _is_ancestor(root, base_sha, candidate_sha) else "BLOCK",
            f"{base_ref}={base_sha[:12]}",
        )
    )

    try:
        current_version = synchronized_version(root)
        checks.append(_check("version_sources", "PASS", current_version))
    except VersionSourceUpdateError as exc:
        current_version = None
        checks.append(_check("version_sources", "BLOCK", str(exc)))

    roadmap_path = root / "ROADMAP.md"
    roadmap_text = roadmap_path.read_text(encoding="utf-8") if roadmap_path.exists() else ""
    try:
        published = baseline_version(roadmap_text)
        target = target_version(roadmap_text)
        roadmap_ok = current_version is not None and target == current_version
        checks.append(
            _check(
                "roadmap_target",
                "PASS" if roadmap_ok else "BLOCK",
                f"baseline={published}; target={target}",
            )
        )
        checks.append(
            _check(
                "roadmap_entry",
                "PASS" if has_release_entry(roadmap_text, current_version or "") else "BLOCK",
                current_version or "unknown",
            )
        )
    except RoadmapSyncError as exc:
        checks.append(_check("roadmap", "BLOCK", str(exc)))

    release_note = root / "docs" / "releases" / f"{version}.md"
    checks.append(
        _check(
            "release_note_available",
            "PASS" if not release_note.exists() else "BLOCK",
            str(release_note.relative_to(root)),
        )
    )
    changelog = root / "CHANGELOG.md"
    changelog_text = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
    checks.append(
        _check(
            "changelog_ready",
            "PASS"
            if f"## [{version}]" not in changelog_text and CHANGELOG_HEADER_END in changelog_text
            else "BLOCK",
            "new section can be inserted"
            if f"## [{version}]" not in changelog_text
            else "version section already exists",
        )
    )

    result = "PASS" if all(item["state"] == "PASS" for item in checks) else "BLOCK"
    plan = {
        "schema": "hyodo.release-plan/v1",
        "release_id": f"hyodo-{version}",
        "observed_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "zero_write": True,
        "root": str(root),
        "base_ref": base_ref,
        "base_sha": base_sha,
        "candidate_sha": candidate_sha,
        "branch": branch or None,
        "worktree": str(root),
        "expected_write_set": [path.replace("<version>", version) for path in EXPECTED_WRITE_SET],
        "expected_version_delta": {"from": current_version, "to": version},
        "validations": checks,
        "push_target": push_target,
        "pr_target": pr_target,
        "result": result,
    }
    if result == "PASS":
        plan.update(
            {
                key: value
                for key, value in start_receipt(plan).items()
                if key in {"state", "history", "residuals", "final_state"}
            }
        )
    else:
        plan.update(
            {
                "state": "OBSERVED",
                "history": [],
                "residuals": [item for item in checks if item["state"] != "PASS"],
                "final_state": "BLOCKED",
            }
        )
    return plan


def _is_ancestor(root: Path, base_sha: str, candidate_sha: str) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", base_sha, candidate_sha],
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a HyoDo release without writing state.")
    parser.add_argument("version", help="Plain semver version, for example 4.12.0")
    parser.add_argument("--root", default=".", help="Repository root to inspect")
    parser.add_argument("--base-ref", default="origin/main", help="Candidate base ref")
    parser.add_argument("--push-target", default="origin", help="Planned push remote")
    parser.add_argument("--pr-target", default="main", help="Planned pull request target")
    args = parser.parse_args(argv)
    try:
        receipt = plan_release(
            Path(args.root),
            args.version,
            base_ref=args.base_ref,
            push_target=args.push_target,
            pr_target=args.pr_target,
        )
    except ReleasePlanError as exc:
        print(f"BLOCK: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
