"""Read-only, exact-artifact independent verifier attestation.

The verifier produces evidence about a candidate. It cannot push, merge,
authorize, or turn a missing observation into a pass.
"""

from __future__ import annotations

import subprocess
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hyodo.nameplate import UNOBSERVED, validate_nameplate_for_artifact

INDEPENDENT_VERIFIER_SCHEMA_VERSION = "hyodo.independent-verifier/v1"
VERDICTS = frozenset({"PASS", "BLOCK", "UNOBSERVED"})


def _git(root: Path, *args: str) -> str | None:
    """Run a read-only git query and return stdout, or None when unobserved."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def _contains_forbidden_input(value: Any) -> bool:
    if isinstance(value, Mapping):
        forbidden = {"builder_verdict", "authority", "approval", "merge"}
        return any(
            key in forbidden or _contains_forbidden_input(item) for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_forbidden_input(item) for item in value)
    return False


def observe_candidate(root: Path) -> dict[str, Any]:
    """Read the candidate checkout without changing it."""
    head = _git(root, "rev-parse", "HEAD")
    status = _git(root, "status", "--porcelain")
    return {
        "head_sha": head or UNOBSERVED,
        "worktree": "CLEAN" if status == "" else "DIRTY" if status is not None else UNOBSERVED,
    }


def verify_exact_candidate(
    *,
    root: Path,
    expected_artifact_sha: str,
    verifier_nameplate: Mapping[str, Any],
    evidence: Mapping[str, Any],
    observed_at: str | None = None,
) -> dict[str, Any]:
    """Return a blind, read-only attestation for one exact candidate SHA.

    ``evidence`` is supplied by the harness and must not contain a builder
    verdict or authority claim. The verifier never accepts either as input.
    """
    observed = observe_candidate(root)
    reasons: list[str] = []
    head = observed["head_sha"]
    if head == UNOBSERVED:
        reasons.append("candidate_head_unobserved")
    elif head != expected_artifact_sha:
        reasons.append("exact_artifact_sha_mismatch")
    if observed["worktree"] == "DIRTY":
        reasons.append("candidate_worktree_dirty")
    elif observed["worktree"] == UNOBSERVED:
        reasons.append("candidate_worktree_unobserved")

    nameplate_ok, nameplate_reasons, normalized = validate_nameplate_for_artifact(
        verifier_nameplate, expected_artifact_sha
    )
    if not nameplate_ok or normalized is None:
        reasons.extend(nameplate_reasons)
    if normalized is not None and normalized["role"] != "verifier":
        reasons.append("verifier_role_required")
    if normalized is not None and normalized["actor_id"] == UNOBSERVED:
        reasons.append("verifier_actor_unobserved")
    if normalized is not None and normalized["session_id"] == UNOBSERVED:
        reasons.append("verifier_session_unobserved")

    if not isinstance(evidence, Mapping) or not evidence:
        reasons.append("verification_evidence_unobserved")
    elif _contains_forbidden_input(evidence):
        reasons.append("authority_or_builder_input_forbidden")

    unobserved_reasons = {
        "candidate_head_unobserved",
        "candidate_worktree_unobserved",
        "verifier_actor_unobserved",
        "verifier_session_unobserved",
        "verification_evidence_unobserved",
    }
    if any(reason in unobserved_reasons for reason in reasons):
        verdict = "UNOBSERVED"
    elif reasons:
        verdict = "BLOCK"
    else:
        verdict = "PASS"
    return {
        "schema_version": INDEPENDENT_VERIFIER_SCHEMA_VERSION,
        "verdict": verdict,
        "isolation_scope": "CONTRACT_LEVEL",
        "target": {"exact_artifact_sha": expected_artifact_sha},
        "observed": observed,
        "verifier_nameplate": dict(normalized or verifier_nameplate),
        "evidence": dict(evidence) if isinstance(evidence, Mapping) else {},
        "residuals": [*reasons, "process_credential_isolation_unproven"],
        "observed_at": observed_at or datetime.now(timezone.utc).isoformat(),
    }


__all__ = [
    "INDEPENDENT_VERIFIER_SCHEMA_VERSION",
    "VERDICTS",
    "observe_candidate",
    "verify_exact_candidate",
]
