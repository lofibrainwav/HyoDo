#!/usr/bin/env python3
"""Run the safe, single-entry release pipeline.

The default mode is a zero-write intake: observe the checkout and produce one
machine-readable receipt. ``--verify`` adds the repository verification suite
but still does not create branches, push, open PRs, or merge anything.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
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


class PipelineExternalError(RuntimeError):
    """Raised when an external pipeline adapter cannot observe or mutate safely."""


def _git_text(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise PipelineExternalError(result.stderr.strip() or result.stdout.strip() or "git failed")
    return result.stdout.strip()


def _repo_slug(root: Path) -> str:
    remote = _git_text(root, "remote", "get-url", "origin")
    match = re.search(r"github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        raise PipelineExternalError(f"origin is not a GitHub repository: {remote}")
    return f"{match.group(1)}/{match.group(2)}"


def _gh_json(root: Path, *args: str, method: str = "GET", fields: dict[str, str] | None = None) -> Any:
    command = ["gh", "api", "--method", method]
    command.extend(args)
    for key, value in (fields or {}).items():
        command.extend(["-f", f"{key}={value}"])
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PipelineExternalError(result.stderr.strip() or result.stdout.strip() or "gh api failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PipelineExternalError("gh api returned non-JSON output") from exc


def _open_pr(root: Path, *, base: str, branch: str, slug: str) -> dict[str, Any] | None:
    owner, _ = slug.split("/", 1)
    rows = _gh_json(
        root,
        f"repos/{slug}/pulls?state=open&base={base}&head={owner}:{branch}",
    )
    return rows[0] if rows else None


def create_one_pr(root: Path, *, base: str = "main", title: str, body: str) -> dict[str, Any]:
    """Create or reuse exactly one open PR for the current candidate branch."""
    branch = _git_text(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch or branch in {"main", "master"}:
        raise PipelineExternalError("one-PR stage requires a named non-main candidate branch")
    slug = _repo_slug(root)
    existing = _open_pr(root, base=base, branch=branch, slug=slug)
    if existing:
        return {"created": False, "pr": existing}
    created = _gh_json(
        root,
        f"repos/{slug}/pulls",
        method="POST",
        fields={"title": title, "head": branch, "base": base, "body": body},
    )
    return {"created": True, "pr": created}


def _check_snapshot(root: Path, *, slug: str, sha: str) -> dict[str, Any]:
    data = _gh_json(root, f"repos/{slug}/commits/{sha}/check-runs")
    checks = data.get("check_runs", [])
    pending = [item["name"] for item in checks if item.get("status") != "completed"]
    failed = [
        item["name"]
        for item in checks
        if item.get("status") == "completed" and item.get("conclusion") not in {"success", "skipped"}
    ]
    return {
        "total": len(checks),
        "pending": pending,
        "failed": failed,
        "passed": len(checks) - len(pending) - len(failed),
        "result": "PASS" if checks and not pending and not failed else "WAIT" if pending else "BLOCK",
    }


def wait_ci(
    root: Path,
    *,
    slug: str,
    sha: str,
    timeout_seconds: int = 1800,
    poll_seconds: int = 10,
) -> dict[str, Any]:
    """Wait for exact-head CI; never treats an empty check set as green."""
    deadline = time.monotonic() + timeout_seconds
    while True:
        snapshot = _check_snapshot(root, slug=slug, sha=sha)
        if snapshot["result"] != "WAIT":
            return snapshot
        if time.monotonic() >= deadline:
            snapshot["result"] = "BLOCK"
            snapshot["timeout"] = True
            return snapshot
        time.sleep(poll_seconds)


def _approved_review(root: Path, *, slug: str, number: int, author: str) -> dict[str, Any]:
    reviews = _gh_json(root, f"repos/{slug}/pulls/{number}/reviews")
    approved = [
        review
        for review in reviews
        if review.get("state") == "APPROVED" and review.get("user", {}).get("login") != author
    ]
    return {"approved": bool(approved), "count": len(approved)}


def readback_main(root: Path, *, expected_sha: str) -> dict[str, Any]:
    remote = _git_text(root, "ls-remote", "origin", "refs/heads/main")
    observed_sha = remote.split()[0] if remote else ""
    return {
        "expected_sha": expected_sha,
        "observed_sha": observed_sha,
        "result": "PASS" if observed_sha == expected_sha else "BLOCK",
    }


def closeout_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Add a compact human/agent handoff without inventing missing evidence."""
    return {
        "goal": receipt.get("release_id"),
        "observed": receipt.get("candidate_sha"),
        "verified": receipt.get("stages", {}),
        "remains_unknown": receipt.get("residuals", []),
        "next": receipt.get("next_action"),
        "evidence": {
            "pr": receipt.get("pr", {}).get("number"),
            "merge_sha": receipt.get("merge", {}).get("sha"),
            "main_readback": receipt.get("main_readback"),
        },
        "observed_at": _now(),
    }


def run_pipeline(
    root: Path,
    version: str,
    *,
    base_ref: str = "origin/main",
    verify: bool = False,
    execute: bool = False,
    wait_for_ci: bool = False,
    merge: bool = False,
    authorize_ref: str | None = None,
    pr_title: str | None = None,
    pr_body: str = "",
) -> dict[str, Any]:
    """Run the release line, with external mutation opt-in and fail-closed gates."""
    root = root.resolve()
    if (execute or merge or wait_for_ci) and not verify:
        return _blocked(root, version, "external stages require --verify")
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
    receipt["next_action"] = "use --execute to create or reuse one PR"

    if not execute:
        return receipt

    try:
        slug = _repo_slug(root)
        pr_result = create_one_pr(
            root,
            title=pr_title or f"release: {version}",
            body=pr_body or f"HyoDo release pipeline candidate {receipt['candidate_sha']}",
        )
        pr = pr_result["pr"]
        receipt["pr"] = {
            "number": pr["number"],
            "url": pr["html_url"],
            "created": pr_result["created"],
            "head_sha": pr["head"]["sha"],
            "base_sha": pr["base"]["sha"],
        }
        receipt["external_mutation"] = pr_result["created"]
        receipt["stages"]["create_one_pr"] = "PASS"
        receipt["stage"] = "PR_OPEN"
    except PipelineExternalError as exc:
        receipt.update(
            {
                "stage": "BLOCKED",
                "result": "BLOCK",
                "residuals": [str(exc)],
                "next_action": "no further mutation; inspect the external adapter error",
            }
        )
        return receipt

    if not wait_for_ci and not merge:
        receipt["stage"] = "PR_OPEN"
        receipt["next_action"] = "rerun with --wait-ci; approval and merge remain blocked"
        return receipt

    try:
        checks = wait_ci(root, slug=slug, sha=receipt["pr"]["head_sha"])
        receipt["checks"] = checks
        receipt["stages"]["wait_ci"] = checks["result"]
        if checks["result"] != "PASS":
            receipt.update(
                {
                    "stage": "BLOCKED" if checks["result"] == "BLOCK" else "WAITING_CI",
                    "result": "BLOCK" if checks["result"] == "BLOCK" else "WAIT",
                    "residuals": checks["failed"] or checks["pending"],
                    "next_action": "wait and rerun the pipeline; no merge occurred",
                }
            )
            return receipt
        receipt["stage"] = "REMOTE_GATED"
    except PipelineExternalError as exc:
        receipt.update(
            {
                "stage": "BLOCKED",
                "result": "BLOCK",
                "residuals": [str(exc)],
                "next_action": "no merge occurred; inspect CI readback",
            }
        )
        return receipt

    if not merge:
        receipt["result"] = "PASS"
        receipt["next_action"] = "human approval and --merge --authorize-ref are required"
        return receipt

    if not authorize_ref:
        receipt.update(
            {
                "stage": "WAITING_APPROVAL",
                "result": "WAIT",
                "residuals": ["explicit authorize_ref is required"],
                "next_action": "provide --authorize-ref only after human approval",
            }
        )
        return receipt

    try:
        pr_data = _gh_json(root, f"repos/{slug}/pulls/{receipt['pr']['number']}")
        approval = _approved_review(
            root,
            slug=slug,
            number=receipt["pr"]["number"],
            author=pr_data.get("user", {}).get("login", ""),
        )
        receipt["approval"] = {"authorization_ref": authorize_ref, **approval}
        if not approval["approved"]:
            receipt.update(
                {
                    "stage": "WAITING_APPROVAL",
                    "result": "WAIT",
                    "residuals": ["no independent approved review observed"],
                    "next_action": "obtain independent review; no merge occurred",
                }
            )
            return receipt
        merged = _gh_json(
            root,
            f"repos/{slug}/pulls/{receipt['pr']['number']}/merge",
            method="PUT",
            fields={
                "merge_method": "squash",
                "commit_title": f"{pr_data['title']} (#{receipt['pr']['number']})",
            },
        )
        if not merged.get("merged"):
            raise PipelineExternalError(merged.get("message", "merge was not confirmed"))
        receipt["merge"] = {"sha": merged["sha"], "message": merged.get("message")}
        receipt["stages"]["merge_once"] = "PASS"
        receipt["stage"] = "MERGED"
        readback = readback_main(root, expected_sha=merged["sha"])
        receipt["main_readback"] = readback
        receipt["stages"]["readback_main"] = readback["result"]
        receipt["stage"] = "READBACK_VERIFIED" if readback["result"] == "PASS" else "BLOCKED"
        receipt["result"] = readback["result"]
        receipt["residuals"] = [] if readback["result"] == "PASS" else ["main SHA mismatch"]
        receipt["closeout"] = closeout_receipt(receipt)
        receipt["next_action"] = "closed" if receipt["result"] == "PASS" else "reconcile main readback"
    except PipelineExternalError as exc:
        receipt.update(
            {
                "stage": "BLOCKED",
                "result": "BLOCK",
                "residuals": [str(exc)],
                "next_action": "reconcile remote state before retrying; merge outcome is unknown",
            }
        )
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
    parser.add_argument("--execute", action="store_true", help="Create or reuse one GitHub PR")
    parser.add_argument("--wait-ci", action="store_true", help="Wait for exact-head CI")
    parser.add_argument("--merge", action="store_true", help="Merge only after approval and authorization")
    parser.add_argument("--authorize-ref", help="Human authorization reference required for merge")
    parser.add_argument("--pr-title", help="PR title when creating a candidate PR")
    parser.add_argument("--pr-body", default="", help="PR body when creating a candidate PR")
    args = parser.parse_args(argv)
    receipt = run_pipeline(
        Path(args.root),
        args.version,
        base_ref=args.base_ref,
        verify=args.verify,
        execute=args.execute,
        wait_for_ci=args.wait_ci,
        merge=args.merge,
        authorize_ref=args.authorize_ref, pr_title=args.pr_title, pr_body=args.pr_body
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
