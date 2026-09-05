#!/usr/bin/env python3
"""Require a GitHub-verified annotated release tag.

The release workflow calls GitHub's Git Database API and rejects lightweight,
unsigned, invalid, or unexpectedly-targeted tags before package publication.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen


def evaluate_tag_trust(
    ref_payload: dict[str, Any],
    tag_payload: dict[str, Any],
    *,
    expected_tag: str,
    expected_commit: str | None = None,
) -> tuple[bool, str, str | None]:
    """Evaluate one Git ref + annotated-tag payload without network access."""
    ref_object = ref_payload.get("object") or {}
    if ref_object.get("type") != "tag":
        return False, "release tag is lightweight; an annotated verified tag is required", None

    tag_name = tag_payload.get("tag")
    if tag_name != expected_tag:
        return False, f"tag object name mismatch: expected {expected_tag!r}, got {tag_name!r}", None

    target = tag_payload.get("object") or {}
    if target.get("type") != "commit":
        return False, f"annotated tag must point directly to a commit, got {target.get('type')!r}", None

    target_sha = target.get("sha")
    if not isinstance(target_sha, str) or not target_sha:
        return False, "annotated tag is missing its target commit SHA", None

    verification = tag_payload.get("verification") or {}
    if verification.get("verified") is not True:
        reason = verification.get("reason") or "unknown"
        return False, f"annotated tag is not GitHub-verified (reason={reason})", target_sha

    if expected_commit is not None and target_sha != expected_commit:
        return (
            False,
            f"verified tag targets {target_sha}, but checked-out release commit is {expected_commit}",
            target_sha,
        )

    return True, "verified annotated tag", target_sha


def _get_json(url: str, token: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hyodo-release-tag-verifier",
        },
    )
    with urlopen(request, timeout=20) as response:  # noqa: S310 - fixed GitHub API origin
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError(f"GitHub API returned {type(payload).__name__}, expected object")
    return payload


def verify_remote_tag(
    *,
    repository: str,
    tag: str,
    token: str,
    api_url: str,
    expected_commit: str | None,
) -> tuple[bool, str, str | None]:
    """Fetch and verify a release tag through the authenticated GitHub API."""
    encoded_tag = quote(tag, safe="")
    root = api_url.rstrip("/")
    ref_payload = _get_json(f"{root}/repos/{repository}/git/ref/tags/{encoded_tag}", token)

    ref_object = ref_payload.get("object") or {}
    if ref_object.get("type") != "tag":
        return evaluate_tag_trust(
            ref_payload,
            {},
            expected_tag=tag,
            expected_commit=expected_commit,
        )

    tag_sha = ref_object.get("sha")
    if not isinstance(tag_sha, str) or not tag_sha:
        return False, "annotated tag reference is missing its tag-object SHA", None

    # Reconstruct the API path instead of following a URL supplied by payload.
    tag_payload = _get_json(f"{root}/repos/{repository}/git/tags/{tag_sha}", token)
    return evaluate_tag_trust(
        ref_payload,
        tag_payload,
        expected_tag=tag,
        expected_commit=expected_commit,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="GitHub owner/repo")
    parser.add_argument("--tag", required=True, help="Release tag, e.g. v4.12.0")
    parser.add_argument("--expected-commit", help="Commit SHA checked out for publication")
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN is required for tag verification", file=sys.stderr)
        return 1

    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    try:
        ok, message, target = verify_remote_tag(
            repository=args.repository,
            tag=args.tag,
            token=token,
            api_url=api_url,
            expected_commit=args.expected_commit,
        )
    except Exception as exc:
        print(f"ERROR: could not verify release tag: {exc}", file=sys.stderr)
        return 1

    if not ok:
        print(f"ERROR: {message}", file=sys.stderr)
        return 1

    print(f"OK: {args.tag} is a {message} targeting {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
