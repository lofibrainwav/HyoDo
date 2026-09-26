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
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

try:
    from scripts.release.plan_release import ReleasePlanError, plan_release
    from scripts.release.release_state import (
        ReleaseOrderError,
        require_state,
        start_publication_receipt,
        transition,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution path
    from plan_release import ReleasePlanError, plan_release
    from release_state import (
        ReleaseOrderError,
        require_state,
        start_publication_receipt,
        transition,
    )


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


# Named CI policy. These checks run only on a push to main (ci.yml gates them
# with `github.event_name == 'push' && github.ref == 'refs/heads/main'`). On a
# pull-request candidate they are skipped by design: expected N/A, not missing
# evidence. Every other skipped check still blocks. On main they must succeed.
MAIN_ONLY_CHECKS = frozenset({"Goodness - Serial Full Suite (main)"})
_FAILED_CONCLUSION_EXEMPT = frozenset({"success", "skipped"})


def _check_snapshot(
    root: Path, *, slug: str, sha: str, event: str = "pull_request"
) -> dict[str, Any]:
    """Classify exact-SHA check runs under the named CI policy.

    ``event="pull_request"``: a skipped ``MAIN_ONLY_CHECKS`` run is recorded as
    ``expected_na``; any other skipped run blocks; only success passes.
    ``event="push"`` (main): every ``MAIN_ONLY_CHECKS`` run must be present and
    successful, and nothing may be pending or failed. An empty check set never
    passes.
    """
    if event not in {"pull_request", "push"}:
        raise ValueError(f"unknown CI event: {event!r}")
    data = _gh_json(root, f"repos/{slug}/commits/{sha}/check-runs?per_page=100")
    checks = data.get("check_runs", [])
    completed = [item for item in checks if item.get("status") == "completed"]
    pending = [item["name"] for item in checks if item.get("status") != "completed"]
    failed = [
        item["name"]
        for item in completed
        if item.get("conclusion") not in _FAILED_CONCLUSION_EXEMPT
    ]
    all_skipped = [item["name"] for item in completed if item.get("conclusion") == "skipped"]
    passed = sum(item.get("conclusion") == "success" for item in completed)
    expected_na: list[str] = []
    missing_required: list[str] = []
    if event == "pull_request":
        expected_na = [name for name in all_skipped if name in MAIN_ONLY_CHECKS]
        skipped = [name for name in all_skipped if name not in MAIN_ONLY_CHECKS]
        blocking_skips = skipped
    else:
        skipped = all_skipped
        successes = {item["name"] for item in completed if item.get("conclusion") == "success"}
        missing_required = sorted(MAIN_ONLY_CHECKS - successes)
        # Other skips on a push are reported, not failed: PR-only jobs such as
        # dependency review are skipped on main by design.
        blocking_skips = [name for name in skipped if name in MAIN_ONLY_CHECKS]
    if pending:
        result = "WAIT"
    elif passed and not failed and not blocking_skips and not missing_required:
        result = "PASS"
    else:
        result = "BLOCK"
    return {
        "sha": sha,
        "event": event,
        "total": len(checks),
        "pending": pending,
        "failed": failed,
        "skipped": skipped,
        "expected_na": expected_na,
        "missing_required": missing_required,
        "passed": passed,
        "result": result,
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


def post_merge_stage(readback: dict[str, Any]) -> str:
    """Name the stage reached after merge.

    Only main has been read back here. READBACK_VERIFIED is reserved for the
    publication chain read back end to end, so a merge must not claim it.
    """
    return "MERGED" if readback.get("result") == "PASS" else "BLOCKED"


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
        receipt["stage"] = post_merge_stage(readback)
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


# ---------------------------------------------------------------------------
# Publication: MERGED -> ... -> READBACK_VERIFIED
#
# v4.21.2 was tagged and its Release published by hand before the SBOM was
# attached; immutable releases made that permanent. The workflows guarded PyPI,
# but nothing owned the irreversible step. This stage owns it: every external
# mutation goes through ``_mutate`` (planned, not called, in a dry run), and
# ``publish_release`` runs only from DRAFT_VERIFIED, under human authority bound
# to the merged SHA, after re-observing the draft and its evidence.
# ---------------------------------------------------------------------------

SBOM_ASSETS = ("sbom.cyclonedx.json", "sbom.cyclonedx.json.sha256")

# release-evidence.yml names each run after its tag input (``run-name``), so the
# pipeline can bind the run it waits on to the tag it dispatched.
EVIDENCE_RUN_TITLE = "HyoDo Release Evidence {tag}"

# Workflow jobs whose success is the evidence for a publication state. Keyed by
# job id; tests fail if a workflow renames or reorders one of these jobs.
WORKFLOW_STATES: dict[str, dict[str, str]] = {
    "release-evidence.yml": {
        "build-evidence": "EVIDENCE_BUILT",
        "attach-assets": "EVIDENCE_ATTACHED",
    },
    "publish.yml": {
        "publish": "PYPI_PUBLISHED",
        "verify": "PROVENANCE_VERIFIED",
    },
}

# `gh run view` reports jobs by display name; WORKFLOW_STATES is keyed by job
# id. This map is written out rather than parsed from the workflow files so the
# pipeline needs no PyYAML: it runs after the irreversible publish, often from a
# system interpreter. Tests fail if a workflow's job names drift from it.
WORKFLOW_JOB_IDS: dict[str, dict[str, str]] = {
    "release-evidence.yml": {
        "Build exact-tag SBOM evidence": "build-evidence",
        "Attach and verify draft Release SBOM assets": "attach-assets",
    },
    "publish.yml": {
        "Build release artifacts": "build",
        "Publish to PyPI (OIDC)": "publish",
        "Post-publish readback": "verify",
    },
}


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _action_boundary() -> datetime:
    """Wait for the next whole UTC second and return it.

    GitHub reports run ``createdAt`` truncated to whole seconds. Acting only
    after a whole-second boundary makes "created at or after the boundary" an
    exact test: an earlier run in the same second can never look fresh.
    """
    now = _utcnow()
    boundary = now.replace(microsecond=0) + timedelta(seconds=1)
    time.sleep((boundary - now).total_seconds())
    return boundary


def _created_since(created_at: str, boundary: datetime) -> bool:
    if boundary.microsecond:
        raise ValueError("run freshness needs a whole-second boundary from _action_boundary()")
    return _parse_utc(created_at) >= boundary


class _PublicationBlocked(Exception):
    def __init__(self, reason: str, stage: str = "BLOCKED", result: str = "BLOCK") -> None:
        super().__init__(reason)
        self.reason = reason
        self.stage = stage
        self.result = result


def _has_evidence(release: dict[str, Any] | None) -> bool:
    return release is not None and set(SBOM_ASSETS) <= set(release.get("assets") or [])


def _has_exact_evidence(release: dict[str, Any] | None) -> bool:
    return release is not None and set(release.get("assets") or []) == set(SBOM_ASSETS)


class GitHubRemote:
    """Real GitHub/PyPI adapter for ``run_publication``.

    Reads reuse the existing release scripts. Each mutation is one gh/git call
    and is only reached through ``run_publication``'s gates.
    """

    def __init__(self, root: Path, *, poll_seconds: int = 15, timeout_seconds: int = 3600) -> None:
        self.root = root.resolve()
        self.repo = _repo_slug(self.root)
        self.poll_seconds = poll_seconds
        self.timeout_seconds = timeout_seconds

    def _cmd(self, *args: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            list(args), cwd=self.root, capture_output=True, text=True, check=False, timeout=timeout
        )

    def _ok(self, *args: str, timeout: int = 120) -> str:
        done = self._cmd(*args, timeout=timeout)
        if done.returncode != 0:
            raise PipelineExternalError(
                done.stderr.strip() or done.stdout.strip() or f"{args[0]} failed"
            )
        return done.stdout.strip()

    # -- observations -------------------------------------------------------
    def observe_main(self) -> dict[str, str]:
        self._ok("git", "fetch", "--quiet", "origin", "main")
        sha = self._ok("git", "rev-parse", "origin/main")
        version = self._ok("git", "show", f"{sha}:VERSION").strip()
        return {"sha": sha, "version": version}

    def observe_main_ci(self, sha: str) -> dict[str, Any]:
        return _check_snapshot(self.root, slug=self.repo, sha=sha, event="push")

    def observe_tag(self, tag: str) -> dict[str, Any] | None:
        if not self._ok("git", "ls-remote", "--tags", "origin", f"refs/tags/{tag}"):
            return None
        try:
            from scripts.release.verify_git_tag import verify_remote_tag
        except ModuleNotFoundError:  # pragma: no cover - direct script execution path
            from verify_git_tag import verify_remote_tag
        ok, _detail, commit = verify_remote_tag(
            repository=self.repo,
            tag=tag,
            token=self._ok("gh", "auth", "token"),
            api_url="https://api.github.com",
            expected_commit=None,
        )
        return {"commit": commit, "verified": ok}

    def observe_release(self, tag: str) -> dict[str, Any] | None:
        done = self._cmd(
            "gh", "release", "view", tag, "--repo", self.repo, "--json", "isDraft,assets"
        )
        if done.returncode != 0:
            if "not found" in (done.stderr + done.stdout).lower():
                return None
            raise PipelineExternalError(done.stderr.strip() or "gh release view failed")
        data = json.loads(done.stdout)
        return {"draft": data["isDraft"], "assets": [a["name"] for a in data["assets"]]}

    def verify_release_assets(self, tag: str) -> dict[str, Any]:
        import hashlib
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            self._ok(
                "gh",
                "release",
                "download",
                tag,
                "--repo",
                self.repo,
                "--pattern",
                "sbom.cyclonedx.json*",
                "--dir",
                tmp,
            )
            sbom = Path(tmp, SBOM_ASSETS[0]).read_bytes()
            recorded = Path(tmp, SBOM_ASSETS[1]).read_text(encoding="utf-8").split()[0]
        actual = hashlib.sha256(sbom).hexdigest()
        return {"ok": actual == recorded, "detail": f"sha256 {actual[:16]} vs {recorded[:16]}"}

    # -- mutations ----------------------------------------------------------
    def create_tag(self, tag: str, commit: str) -> None:
        self._ok("git", "tag", "-s", tag, commit, "-m", f"HyoDo {tag}")
        self._ok("git", "push", "origin", f"refs/tags/{tag}")

    def create_draft_release(self, tag: str, notes: Path) -> None:
        self._ok(
            "gh",
            "release",
            "create",
            tag,
            "--repo",
            self.repo,
            "--verify-tag",
            "--draft",
            "--title",
            f"HyoDo {tag}",
            "--notes-file",
            str(notes),
        )

    def publish_release(self, tag: str) -> None:
        # Only publish.yml runs created at or after this boundary are evidence for it.
        self.publish_started_at = _action_boundary()
        self._ok("gh", "release", "edit", tag, "--repo", self.repo, "--draft=false", "--latest")

    def _job_names(self, workflow: str) -> dict[str, str]:
        return WORKFLOW_JOB_IDS[workflow]

    def _wait_run(
        self,
        workflow: str,
        *,
        event: str,
        since: datetime | None,
        branch: str | None,
        title: str | None = None,
    ) -> dict:
        """Wait for the run this invocation caused, and return its job outcomes.

        A run counts only if it was created at or after ``since`` and matches the
        branch and/or run title given. Picking "the newest run" instead can bind
        evidence to another release or to a run from before the action.
        """
        if not since:
            raise PipelineExternalError(f"{workflow}: refusing to match runs without a start time")
        deadline = time.monotonic() + self.timeout_seconds
        run_id = None
        while run_id is None:
            listing = json.loads(
                self._ok(
                    "gh",
                    "run",
                    "list",
                    "--repo",
                    self.repo,
                    "--workflow",
                    workflow,
                    "--event",
                    event,
                    "--limit",
                    "20",
                    "--json",
                    "databaseId,createdAt,headBranch,displayTitle",
                )
            )
            fresh = [
                r
                for r in listing
                if _created_since(r["createdAt"], since)
                and (branch is None or r["headBranch"] == branch)
                and (title is None or r.get("displayTitle") == title)
            ]
            if len(fresh) > 1:
                raise PipelineExternalError(
                    f"{len(fresh)} {workflow} runs match; refusing to guess which is ours"
                )
            if fresh:
                run_id = str(fresh[0]["databaseId"])
            elif time.monotonic() > deadline:
                raise PipelineExternalError(f"no {workflow} run appeared for this action")
            else:
                time.sleep(self.poll_seconds)
        while True:
            view = json.loads(
                self._ok("gh", "run", "view", run_id, "--repo", self.repo, "--json", "status,jobs")
            )
            if view["status"] == "completed":
                break
            if time.monotonic() > deadline:
                raise PipelineExternalError(f"{workflow} run {run_id} did not finish")
            time.sleep(self.poll_seconds)
        names = self._job_names(workflow)
        jobs = {names.get(j["name"], j["name"]): j["conclusion"] for j in view["jobs"]}
        return {"run_id": run_id, "jobs": jobs}

    def run_release_evidence(self, tag: str) -> dict[str, Any]:
        since = _action_boundary()
        self._ok(
            "gh", "workflow", "run", "release-evidence.yml", "--repo", self.repo, "-f", f"tag={tag}"
        )
        return self._wait_run(
            "release-evidence.yml",
            event="workflow_dispatch",
            since=since,
            branch=None,
            title=EVIDENCE_RUN_TITLE.format(tag=tag),
        )

    def wait_publish_workflow(self, tag: str) -> dict[str, Any]:
        since = getattr(self, "publish_started_at", None)
        return self._wait_run("publish.yml", event="release", since=since, branch=tag)

    def verify_pypi(self, version: str) -> dict[str, Any]:
        done = self._cmd(
            sys.executable,
            "scripts/release/verify-pypi-release.py",
            "--version",
            version,
            "--require-provenance",
            "--install-smoke",
            timeout=1800,
        )
        ok = done.returncode == 0
        return {"provenance": ok, "install": ok, "detail": done.stdout[-300:]}

    def verify_release_chain(self, version: str) -> dict[str, Any]:
        try:
            from scripts.release.verify_release_chain import measure_chain
        except ModuleNotFoundError:  # pragma: no cover - direct script execution path
            from verify_release_chain import measure_chain
        self._ok("git", "fetch", "--quiet", "--tags", "origin")
        steps = measure_chain(version, repo=self.repo, root=self.root)
        missing = [step.name for step in steps if step.state != "OBSERVED"]
        return {
            "ok": not missing,
            "detail": f"{len(steps) - len(missing)}/{len(steps)} OBSERVED"
            + (f"; missing {missing}" if missing else ""),
        }


def run_publication(
    version: str,
    remote: Any,
    *,
    notes: Path,
    execute: bool = False,
    authorize_ref: str | None = None,
    authorize_sha: str | None = None,
) -> dict[str, Any]:
    """Drive one merged version from MERGED to READBACK_VERIFIED, fail-closed.

    Without ``execute`` this is a dry run: remote state is read for real, every
    mutation is recorded in ``planned_mutations`` instead of being called, and
    the run stops at DRAFT_VERIFIED because publication is irreversible.
    """
    tag = f"v{version}"
    dry_run = not execute
    try:
        main_state = remote.observe_main()
        main_sha = main_state.get("sha") or ""
        receipt = start_publication_receipt(version, main_sha, f"origin/main @ {main_sha}")
    except Exception as exc:
        # Nothing has been mutated yet; still answer with a receipt.
        return {
            "schema": "hyodo.release-receipt/v1",
            "phase": "publication",
            "version": version,
            "state": None,
            "stage": "BLOCKED",
            "result": "BLOCK",
            "residuals": [f"{type(exc).__name__}: {exc}"],
            "mutations": [],
            "external_mutation": False,
        }
    receipt["history"][0]["simulated"] = False
    receipt.update(
        {
            "mode": "dry-run" if dry_run else "execute",
            "stage": "MERGED",
            "result": "PASS",
            "planned_mutations": [],
            "mutations": [],
            "external_mutation": False,
        }
    )
    # What a dry run has simulated so far, so later reads see its own effects.
    simulated: dict[str, Any] = {}
    resumed_existing_evidence = False

    def advance(state: str, evidence: str, *, was_simulated: bool) -> None:
        nonlocal receipt
        receipt = transition(receipt, state, evidence)
        receipt["history"][-1]["simulated"] = was_simulated
        receipt["stage"] = state

    def mutate(kind: str, call: Any, *args: Any) -> Any:
        record = {"kind": kind, "tag": tag, "observed_at": _now()}
        if dry_run:
            receipt["planned_mutations"].append(record)
            return None
        receipt["mutations"].append(record)
        receipt["external_mutation"] = True
        return call(*args)

    def observe_tag() -> dict[str, Any] | None:
        return simulated.get("tag") if "tag" in simulated else remote.observe_tag(tag)

    def observe_release() -> dict[str, Any] | None:
        return simulated.get("release") if "release" in simulated else remote.observe_release(tag)

    try:
        if main_state.get("version") != version:
            raise _PublicationBlocked(
                f"origin/main VERSION is {main_state.get('version')!r}, not {version!r}"
            )
        # Main-only checks are N/A on the PR; the merged main SHA is where they
        # must actually succeed before anything is tagged.
        main_ci = remote.observe_main_ci(main_sha)
        receipt["main_ci"] = main_ci
        if main_ci.get("result") != "PASS":
            waiting = main_ci.get("result") == "WAIT"
            raise _PublicationBlocked(
                f"main CI at {main_sha} is {main_ci.get('result')}: "
                f"pending={main_ci.get('pending')} failed={main_ci.get('failed')} "
                f"missing_required={main_ci.get('missing_required')}",
                "WAITING_CI" if waiting else "BLOCKED",
                "WAIT" if waiting else "BLOCK",
            )

        # TAGGED ------------------------------------------------------------
        current_tag = observe_tag()
        if current_tag is None:
            mutate("create_tag", remote.create_tag, tag, main_sha)
            if dry_run:
                simulated["tag"] = {"commit": main_sha, "verified": True}
            current_tag = observe_tag()
        if current_tag is None or current_tag.get("commit") != main_sha:
            found = None if current_tag is None else current_tag.get("commit")
            raise _PublicationBlocked(f"{tag} targets {found}, not merged main {main_sha}")
        if not current_tag.get("verified"):
            raise _PublicationBlocked(f"{tag} is not a GitHub-verified signed tag")
        advance("TAGGED", f"{tag} -> {main_sha} verified", was_simulated="tag" in simulated)

        # DRAFT_CREATED -----------------------------------------------------
        release = observe_release()
        if release is not None and not release.get("draft"):
            raise _PublicationBlocked(
                f"GitHub Release {tag} is already published; immutable releases cannot "
                "take SBOM evidence afterwards (the v4.21.2 failure). Nothing was changed; "
                "release a new version instead."
            )
        if release is None:
            mutate("create_draft_release", remote.create_draft_release, tag, notes)
            if dry_run:
                simulated["release"] = {"draft": True, "assets": []}
            release = observe_release()
        if release is None or not release.get("draft"):
            raise _PublicationBlocked(f"draft Release {tag} was not observed after creation")
        advance("DRAFT_CREATED", f"draft Release {tag}", was_simulated="release" in simulated)

        # EVIDENCE_BUILT / EVIDENCE_ATTACHED (release-evidence.yml) ------------
        require_state(receipt, "DRAFT_CREATED", "release evidence")
        if release.get("assets"):
            # This is the #465 resume path. Drafts are mutable, so bind existing
            # evidence only when it is exactly the expected SBOM pair and the
            # digest verifies now; the publish boundary verifies it again.
            resumed_existing_evidence = True
            if not _has_exact_evidence(release):
                raise _PublicationBlocked(
                    f"draft {tag} already carries assets {release['assets']} from a run "
                    "this invocation did not observe; delete the draft and rerun"
                )
            advance(
                "EVIDENCE_BUILT",
                f"existing draft {tag} SBOM assets observed",
                was_simulated=False,
            )
            advance(
                "EVIDENCE_ATTACHED",
                f"existing draft {tag} SBOM assets observed",
                was_simulated=False,
            )
        else:
            run = mutate("run_release_evidence", remote.run_release_evidence, tag)
            if dry_run:
                run = {
                    "run_id": "SIMULATED",
                    "jobs": dict.fromkeys(WORKFLOW_STATES["release-evidence.yml"], "success"),
                }
                simulated["release"] = {"draft": True, "assets": list(SBOM_ASSETS)}
            for job, state in WORKFLOW_STATES["release-evidence.yml"].items():
                if run["jobs"].get(job) != "success":
                    raise _PublicationBlocked(
                        f"release-evidence.yml job {job} ended {run['jobs'].get(job)!r} "
                        f"(run {run['run_id']})"
                    )
                advance(
                    state,
                    f"release-evidence.yml {job} run {run['run_id']}",
                    was_simulated=dry_run,
                )

        # DRAFT_VERIFIED ------------------------------------------------------
        release = observe_release()
        if release is None or not release.get("draft") or not _has_evidence(release):
            raise _PublicationBlocked(f"{tag} is not a draft carrying both SBOM assets")
        if dry_run and not resumed_existing_evidence:
            verified = {"ok": True, "detail": "SIMULATED digest check"}
        else:
            verified = remote.verify_release_assets(tag)
        if not verified.get("ok"):
            raise _PublicationBlocked(f"SBOM digest did not verify: {verified.get('detail')}")
        advance(
            "DRAFT_VERIFIED",
            f"draft {tag} SBOM digest verified",
            was_simulated=dry_run and not resumed_existing_evidence,
        )

        if dry_run:
            receipt["next_action"] = (
                "rehearsal complete; publication is irreversible and requires "
                "--execute with --authorize-ref and --authorize-sha bound to the merged SHA"
            )
            return receipt

        # PUBLISHED (irreversible) --------------------------------------------
        if not _provided_reference(authorize_ref):
            raise _PublicationBlocked(
                "publishing is irreversible and needs human authority", "WAITING_APPROVAL", "WAIT"
            )
        if authorize_sha != main_sha:
            raise _PublicationBlocked(
                f"authority covers {authorize_sha}, not merged main {main_sha}",
                "RECONCILIATION_REQUIRED",
            )
        require_state(receipt, "DRAFT_VERIFIED", "publish release")
        final_tag = remote.observe_tag(tag)
        if (
            final_tag is None
            or final_tag.get("commit") != main_sha
            or not final_tag.get("verified")
        ):
            raise _PublicationBlocked(
                f"{tag} no longer verifies at {main_sha}; refusing to publish"
            )
        release = remote.observe_release(tag)
        if release is None or not release.get("draft") or not _has_evidence(release):
            raise _PublicationBlocked(f"{tag} changed after verification; refusing to publish")
        # Draft Release assets are mutable until publication. Re-download and
        # verify the digest at the irreversible boundary so same-named assets
        # cannot be replaced after DRAFT_VERIFIED and still get published.
        final_verified = remote.verify_release_assets(tag)
        if not final_verified.get("ok"):
            raise _PublicationBlocked(
                f"SBOM digest changed before publish: {final_verified.get('detail')}"
            )
        mutate("publish_release", remote.publish_release, tag)
        release = remote.observe_release(tag)
        if release is None or release.get("draft"):
            raise _PublicationBlocked(f"{tag} was not observed as published")
        advance(
            "PUBLISHED", f"Release {tag} published with SBOM ({authorize_ref})", was_simulated=False
        )

        # PYPI_PUBLISHED / PROVENANCE_VERIFIED (publish.yml) -------------------
        run = remote.wait_publish_workflow(tag)
        if run["jobs"].get("build") != "success":
            raise _PublicationBlocked(f"publish.yml build ended {run['jobs'].get('build')!r}")
        for job, state in WORKFLOW_STATES["publish.yml"].items():
            if run["jobs"].get(job) != "success":
                raise _PublicationBlocked(
                    f"publish.yml job {job} ended {run['jobs'].get(job)!r} (run {run['run_id']})"
                )
            advance(state, f"publish.yml {job} run {run['run_id']}", was_simulated=False)

        # INSTALL_VERIFIED / READBACK_VERIFIED ---------------------------------
        pypi = remote.verify_pypi(version)
        if not (pypi.get("provenance") and pypi.get("install")):
            raise _PublicationBlocked(f"PyPI readback failed: {pypi.get('detail')}")
        advance(
            "INSTALL_VERIFIED", f"PyPI {version} cold install + provenance", was_simulated=False
        )
        chain = remote.verify_release_chain(version)
        if not chain.get("ok"):
            raise _PublicationBlocked(f"release chain readback incomplete: {chain.get('detail')}")
        advance(
            "READBACK_VERIFIED",
            f"release chain {version}: {chain.get('detail')}",
            was_simulated=False,
        )
        receipt["next_action"] = "closed; seal the measured receipt in docs/releases"
    except (_PublicationBlocked, ReleaseOrderError, PipelineExternalError) as exc:
        blocked = exc if isinstance(exc, _PublicationBlocked) else _PublicationBlocked(str(exc))
        receipt.update(
            {
                "stage": blocked.stage,
                "result": blocked.result,
                "residuals": [blocked.reason],
                "next_action": "resolve the measured block; no later step was attempted",
            }
        )
    except Exception as exc:
        # Anything unexpected (a timeout, malformed gh output) still returns the
        # receipt, so a mutation that already happened, above all an
        # irreversible publish, stays on record.
        receipt.update(
            {
                "stage": "BLOCKED",
                "result": "BLOCK",
                "residuals": [
                    f"{type(exc).__name__}: {exc}; outcome after {receipt['state']} is "
                    "unknown, reconcile remote state before any retry"
                ],
                "next_action": "reconcile remote state; see mutations for what already ran",
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
    parser.add_argument(
        "--publication",
        action="store_true",
        help=(
            "Drive a merged version through tag, draft, evidence, publication and "
            "readback. Dry run unless --execute; publishing also needs --authorize-ref "
            "and --authorize-sha bound to the merged main SHA"
        ),
    )
    parser.add_argument("--notes", help="Release notes file (default docs/releases/<v>.md)")
    args = parser.parse_args(argv)
    if args.publication:
        root = Path(args.root)
        notes = (
            Path(args.notes) if args.notes else root / "docs" / "releases" / f"{args.version}.md"
        )
        receipt = run_publication(
            args.version,
            GitHubRemote(root),
            notes=notes,
            execute=args.execute,
            authorize_ref=args.authorize_ref,
            authorize_sha=args.authorize_sha,
        )
        print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if receipt["result"] == "PASS" else 1
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
