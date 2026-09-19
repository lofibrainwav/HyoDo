#!/usr/bin/env python3
"""Run the safe, single-entry release pipeline.

The default mode is a zero-write intake: observe the checkout and produce one
machine-readable receipt. ``--verify`` adds the repository verification suite
but still does not create branches, push, open PRs, or merge anything.
"""

from __future__ import annotations

import argparse
import json
import os
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


UNOBSERVED = "UNOBSERVED"


def _runtime_identity() -> dict[str, str]:
    """Read agent labels from the runtime; never invent a model or authority."""
    return {
        "agent": os.environ.get("HYODO_AGENT", UNOBSERVED),
        "model": os.environ.get("HYODO_MODEL", UNOBSERVED),
        "mode": os.environ.get("HYODO_MODE", UNOBSERVED),
        "github_actor": os.environ.get("GITHUB_ACTOR", UNOBSERVED),
        "authority": "human approval required",
    }


def _five_w_one_h(root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    try:
        repo = _repo_slug(root)
    except PipelineExternalError:
        repo = UNOBSERVED
    runtime_identity = _runtime_identity()
    verifier = receipt.get("verifier", {})
    approval = receipt.get("approval", {})
    return {
        "who": {
            **runtime_identity,
            "builder_agent": {
                "agent": runtime_identity["agent"],
                "model": runtime_identity["model"],
                "mode": runtime_identity["mode"],
            },
            "verifier_agent": verifier.get("reviewer", UNOBSERVED),
            "human_authority": approval.get("authorization_ref", UNOBSERVED),
        },
        "when": {
            "observed_at": receipt.get("observed_at", UNOBSERVED),
            "approved_at": receipt.get("approval", {}).get("observed_at", UNOBSERVED),
            "merged_at": receipt.get("merge", {}).get("observed_at", UNOBSERVED),
            "readback_at": receipt.get("main_readback", {}).get("observed_at", UNOBSERVED),
        },
        "where": {
            "repo": repo,
            "branch": receipt.get("branch", UNOBSERVED),
            "worktree": receipt.get("root", UNOBSERVED),
            "target": receipt.get("base_ref", UNOBSERVED),
        },
        "what": {
            "pr": receipt.get("pr", {}).get("number", UNOBSERVED),
            "candidate_sha": receipt.get("candidate_sha", UNOBSERVED),
            "authorized_sha": approval.get("authorized_sha", UNOBSERVED),
            "ci_verified_sha": receipt.get("checks", {}).get("sha", UNOBSERVED),
            "merge_sha": receipt.get("merge", {}).get("sha", UNOBSERVED),
            "result": receipt.get("result", UNOBSERVED),
        },
        "how": {
            "pipeline": receipt.get("schema", UNOBSERVED),
            "stages": list(receipt.get("stages", {}).keys()),
            "mutations": receipt.get("mutations", []),
        },
        "why": {
            "intent": f"close one exact verified candidate: {receipt.get('release_id', UNOBSERVED)}",
            "authority_ref": receipt.get("approval", {}).get("authorization_ref", UNOBSERVED),
            "evidence_refs": receipt.get("evidence_refs", []),
        },
    }


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


def _branch(root: Path) -> str:
    return _git_text(root, "symbolic-ref", "--quiet", "--short", "HEAD")


def _remote_branch_sha(root: Path, branch: str) -> str:
    remote = _git_text(root, "ls-remote", "origin", f"refs/heads/{branch}")
    return remote.split()[0] if remote else ""


def push_candidate(root: Path, *, candidate_sha: str) -> dict[str, str]:
    """Push the named candidate once, then bind the remote branch to its SHA."""
    branch = _branch(root)
    if not branch or branch in {"main", "master"}:
        raise PipelineExternalError("candidate push requires a named non-main branch")
    result = subprocess.run(
        ["git", "-C", str(root), "push", "origin", f"HEAD:{branch}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise PipelineExternalError(
            result.stderr.strip() or result.stdout.strip() or "git push failed"
        )
    remote_sha = _remote_branch_sha(root, branch)
    if remote_sha != candidate_sha:
        raise PipelineExternalError(
            f"RECONCILIATION_REQUIRED: candidate {candidate_sha} != remote {remote_sha}"
        )
    return {"branch": branch, "candidate_sha": candidate_sha, "remote_sha": remote_sha}


def _gh_json(
    root: Path, *args: str, method: str = "GET", fields: dict[str, str] | None = None
) -> Any:
    command = ["gh", "api", "--method", method]
    command.extend(args)
    for key, value in (fields or {}).items():
        command.extend(["-f", f"{key}={value}"])
    result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise PipelineExternalError(
            result.stderr.strip() or result.stdout.strip() or "gh api failed"
        )
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
    branch = _branch(root)
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
        if item.get("status") == "completed"
        and item.get("conclusion") not in {"success", "skipped"}
    ]
    skipped = [
        item["name"]
        for item in checks
        if item.get("status") == "completed" and item.get("conclusion") == "skipped"
    ]
    passed = sum(
        item.get("status") == "completed" and item.get("conclusion") == "success" for item in checks
    )
    return {
        "sha": sha,
        "total": len(checks),
        "pending": pending,
        "failed": failed,
        "skipped": skipped,
        "passed": passed,
        "result": "PASS"
        if passed and not pending and not failed
        else "WAIT"
        if pending
        else "BLOCK",
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
    latest = approved[-1] if approved else None
    return {
        "approved": bool(approved),
        "count": len(approved),
        "review_id": latest.get("id") if latest else None,
        "reviewer": latest.get("user", {}).get("login") if latest else None,
        "review_commit_sha": latest.get("commit_id") if latest else None,
    }


def _provided_reference(value: object) -> bool:
    """Reject absence markers; the calling host still authenticates the grant."""
    return (
        isinstance(value, str)
        and bool(value.strip())
        and value.strip().upper() not in {UNOBSERVED, "UNKNOWN"}
    )


def _human_authority_gate(
    *,
    authorize_ref: str | None,
    authorize_sha: str | None,
    current_pr_head: str,
    remote_candidate_sha: str,
    ci_verified_sha: str,
    verifier: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate human authority separately from optional verifier evidence."""
    verifier_status = "VERIFIED" if verifier.get("approved") else "UNVERIFIED"
    verifier_residual = None if verifier.get("approved") else "verifier_missing"
    result: dict[str, Any] = {
        "human_authority": {
            "authorization_ref": authorize_ref or UNOBSERVED,
            "authorized_sha": authorize_sha or UNOBSERVED,
        },
        "verifier": {
            "status": verifier_status,
            "reviewer": verifier.get("reviewer") or UNOBSERVED,
            "review_id": verifier.get("review_id") or UNOBSERVED,
            "review_commit_sha": verifier.get("review_commit_sha") or UNOBSERVED,
            "residual": verifier_residual,
        },
    }
    if not _provided_reference(authorize_ref) or not _provided_reference(authorize_sha):
        result.update(
            {
                "stage": "WAITING_APPROVAL",
                "result": "WAIT",
                "residuals": ["human exact-head authorization is required"],
            }
        )
        return result

    observed = {
        "authorized_sha": authorize_sha,
        "current_pr_head": current_pr_head,
        "remote_candidate_sha": remote_candidate_sha,
        "ci_verified_sha": ci_verified_sha,
    }
    if (
        not all(_provided_reference(value) for value in observed.values())
        or len(set(observed.values())) != 1
    ):
        result.update(
            {
                "stage": "RECONCILIATION_REQUIRED",
                "result": "BLOCK",
                "residuals": [
                    "human authorization or verified artifact is bound to a different head"
                ],
                "head_binding": observed,
            }
        )
        return result

    result.update({"stage": "AUTHORIZED", "result": "PASS", "head_binding": observed})
    return result


def readback_main(root: Path, *, expected_sha: str) -> dict[str, Any]:
    remote = _git_text(root, "ls-remote", "origin", "refs/heads/main")
    observed_sha = remote.split()[0] if remote else ""
    return {
        "expected_sha": expected_sha,
        "observed_sha": observed_sha,
        "observed_at": _now(),
        "result": "PASS" if observed_sha == expected_sha else "BLOCK",
    }


def closeout_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Add a compact human/agent handoff without inventing missing evidence."""
    return {
        "schema": "hyodo.closeout/v1",
        "five_w_one_h": _five_w_one_h(Path(receipt["root"]), receipt),
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
        "mutations": receipt.get("mutations", []),
        "observed_at": _now(),
    }


def run_pipeline(
    root: Path,
    version: str,
    *,
    base_ref: str = "origin/main",
    verify: bool = False,
    execute: bool = False,
    push_candidate_stage: bool = False,
    wait_for_ci: bool = False,
    merge: bool = False,
    authorize_ref: str | None = None,
    authorize_sha: str | None = None,
    pr_title: str | None = None,
    pr_body: str = "",
) -> dict[str, Any]:
    """Run the release line, with external mutation opt-in and fail-closed gates."""
    root = root.resolve()
    if (execute or merge or wait_for_ci or push_candidate_stage) and not verify:
        return _blocked(root, version, "external stages require --verify")
    if push_candidate_stage and not execute:
        return _blocked(root, version, "push stage requires --execute")
    if merge and not (execute and wait_for_ci):
        return _blocked(root, version, "merge stage requires --execute --wait-ci")
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
        "mutations": [],
    }
    receipt["five_w_one_h"] = _five_w_one_h(root, receipt)

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
        if push_candidate_stage:
            receipt["push"] = push_candidate(root, candidate_sha=receipt["candidate_sha"])
            receipt["stages"]["push_candidate"] = "PASS"
            receipt["external_mutation"] = True
            receipt["mutations"].append({"kind": "PUSH_CANDIDATE", "sha": receipt["candidate_sha"]})
        else:
            remote_sha = _remote_branch_sha(root, _branch(root))
            receipt["push"] = {
                "branch": _branch(root),
                "candidate_sha": receipt["candidate_sha"],
                "remote_sha": remote_sha,
                "result": "PASS" if remote_sha == receipt["candidate_sha"] else "BLOCK",
            }
            if remote_sha != receipt["candidate_sha"]:
                raise PipelineExternalError(
                    "RECONCILIATION_REQUIRED: remote branch is not the planned candidate"
                )
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
        receipt["mutations"].append(
            {
                "kind": "CREATE_PR" if pr_result["created"] else "REUSE_PR",
                "number": pr["number"],
                "head_sha": pr["head"]["sha"],
            }
        )
        if receipt["pr"]["head_sha"] != receipt["candidate_sha"]:
            raise PipelineExternalError(
                "RECONCILIATION_REQUIRED: PR head is not the planned candidate"
            )
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
        receipt["next_action"] = "rerun with --wait-ci; human exact-head authority is required"
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
                    "residuals": checks["failed"]
                    or checks["pending"]
                    or checks.get("skipped")
                    or ["no successful CI checks observed"],
                    "next_action": "wait and rerun the pipeline; no merge occurred",
                }
            )
            return receipt
        receipt["stage"] = "REMOTE_GATED"
        current_pr = _gh_json(root, f"repos/{slug}/pulls/{receipt['pr']['number']}")
        current_head = current_pr.get("head", {}).get("sha")
        remote_head = _remote_branch_sha(root, _branch(root))
        if current_head != receipt["pr"]["head_sha"] or remote_head != receipt["pr"]["head_sha"]:
            receipt.update(
                {
                    "stage": "RECONCILIATION_REQUIRED",
                    "result": "BLOCK",
                    "residuals": ["PR or remote branch moved after CI"],
                    "next_action": "replan and rerun CI for the new exact head",
                }
            )
            return receipt
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
        receipt["next_action"] = (
            "human exact-head approval and --merge --authorize-ref --authorize-sha are required"
        )
        return receipt

    try:
        pr_data = _gh_json(root, f"repos/{slug}/pulls/{receipt['pr']['number']}")
        current_head = pr_data.get("head", {}).get("sha")
        remote_head = _remote_branch_sha(root, _branch(root))
        ci_verified_sha = receipt.get("checks", {}).get("sha", UNOBSERVED)
        approval = _approved_review(
            root,
            slug=slug,
            number=receipt["pr"]["number"],
            author=pr_data.get("user", {}).get("login", ""),
        )
        if approval["approved"] and approval["review_commit_sha"] != current_head:
            approval["approved"] = False
            approval["review_stale"] = True
        gate = _human_authority_gate(
            authorize_ref=authorize_ref,
            authorize_sha=authorize_sha,
            current_pr_head=current_head,
            remote_candidate_sha=remote_head,
            ci_verified_sha=ci_verified_sha,
            verifier=approval,
        )
        receipt["approval"] = {"observed_at": _now(), **gate["human_authority"]}
        receipt["verifier"] = gate["verifier"]
        if gate["result"] != "PASS":
            receipt.update(
                {
                    "stage": gate["stage"],
                    "result": gate["result"],
                    "residuals": gate["residuals"],
                    "head_binding": gate.get("head_binding"),
                    "next_action": (
                        "provide human exact-head authorization; no merge occurred"
                        if gate["stage"] == "WAITING_APPROVAL"
                        else "reconcile remote state and re-authorize the exact head"
                    ),
                }
            )
            return receipt
        merged = _gh_json(
            root,
            f"repos/{slug}/pulls/{receipt['pr']['number']}/merge",
            method="PUT",
            fields={
                "merge_method": "squash",
                "sha": receipt["pr"]["head_sha"],
                "commit_title": f"{pr_data['title']} (#{receipt['pr']['number']})",
            },
        )
        if not merged.get("merged"):
            raise PipelineExternalError(merged.get("message", "merge was not confirmed"))
        receipt["merge"] = {
            "sha": merged["sha"],
            "message": merged.get("message"),
            "observed_at": _now(),
        }
        receipt["external_mutation"] = True
        receipt["mutations"].append({"kind": "MERGE", "sha": merged["sha"]})
        receipt["stages"]["merge_once"] = "PASS"
        receipt["stage"] = "MERGED"
        readback = readback_main(root, expected_sha=merged["sha"])
        receipt["main_readback"] = readback
        receipt["stages"]["readback_main"] = readback["result"]
        receipt["stage"] = "READBACK_VERIFIED" if readback["result"] == "PASS" else "BLOCKED"
        receipt["result"] = readback["result"]
        receipt["residuals"] = [] if readback["result"] == "PASS" else ["main SHA mismatch"]
        receipt["closeout"] = closeout_receipt(receipt)
        receipt["next_action"] = (
            "closed" if receipt["result"] == "PASS" else "reconcile main readback"
        )
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
    parser.add_argument(
        "--push-candidate",
        action="store_true",
        help="Push and bind the candidate before creating a PR",
    )
    parser.add_argument("--wait-ci", action="store_true", help="Wait for exact-head CI")
    parser.add_argument(
        "--merge", action="store_true", help="Merge only after approval and authorization"
    )
    parser.add_argument("--authorize-ref", help="Human authorization reference required for merge")
    parser.add_argument(
        "--authorize-sha", help="Exact candidate SHA covered by the human authorization"
    )
    parser.add_argument("--pr-title", help="PR title when creating a candidate PR")
    parser.add_argument("--pr-body", default="", help="PR body when creating a candidate PR")
    args = parser.parse_args(argv)
    receipt = run_pipeline(
        Path(args.root),
        args.version,
        base_ref=args.base_ref,
        verify=args.verify,
        execute=args.execute,
        push_candidate_stage=args.push_candidate,
        wait_for_ci=args.wait_ci,
        merge=args.merge,
        authorize_ref=args.authorize_ref,
        authorize_sha=args.authorize_sha,
        pr_title=args.pr_title,
        pr_body=args.pr_body,
    )
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
